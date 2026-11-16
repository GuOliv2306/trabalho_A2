"""
Análises de métodos digitais (funções puras sobre DataFrames).

Princípio (Rogers, "follow the medium"): os objetos aqui são os do próprio meio
(revisões, tags de reversão, links, posição no ranking). Cada resultado diz algo
sobre o tema E sobre a plataforma que produziu o dado; por isso as rotas devolvem
junto uma `leitura_do_meio`.
"""

import re
from itertools import combinations
from typing import Any, Dict, List

import pandas as pd

REVERTING_TAGS = {"mw-undo", "mw-rollback", "mw-manual-revert"}
REVERTED_TAG = "mw-reverted"

STOPWORDS = {
    "a", "o", "as", "os", "de", "da", "do", "das", "dos", "e", "em", "no", "na", "nos", "nas",
    "um", "uma", "para", "por", "com", "sem", "que", "como", "ou", "ao", "aos", "se", "x",
}

LEITURAS = {
    "edit_history": [
        "A amostra são as N revisões mais recentes do artigo, não o histórico inteiro: a janela de tempo muda de artigo para artigo.",
        "Reversão é medida pelas tags do MediaWiki (mw-reverted, mw-undo, mw-rollback). Essas tags são recentes; edições antigas parecem 'calmas' porque o meio ainda não as marcava. Use revert_rate_tagged_era (só conta edições desde tagged_era_start) para comparar.",
        "'Bot' é quem tem hoje a flag de bot. Robôs sem flag ou desativados contam como humanos registrados.",
        "Anônimos são IPs ou contas temporárias: um mesmo endereço pode ser várias pessoas, e uma pessoa vários endereços. 'Editores únicos' conta contas, não gente.",
        "Quem é revertido (reverted_by_actor) mostra como a plataforma distribui confiança, não só quem 'erra'.",
    ],
    "controversy": [
        "O ranking ordena por taxa de reversão: é uma medida de disputa registrada pela plataforma, não de discordância social sobre o tema.",
        "A taxa só conta edições desde plataforma.tag_era_start (primeira tag mw-reverted do corpus): antes disso o meio não registrava o objeto 'edição revertida'.",
        "Compare plataforma.last_anon_edit com tag_era_start: se a edição anônima some perto de quando as reversões passam a ser marcadas, 'anônimo não é revertido' é efeito de regras da plataforma (quem pode editar, o que é etiquetado), não comportamento.",
        "O recorte de artigos veio dos links recíprocos da página-semente, ordenados por pageviews: o conjunto já é moldado pela estrutura de links e pela atenção.",
        "Artigos protegidos contra edição têm menos reversões por regra da plataforma, não por consenso.",
    ],
    "link_network": [
        "Um link na Wikipedia é uma decisão editorial (e muitas vezes vem de predefinições/navboxes), não uma medida de proximidade conceitual.",
        "A rede só contém os artigos coletados: grau e densidade valem dentro do recorte, não na enciclopédia.",
        "No recorte automático os vizinhos são escolhidos por terem link recíproco com a semente: a centralidade da semente e a alta reciprocidade são consequência do critério, não achado.",
    ],
    "editions": [
        "Cada edição linguística é uma comunidade com regras próprias: tamanho e audiência diferentes mostram o tema como referência cultural local, não 'a mesma página traduzida'.",
        "Pageviews excluem robôs identificados e agregam leitores de vários países por idioma (pt soma Brasil e Portugal).",
    ],
    "rank_effect": [
        "O CTR cai com a posição: o clique mede a ordenação do buscador tanto quanto o interesse de quem busca.",
        "Impressão é o buscador decidindo exibir o site; a consulta só existe no dado se o algoritmo a associou à página.",
        "Posição é uma média no período: esconde personalização, localização e variação diária.",
        "Atenção: neste projeto os dados de busca são sintéticos (simulador); a curva reflete o modelo de CTR do simulador.",
    ],
    "query_network": [
        "As consultas são o vocabulário que o buscador registrou e resolveu mostrar; termos raros são omitidos pela plataforma real.",
        "Coocorrência de termos na mesma consulta aproxima como o tema é formulado por quem busca, dentro do que o ranking deixou aparecer.",
        "Atenção: neste projeto os dados de busca são sintéticos (simulador).",
    ],
}


