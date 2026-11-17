"""
Quase-experimentos para dados de busca: "a mudança X causou a subida ou a queda?".

Todos os estimadores trabalham em log(1 + y) e devolvem o efeito relativo
(0.10 = +10%) com intervalo de 95%. O efeito é a razão média (geométrica) entre o que
aconteceu e o contrafactual, o que o torna pouco sensível a dias de pico.
Funções puras sobre DataFrames.

- interrupted_time_series: a série contra a própria tendência anterior.
- control_counterfactual: a série contra um contrafactual previsto por páginas de controle
  (a lógica do CausalImpact, com regressão simples no lugar do modelo bayesiano).
- diff_in_diff: páginas alteradas contra páginas parecidas que não mudaram.
- ab_test / ab_split: o mesmo, com sorteio, e inferência por permutação.
"""

from typing import Any, Dict, List

import numpy as np
import pandas as pd
from scipy import stats

MIN_PRE, MIN_POST = 14, 7
BLOCK = 7  # reamostragem em blocos de uma semana: preserva parte da autocorrelação
LOW_COUNT = 10  # abaixo disso, o "+1" do log(1 + y) puxa o efeito para zero

PRESSUPOSTOS = {
    "its": [
        "A tendência do período anterior continuaria igual sem a mudança.",
        "Nada mais aconteceu na mesma data (update do algoritmo, campanha, sazonalidade nova).",
        "Não há grupo de controle: qualquer choque posterior no site inteiro entra no efeito. Use `end_date` para cortar a janela antes de um evento conhecido.",
        "O intervalo é otimista: em simulação, o de 95% cobriu o valor verdadeiro em 90% das vezes com dias independentes e em 82% com dias correlacionados (AR(1), 0,6).",
    ],
    "control_counterfactual": [
        "As páginas de controle não foram afetadas pela mudança (nem por links internos vindos das tratadas).",
        "A relação entre tratadas e controles no período anterior continuaria igual (veja pre_fit_r2).",
        "Choques que atingem todos por igual são absorvidos; choques só nas tratadas, não.",
        "Se a série de controle for ruidosa, a regressão a acompanha menos do que deveria e um choque comum é absorvido só em parte.",
        "O intervalo é um pouco otimista: em simulação, o de 95% cobriu o valor verdadeiro em 92% das vezes com dias independentes e em 88% com dias correlacionados (AR(1), 0,6).",
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
    "Atenção: neste projeto o painel é sintético e o efeito verdadeiro é conhecido (`true_effect`, definido para cliques); serve para conferir se o método recupera o efeito, não como evidência sobre SEO real.",
]


def _block_bootstrap(residuals: np.ndarray, rng: np.random.Generator, size: int = None) -> np.ndarray:
    n = len(residuals)
    size = size or n
    starts = rng.integers(0, max(1, n - BLOCK + 1), size=int(np.ceil(size / BLOCK)))
    return np.concatenate([residuals[s:s + BLOCK] for s in starts])[:size]


def _summary(log_effect: float, log_draws: np.ndarray) -> Dict[str, Any]:
    if not np.isfinite(log_effect) or not np.isfinite(log_draws).all() or np.ptp(log_draws) == 0:
        raise ValueError("Série sem variação suficiente para estimar um efeito.")
    lo, hi = np.percentile(log_draws, [2.5, 97.5])
    p = 2 * min((log_draws <= 0).mean(), (log_draws >= 0).mean())
    return {"relative_effect": round(float(np.expm1(log_effect)), 4),
            "ci95": [round(float(np.expm1(lo)), 4), round(float(np.expm1(hi)), 4)],
            "p_value": round(float(min(1.0, p)), 4)}


def _low_count_warning(values: pd.Series) -> List[str]:
    typical = float(values.median()) if len(values) else 0.0
    if typical >= LOW_COUNT:
        return []
    return [f"contagens pequenas (mediana de {typical:.1f} por unidade e dia): o log(1 + y) puxa o efeito "
            "para zero; some mais páginas por unidade ou use períodos semanais."]


def _prepare(series: pd.DataFrame, intervention_date, end_date=None) -> pd.DataFrame:
    df = series.dropna(subset=["date", "y"]).copy()
    df["date"] = pd.to_datetime(df["date"])
    numeric = [c for c in df.columns if c != "date"]
    df = df.groupby("date", as_index=False)[numeric].sum().sort_values("date")   # uma linha por dia
    if end_date is not None:
        df = df[df["date"] <= pd.Timestamp(end_date)]
    df["post"] = df["date"] >= pd.Timestamp(intervention_date)
    n_pre, n_post = int((~df["post"]).sum()), int(df["post"].sum())
    if n_pre < MIN_PRE or n_post < MIN_POST:
        raise ValueError(f"Série curta demais: {n_pre} dias antes (mínimo {MIN_PRE}) e {n_post} depois (mínimo {MIN_POST}).")
    return df.reset_index(drop=True)


def _series_out(df: pd.DataFrame, counterfactual_log: np.ndarray):
    return [{"date": d.date().isoformat(), "actual": float(a), "counterfactual": round(float(c), 2)}
            for d, a, c in zip(df["date"], df["y"], np.expm1(counterfactual_log))]


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
        cf = base @ beta[: base.shape[1]]
        fitted = X @ beta
        # no pós, a média dos resíduos é zero: ajustado - contrafactual = real - contrafactual (em log)
        return beta, cf, fitted, float((fitted[post] - cf[post]).mean())

    beta, cf, fitted, effect = fit(y)
    rng = np.random.default_rng(seed)
    # resíduos de mínimos quadrados são menores que o erro verdadeiro: corrige pelos graus de liberdade
    resid = (y - fitted) * np.sqrt(n / max(1, n - X.shape[1]))
    draws = np.array([fit(fitted + _block_bootstrap(resid, rng))[3] for _ in range(n_boot)])
    return {
        **_summary(effect, draws),
        "level_change": round(float(np.expm1(beta[-2])), 4),
        "slope_change_per_day": round(float(beta[-1]), 5),
        "n_pre": int((~post).sum()), "n_post": int(post.sum()),
        "avisos": _low_count_warning(df["y"]),
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
    n_post = int(post.sum())
    y = np.log1p(df["y"].to_numpy(dtype=float))
    # tendência própria: a regressão acompanha o controle menos do que deveria quando ele é ruidoso,
    # e a sobra de tendência viraria "efeito" no período posterior
    X = np.column_stack([np.ones(len(df)), np.log1p(df["y_control"].to_numpy(dtype=float)), np.arange(len(df), dtype=float)])

    def fit(target_pre):
        beta = np.linalg.lstsq(X[~post], target_pre, rcond=None)[0]
        return beta, X @ beta

    beta, cf = fit(y[~post])
    effect = float((y[post] - cf[post]).mean())
    fitted_pre = X[~post] @ beta
    n_pre = len(fitted_pre)
    resid = (y[~post] - fitted_pre) * np.sqrt(n_pre / max(1, n_pre - X.shape[1]))
    ss_tot = ((y[~post] - y[~post].mean()) ** 2).sum()
    rng = np.random.default_rng(seed)
    draws = []
    for _ in range(n_boot):
        _, cf_b = fit(fitted_pre + _block_bootstrap(resid, rng))
        # incerteza do ajuste + ruído médio do pós, reamostrado em blocos como o do pré
        draws.append(float((y[post] - cf_b[post]).mean() - _block_bootstrap(resid, rng, n_post).mean()))
    return {
        **_summary(effect, np.array(draws)),
        "pre_fit_r2": round(float(1 - ((y[~post] - fitted_pre) ** 2).sum() / ss_tot), 4) if ss_tot else None,
        "n_pre": n_pre, "n_post": n_post,
        "avisos": _low_count_warning(df[["y", "y_control"]].min(axis=1)),
        "series": _series_out(df, cf),
    }


def _clean_panel(panel: pd.DataFrame, end_date=None) -> pd.DataFrame:
    df = panel.dropna(subset=["unit", "date", "y", "treated"]).copy()
    df["date"] = pd.to_datetime(df["date"])
    df["treated"] = df["treated"].astype(bool)
    if end_date is not None:
        df = df[df["date"] <= pd.Timestamp(end_date)]
    return df


def _unit_changes(df: pd.DataFrame, intervention_date) -> pd.DataFrame:
    """Por unidade: média de log(1+y) antes e depois da data, e a variação. `df` já limpo."""
    df = df.assign(post=df["date"] >= pd.Timestamp(intervention_date), ly=np.log1p(df["y"].astype(float)))
    means = df.pivot_table(index=["unit", "treated"], columns="post", values="ly", aggfunc="mean")
    if True not in means.columns or False not in means.columns:
        raise ValueError("É preciso ter dias antes e depois da data da intervenção.")
    means = means.dropna().reset_index()
    means["delta"] = means[True] - means[False]
    if means["treated"].sum() < 2 or (~means["treated"]).sum() < 2:
        raise ValueError("É preciso ter pelo menos 2 unidades tratadas e 2 de controle com dados antes e depois.")
    return means.rename(columns={False: "pre", True: "post"})


def _did_estimate(changes: pd.DataFrame) -> Dict[str, Any]:
    t, c = changes.loc[changes["treated"], "delta"], changes.loc[~changes["treated"], "delta"]
    did = t.mean() - c.mean()
    vt, vc = t.var(ddof=1) / len(t), c.var(ddof=1) / len(c)
    se = float(np.sqrt(vt + vc))
    if not se:
        raise ValueError("Unidades sem variação: não há como estimar a incerteza.")
    dof = (vt + vc) ** 2 / (vt ** 2 / (len(t) - 1) + vc ** 2 / (len(c) - 1))   # Welch
    half = stats.t.ppf(0.975, dof) * se
    return {
        "relative_effect": round(float(np.expm1(did)), 4),
        "ci95": [round(float(np.expm1(did - half)), 4), round(float(np.expm1(did + half)), 4)],
        "p_value": round(float(2 * stats.t.sf(abs(did) / se, dof)), 4),
    }


def diff_in_diff(panel: pd.DataFrame, intervention_date, end_date=None) -> Dict[str, Any]:
    """
    Diferença-em-diferenças com a página como unidade (erro agrupado por página).

    `panel`: colunas unit, date, y, treated. Devolve também o antes/depois ingênuo das
    tratadas, um placebo no período anterior e o estudo de evento semanal.
    """
    t0 = pd.Timestamp(intervention_date)
    df = _clean_panel(panel, end_date)
    n_pre, n_post = df.loc[df["date"] < t0, "date"].nunique(), df.loc[df["date"] >= t0, "date"].nunique()
    if n_pre < MIN_PRE or n_post < MIN_POST:
        raise ValueError(f"Painel curto demais: {n_pre} dias antes (mínimo {MIN_PRE}) e {n_post} depois (mínimo {MIN_POST}).")
    changes = _unit_changes(df, t0)
    treated, control = changes[changes["treated"]], changes[~changes["treated"]]

    pre_dates = np.sort(df.loc[df["date"] < t0, "date"].unique())
    placebo = None
    if len(pre_dates) >= 2 * MIN_POST:
        fake = pd.Timestamp(pre_dates[len(pre_dates) // 2])
        placebo = {"date": fake.date().isoformat(), **_did_estimate(_unit_changes(df[df["date"] < t0], fake))}

    week = np.floor((df["date"] - t0).dt.days / 7).astype(int)
    df = df.assign(week=np.where(week >= 0, week + 1, week),   # ..., -2, -1, 1, 2, ... (sem semana 0)
                   ly=np.log1p(df["y"].astype(float)))
    gap = df.pivot_table(index="week", columns="treated", values="ly", aggfunc="mean")
    gap = (gap[True] - gap[False]).dropna()
    gap = gap - gap[gap.index < 0].mean()

    return {
        **_did_estimate(changes),
        "naive_before_after": round(float(np.expm1(treated["delta"].mean())), 4),
        "control_change": round(float(np.expm1(control["delta"].mean())), 4),
        "n_treated": len(treated), "n_control": len(control),
        "units_dropped": int(df["unit"].nunique() - len(changes)),   # sem dados antes ou depois
        "balance": {
            "treated_pre_mean": round(float(np.expm1(treated["pre"].mean())), 2),
            "control_pre_mean": round(float(np.expm1(control["pre"].mean())), 2),
        },
        "placebo_pre": placebo,
        "event_study": [{"week": int(w), "gap": round(float(g), 4)} for w, g in gap.items()],
        "avisos": _low_count_warning(df.groupby("unit")["y"].mean()),
    }


def ab_test(panel: pd.DataFrame, intervention_date, end_date=None, n_perm: int = 2000, seed: int = 0) -> Dict[str, Any]:
    """Teste A/B por grupos de páginas: o estimador do DiD com inferência por permutação do sorteio."""
    result = diff_in_diff(panel, intervention_date, end_date)
    changes = _unit_changes(_clean_panel(panel, end_date), intervention_date)
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
