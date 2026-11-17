"""
Quase-experimentos para dados de busca: "a mudança X causou a subida ou a queda?".

Todos os estimadores trabalham em log(1 + y) e devolvem o efeito relativo
(0.10 = +10%) com intervalo de 95%. Funções puras sobre DataFrames.

- interrupted_time_series: a série contra a própria tendência anterior.
- control_counterfactual: a série contra um contrafactual previsto por páginas de controle
  (a lógica do CausalImpact, com regressão simples no lugar do modelo bayesiano).
- diff_in_diff: páginas alteradas contra páginas parecidas que não mudaram.
- ab_test / ab_split: o mesmo, com sorteio, e inferência por permutação.
"""

from typing import Any, Dict

import numpy as np
import pandas as pd
from scipy import stats

MIN_PRE, MIN_POST = 14, 7
BLOCK = 7  # reamostragem em blocos de uma semana: preserva a autocorrelação e a sazonalidade

PRESSUPOSTOS = {
    "its": [
        "A tendência do período anterior continuaria igual sem a mudança.",
        "Nada mais aconteceu na mesma data (update do algoritmo, campanha, sazonalidade nova).",
        "Não há grupo de controle: qualquer choque posterior no site inteiro entra no efeito. Use `end_date` para cortar a janela antes de um evento conhecido.",
    ],
    "control_counterfactual": [
        "As páginas de controle não foram afetadas pela mudança (nem por links internos vindos das tratadas).",
        "A relação entre tratadas e controles no período anterior continuaria igual (veja pre_fit_r2).",
        "Choques que atingem todos por igual são absorvidos; choques só nas tratadas, não.",
    ],
    "did": [
        "Tendências paralelas: sem a mudança, tratadas e controles variariam na mesma proporção (veja placebo_pre e event_study).",
        "Quem escolheu as páginas tratadas não as escolheu por algo que também muda a tendência delas.",
        "Sem contaminação: a mudança nas tratadas não tira nem dá tráfego às de controle (canibalização, links internos).",
    ],
    "ab": [
        "O sorteio garante grupos comparáveis em média; com poucas páginas, confira `balance`.",
        "Sem contaminação entre grupos: páginas do mesmo template disputam as mesmas consultas.",
        "O p-valor por permutação pergunta: se o rótulo fosse sorteado de novo, com que frequência sairia uma diferença deste tamanho?",
    ],
}

LEITURA_DO_MEIO = [
    "Clique e posição do Search Console são médias diárias produzidas pelo buscador: uma mudança de layout na página de resultados altera o CTR sem que a página tenha mudado.",
    "O buscador reage à mudança com atraso (rastreamento e reindexação): os primeiros dias do 'depois' misturam versões antiga e nova.",
    "Updates do algoritmo são intervenções da plataforma sobre todos ao mesmo tempo: o método só responde à pergunta causal se tiver com o que comparar.",
    "Atenção: neste projeto o painel é sintético e o efeito verdadeiro é conhecido (`true_effect`); serve para conferir se o método recupera o efeito, não como evidência sobre SEO real.",
]