def _gini(counts: pd.Series) -> float:
    x = counts.sort_values().to_numpy(dtype=float)
    n = len(x)
    if n == 0 or x.sum() == 0:
        return 0.0
    ranks = pd.RangeIndex(1, n + 1).to_numpy()
    return round(float(2 * (ranks * x).sum() / (n * x.sum()) - (n + 1) / n), 4)


def edit_history_profile(revs: pd.DataFrame, tagged_era_start: Any = None) -> Dict[str, Any]:
    """
    Perfil do histórico de edições de um artigo (quem edita, quanto, quem é revertido, quando).

    `tagged_era_start`: desde quando o meio marca reversões (tag mw-reverted). Sem valor, usa a
    primeira ocorrência no próprio artigo; ao comparar artigos, passe a primeira do corpus.
    """
    if revs.empty:
        return {"total_edits": 0}

    df = revs.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df["tags"] = df["tags"].map(lambda t: t.split("|") if isinstance(t, str) else list(t))
    df["reverting"] = df["tags"].map(lambda t: bool(REVERTING_TAGS & set(t)))
    df["reverted"] = df["tags"].map(lambda t: REVERTED_TAG in t)
    total = len(df)

    per_editor = df.groupby("user").size().sort_values(ascending=False)
    top_n = max(1, round(len(per_editor) * 0.1))
    actor_of = df.dropna(subset=["user"]).drop_duplicates("user").set_index("user")["actor_type"]

    month = df["timestamp"].dt.tz_localize(None).dt.to_period("M")
    months = pd.period_range(month.min(), month.max(), freq="M")
    edits = month.value_counts().reindex(months, fill_value=0)
    reverted = month[df["reverted"]].value_counts().reindex(months, fill_value=0)
    threshold = edits.mean() + 2 * edits.std(ddof=0)

    era = pd.to_datetime(tagged_era_start, utc=True) if tagged_era_start is not None else (
        df.loc[df["reverted"], "timestamp"].min() if df["reverted"].any() else None)
    in_era = df[df["timestamp"] >= era] if era is not None else df.iloc[0:0]

    return {
        "total_edits": total,
        "unique_editors": int(df["user"].nunique()),
        "sample_window": {"first": df["timestamp"].min().isoformat(), "last": df["timestamp"].max().isoformat()},
        "actor_shares": {k: round(v / total, 4) for k, v in df["actor_type"].value_counts().items()},
        "interface_shares": {
            "visualeditor": round(df["tags"].map(lambda t: "visualeditor" in t).mean(), 4),
            "mobile": round(df["tags"].map(lambda t: any(x.startswith("mobile") for x in t)).mean(), 4),
        },
        "concentration": {
            "gini": _gini(per_editor),
            "top_editor_share": round(per_editor.iloc[0] / total, 4) if len(per_editor) else 0.0,
            "top10pct_share": round(per_editor.head(top_n).sum() / total, 4) if len(per_editor) else 0.0,
        },
        "reverts": {
            "reverting_edits": int(df["reverting"].sum()),
            "reverted_edits": int(df["reverted"].sum()),
            "revert_rate": round(df["reverted"].mean(), 4),
            "reverted_by_actor": {k: int(v) for k, v in df.loc[df["reverted"], "actor_type"].value_counts().items()},
            "tagged_era_start": era.isoformat() if era is not None else None,
            "edits_in_tagged_era": len(in_era),
            "revert_rate_tagged_era": round(in_era["reverted"].mean(), 4) if len(in_era) else None,
        },
        "top_editors": [
            {"user": u, "edits": int(n), "actor_type": actor_of[u]} for u, n in per_editor.head(10).items()
        ],
        "timeline": [
            {"period": str(p), "edits": int(edits[p]), "reverted": int(reverted[p])} for p in months
        ],
        "bursts": [
            {"period": str(p), "edits": int(n)} for p, n in edits.items() if n > threshold
        ],
    }