def _block_bootstrap(residuals: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    n = len(residuals)
    starts = rng.integers(0, max(1, n - BLOCK + 1), size=int(np.ceil(n / BLOCK)))
    return np.concatenate([residuals[s:s + BLOCK] for s in starts])[:n]


def _summary(estimate: float, draws: np.ndarray) -> Dict[str, Any]:
    lo, hi = np.percentile(draws, [2.5, 97.5])
    p = 2 * min((draws <= 0).mean(), (draws >= 0).mean())
    return {"relative_effect": round(float(estimate), 4), "ci95": [round(float(lo), 4), round(float(hi), 4)],
            "p_value": round(float(min(1.0, p)), 4)}


def _prepare(series: pd.DataFrame, intervention_date, end_date=None) -> pd.DataFrame:
    df = series.dropna(subset=["date", "y"]).copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    if end_date is not None:
        df = df[df["date"] <= pd.Timestamp(end_date)]
    df["post"] = df["date"] >= pd.Timestamp(intervention_date)
    n_pre, n_post = int((~df["post"]).sum()), int(df["post"].sum())
    if n_pre < MIN_PRE or n_post < MIN_POST:
        raise ValueError(f"Série curta demais: {n_pre} dias antes (mínimo {MIN_PRE}) e {n_post} depois (mínimo {MIN_POST}).")
    return df.reset_index(drop=True)


def _series_out(df: pd.DataFrame, counterfactual: np.ndarray):
    return [{"date": d.date().isoformat(), "actual": float(a), "counterfactual": round(float(c), 2)}
            for d, a, c in zip(df["date"], df["y"], counterfactual)]


def interrupted_time_series(series: pd.DataFrame, intervention_date, end_date=None,
                            n_boot: int = 500, seed: int = 0) -> Dict[str, Any]:
    """
    Regressão segmentada: nível + tendência + dia da semana, com mudança de nível e de
    inclinação na data. Contrafactual = a mesma regressão sem os termos de mudança.

    `series`: colunas date, y (uma linha por dia).
    """
    df = _prepare(series, intervention_date, end_date)
    n, post = len(df), df["post"].to_numpy()
    t = np.arange(n, dtype=float)
    since = np.where(post, t - t[post][0], 0.0)
    dow = pd.get_dummies(df["date"].dt.day_of_week, drop_first=True).to_numpy(dtype=float)
    base = np.column_stack([np.ones(n), t, dow])
    X = np.column_stack([base, post.astype(float), since])
    y = np.log1p(df["y"].to_numpy(dtype=float))

    def fit(target):
        beta = np.linalg.lstsq(X, target, rcond=None)[0]
        cf = np.expm1(base @ beta[: base.shape[1]])
        fitted = X @ beta
        # efeito = o que o modelo ajustou no pós contra o que ele projeta sem a mudança
        return beta, cf, fitted, np.expm1(fitted[post]).sum() / cf[post].sum() - 1

    beta, cf, fitted, effect = fit(y)
    rng = np.random.default_rng(seed)
    resid = y - fitted
    draws = np.array([fit(fitted + _block_bootstrap(resid, rng))[3] for _ in range(n_boot)])
    return {
        **_summary(effect, draws),
        "level_change": round(float(np.expm1(beta[-2])), 4),
        "slope_change_per_day": round(float(beta[-1]), 5),
        "n_pre": int((~post).sum()), "n_post": int(post.sum()),
        "series": _series_out(df, cf),
    }


def control_counterfactual(treated: pd.DataFrame, control: pd.DataFrame, intervention_date, end_date=None,
                           n_boot: int = 500, seed: int = 0) -> Dict[str, Any]:
    """
    Aprende, no período anterior, como a série tratada acompanha a de controle; projeta
    essa relação no período posterior e compara com o que aconteceu.

    `treated`, `control`: colunas date, y (uma linha por dia, somando as páginas do grupo).
    """
    merged = treated.merge(control, on="date", suffixes=("", "_control"))
    df = _prepare(merged, intervention_date, end_date)
    post = df["post"].to_numpy()
    y = np.log1p(df["y"].to_numpy(dtype=float))
    X = np.column_stack([np.ones(len(df)), np.log1p(df["y_control"].to_numpy(dtype=float))])

    def fit(target_pre):
        beta = np.linalg.lstsq(X[~post], target_pre, rcond=None)[0]
        return beta, np.expm1(X @ beta)

    beta, cf = fit(y[~post])
    actual_post = df["y"].to_numpy(dtype=float)[post].sum()
    effect = actual_post / cf[post].sum() - 1
    fitted_pre = X[~post] @ beta
    resid = y[~post] - fitted_pre
    ss_tot = ((y[~post] - y[~post].mean()) ** 2).sum()
    rng = np.random.default_rng(seed)
    draws = []
    for _ in range(n_boot):
        _, cf_b = fit(fitted_pre + _block_bootstrap(resid, rng))
        # incerteza do ajuste + ruído diário do pós
        noise = np.exp(rng.choice(resid, size=int(post.sum())))
        draws.append(actual_post / (cf_b[post] * noise).sum() - 1)
    return {
        **_summary(effect, np.array(draws)),
        "pre_fit_r2": round(float(1 - (resid ** 2).sum() / ss_tot), 4) if ss_tot else None,
        "n_pre": int((~post).sum()), "n_post": int(post.sum()),
        "series": _series_out(df, cf),
    }


def _unit_changes(panel: pd.DataFrame, intervention_date, start_date=None, end_date=None) -> pd.DataFrame:
    """Por unidade: média de log(1+y) antes e depois da data, e a variação."""
    df = panel.dropna(subset=["unit", "date", "y"]).copy()
    df["date"] = pd.to_datetime(df["date"])
    if start_date is not None:
        df = df[df["date"] >= pd.Timestamp(start_date)]
    if end_date is not None:
        df = df[df["date"] <= pd.Timestamp(end_date)]
    df["post"] = df["date"] >= pd.Timestamp(intervention_date)
    df["ly"] = np.log1p(df["y"].astype(float))
    means = df.pivot_table(index=["unit", "treated"], columns="post", values="ly", aggfunc="mean")
    if True not in means.columns or False not in means.columns:
        raise ValueError("É preciso ter dias antes e depois da data da intervenção.")
    means = means.dropna().reset_index()
    means["delta"] = means[True] - means[False]
    means["treated"] = means["treated"].astype(bool)
    if means["treated"].sum() < 2 or (~means["treated"]).sum() < 2:
        raise ValueError("É preciso ter pelo menos 2 unidades tratadas e 2 de controle.")
    return means.rename(columns={False: "pre", True: "post"})


def _did_estimate(changes: pd.DataFrame) -> Dict[str, Any]:
    t, c = changes.loc[changes["treated"], "delta"], changes.loc[~changes["treated"], "delta"]
    did = t.mean() - c.mean()
    vt, vc = t.var(ddof=1) / len(t), c.var(ddof=1) / len(c)
    se = float(np.sqrt(vt + vc))
    dof = (vt + vc) ** 2 / (vt ** 2 / (len(t) - 1) + vc ** 2 / (len(c) - 1)) if se else 1.0   # Welch
    half = stats.t.ppf(0.975, dof) * se
    p = 2 * stats.t.sf(abs(did) / se, dof) if se else 1.0
    return {
        "relative_effect": round(float(np.expm1(did)), 4),
        "ci95": [round(float(np.expm1(did - half)), 4), round(float(np.expm1(did + half)), 4)],
        "p_value": round(float(p), 4),
    }


def diff_in_diff(panel: pd.DataFrame, intervention_date, end_date=None) -> Dict[str, Any]:
    """
    Diferença-em-diferenças com a página como unidade (erro agrupado por página).

    `panel`: colunas unit, date, y, treated. Devolve também o antes/depois ingênuo das
    tratadas, um placebo no período anterior e o estudo de evento semanal.
    """
    t0 = pd.Timestamp(intervention_date)
    changes = _unit_changes(panel, t0, end_date=end_date)
    treated, control = changes[changes["treated"]], changes[~changes["treated"]]

    df = panel.copy()
    df["date"] = pd.to_datetime(df["date"])
    if end_date is not None:
        df = df[df["date"] <= pd.Timestamp(end_date)]
    pre_dates = np.sort(df.loc[df["date"] < t0, "date"].unique())
    placebo = None
    if len(pre_dates) >= 2 * MIN_POST:
        fake = pd.Timestamp(pre_dates[len(pre_dates) // 2])
        placebo = {"date": fake.date().isoformat(), **_did_estimate(_unit_changes(df[df["date"] < t0], fake))}

    df["week"] = np.floor((df["date"] - t0).dt.days / 7).astype(int)
    df["week"] = np.where(df["week"] >= 0, df["week"] + 1, df["week"])   # ..., -2, -1, 1, 2, ... (sem semana 0)
    df["ly"] = np.log1p(df["y"].astype(float))
    gap = df.pivot_table(index="week", columns="treated", values="ly", aggfunc="mean")
    gap = (gap[True] - gap[False]).dropna()
    gap = gap - gap[gap.index < 0].mean()

    return {
        **_did_estimate(changes),
        "naive_before_after": round(float(np.expm1(treated["delta"].mean())), 4),
        "control_change": round(float(np.expm1(control["delta"].mean())), 4),
        "n_treated": len(treated), "n_control": len(control),
        "balance": {
            "treated_pre_mean": round(float(np.expm1(treated["pre"].mean())), 2),
            "control_pre_mean": round(float(np.expm1(control["pre"].mean())), 2),
        },
        "placebo_pre": placebo,
        "event_study": [{"week": int(w), "gap": round(float(g), 4)} for w, g in gap.items()],
    }


def ab_test(panel: pd.DataFrame, intervention_date, end_date=None, n_perm: int = 2000, seed: int = 0) -> Dict[str, Any]:
    """Teste A/B por grupos de páginas: o estimador do DiD com inferência por permutação do sorteio."""
    result = diff_in_diff(panel, intervention_date, end_date)
    changes = _unit_changes(panel, intervention_date, end_date=end_date)
    delta, treated = changes["delta"].to_numpy(), changes["treated"].to_numpy()
    observed = delta[treated].mean() - delta[~treated].mean()
    rng = np.random.default_rng(seed)
    perms = np.empty(n_perm)
    for i in range(n_perm):
        shuffled = rng.permutation(treated)
        perms[i] = delta[shuffled].mean() - delta[~shuffled].mean()
    # +1: o próprio sorteio observado conta como uma permutação possível
    p = (1 + (np.abs(perms) >= abs(observed)).sum()) / (n_perm + 1)
    return {**result, "permutation_p_value": round(float(p), 4), "n_permutations": n_perm}


def ab_split(pages: pd.DataFrame, seed: int = 0) -> Dict[str, Any]:
    """
    Sorteio estratificado para um teste A/B de SEO: ordena as páginas pelo tráfego
    anterior e sorteia dentro de cada par vizinho, para os grupos nascerem parecidos.

    `pages`: colunas unit, pre_metric.
    """
    df = pages.dropna(subset=["unit"]).fillna({"pre_metric": 0}).sort_values(["pre_metric", "unit"], ascending=[False, True])
    rng = np.random.default_rng(seed)
    units = df["unit"].tolist()
    assignment: Dict[str, str] = {}
    for i in range(0, len(units), 2):
        pair = units[i:i + 2]
        first = "tratado" if rng.random() < 0.5 else "controle"
        assignment[pair[0]] = first
        if len(pair) == 2:
            assignment[pair[1]] = "controle" if first == "tratado" else "tratado"
    df["grp"] = df["unit"].map(assignment)
    means = df.groupby("grp")["pre_metric"].mean()
    t, c = float(means.get("tratado", 0.0)), float(means.get("controle", 0.0))
    return {
        "assignment": assignment,
        "balance": {"treated_pre_mean": round(t, 2), "control_pre_mean": round(c, 2),
                    "relative_gap": round(t / c - 1, 4) if c else None},
        "seed": seed,
    }