def link_network(edges: pd.DataFrame, nodes: List[str]) -> Dict[str, Any]:
    """Rede dirigida de hiperlinks entre os artigos coletados."""
    node_set = set(nodes)
    pairs = {
        (s, t) for s, t in zip(edges["source"], edges["target"])
        if s != t and s in node_set and t in node_set
    } if len(edges) else set()
    n = len(node_set)
    in_deg = pd.Series([t for _, t in pairs]).value_counts() if pairs else {}
    out_deg = pd.Series([s for s, _ in pairs]).value_counts() if pairs else {}
    node_rows = [
        {"id": x, "in_degree": int(in_deg.get(x, 0)), "out_degree": int(out_deg.get(x, 0))} for x in node_set
    ]
    node_rows.sort(key=lambda r: (-r["in_degree"], -r["out_degree"], r["id"]))
    return {
        "node_count": n,
        "edge_count": len(pairs),
        "density": round(len(pairs) / (n * (n - 1)), 4) if n > 1 else 0.0,
        "reciprocity": round(sum((t, s) in pairs for s, t in pairs) / len(pairs), 4) if pairs else 0.0,
        "nodes": node_rows,
        "edges": [{"source": s, "target": t, "reciprocal": (t, s) in pairs} for s, t in sorted(pairs)],
    }


def rank_effect(queries: pd.DataFrame) -> Dict[str, Any]:
    """Quanto do clique é explicado pela posição no ranking (o meio produzindo o dado)."""
    if queries.empty:
        return {"curve": [], "top3_click_share": None, "top3_impression_share": None,
                "spearman_position_ctr": None}

    df = queries.copy()
    df["pos"] = df["position"].round().clip(lower=1).astype(int)
    curve = df.groupby("pos").agg(
        queries=("query", "count"), impressions=("impressions", "sum"), clicks=("clicks", "sum")
    )
    top3 = df[df["pos"] <= 3]
    ctr = df["clicks"] / df["impressions"].where(df["impressions"] > 0)
    rho = df["position"].rank().corr(ctr.rank()) if len(df) >= 3 else None

    def share(col):
        return round(float(top3[col].sum() / df[col].sum()), 4) if df[col].sum() else None

    return {
        "curve": [
            {"position": int(p), "queries": int(r.queries), "impressions": int(r.impressions),
             "clicks": int(r.clicks), "ctr": round(r.clicks / r.impressions, 4) if r.impressions else 0.0}
            for p, r in curve.iterrows()
        ],
        "top3_click_share": share("clicks"),
        "top3_impression_share": share("impressions"),
        "spearman_position_ctr": None if rho is None or pd.isna(rho) else round(float(rho), 4),
    }


def query_term_network(queries: pd.DataFrame) -> Dict[str, Any]:
    """Rede de coocorrência de termos nas consultas de busca."""
    nodes: Dict[str, Dict[str, int]] = {}
    edges: Dict[tuple, Dict[str, int]] = {}
    for row in queries.itertuples():
        terms = sorted({t for t in re.findall(r"\w+", str(row.query).lower()) if t not in STOPWORDS and len(t) > 1})
        for t in terms:
            n = nodes.setdefault(t, {"queries": 0, "impressions": 0, "clicks": 0})
            n["queries"] += 1
            n["impressions"] += int(row.impressions)
            n["clicks"] += int(row.clicks)
        for pair in combinations(terms, 2):
            e = edges.setdefault(pair, {"weight": 0, "impressions": 0})
            e["weight"] += 1
            e["impressions"] += int(row.impressions)
    return {
        "nodes": sorted(({"id": t, **v} for t, v in nodes.items()), key=lambda n: (-n["impressions"], n["id"])),
        "edges": sorted(({"source": a, "target": b, **v} for (a, b), v in edges.items()),
                        key=lambda e: (-e["weight"], e["source"], e["target"])),
    }
