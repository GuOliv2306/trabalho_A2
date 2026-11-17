"""
Experimentos naturais: decisões da própria plataforma tratadas como intervenção.

A plataforma muda uma regra para todos de uma vez, em data conhecida. Compara-se a
edição linguística que mudou com outra que não mudou, nos mesmos artigos.
"""

from typing import Any, Dict, List

import pandas as pd

OUTCOMES = {
    "reverts": "edições que restauram uma versão anterior idêntica (reversões)",
    "human_edits": "edições feitas por pessoas (registradas ou anônimas)",
    "registered_edits": "edições de contas registradas",
    "anon_edits": "edições anônimas (checagem: tem de cair a zero)",
}

NATURAL_EXPERIMENTS: Dict[str, Dict[str, Any]] = {
    "fim_edicao_anonima_ptwiki": {
        "name": "Fim da edição anônima na Wikipédia em português",
        "description": "Desde 4 de outubro de 2020, por decisão da comunidade, só contas registradas editam a pt.wikipedia.",
        "date": "2020-10-04",
        "start": "2018-10-01",   # 24 meses antes
        "end": "2022-10-01",     # 24 meses depois
        "eligibility_months": 6,  # primeiros meses da janela: só decidem quem entra, ficam fora da estimativa
        "treated_lang": "pt",
        "control_langs": ["es", "fr"],
        "default_seed": "Inteligência artificial",
        "referencia_externa": {
            "fonte": "Wikimedia Foundation, IP Editing Restriction Study / Portuguese Wikipedia",
            "url": "https://meta.wikimedia.org/wiki/IP_Editing:_Privacy_Enhancement_and_Abuse_Mitigation/IP_Editing_Restriction_Study/Portuguese_Wikipedia",
            "achado": "Na wiki inteira, as reversões caíram cerca de 44% a 47% na comparação com o mesmo trimestre do ano anterior.",
            "como_comparar": "O estudo compara pt com ela mesma um ano antes, na wiki inteira e contando edições revertidas em 48 horas. "
                             "Aqui são poucos artigos, comparados com outra edição linguística, contando reversões por conteúdo idêntico. "
                             "Espere a mesma direção, não o mesmo número.",
        },
    },
}

PRESSUPOSTOS = [
    "Sem a mudança de regra, os artigos em português teriam variado na mesma proporção que os mesmos artigos no idioma de controle (veja placebo_pre).",
    "Nada mais mudou só na edição em português na mesma época. A pandemia de 2020 e a onda de interesse por IA depois de 2022 atingem os dois idiomas, mas não necessariamente por igual.",
    "A edição de controle não mudou a própria regra no período.",
    "Os artigos entram só se estavam abertos a anônimos nos dois idiomas; artigos já protegidos não sofreram a intervenção.",
    "Quem entra é decidido pelos primeiros meses da janela, e esses meses ficam fora da estimativa: escolher artigos por terem anônimos e medir no mesmo período inflaria o 'antes'.",
]

LEITURA_DO_MEIO = [
    "A intervenção é da plataforma: uma regra de quem pode editar. O 'comportamento' medido muda porque a regra mudou, não porque as pessoas mudaram.",
    "Reversão aqui é a edição que devolve o artigo a um conteúdo idêntico a uma das 15 versões anteriores. Não depende das tags do MediaWiki, que só passaram a marcar edições revertidas em 2020.",
    "Com a regra nova, parte de quem editava sem conta passa a editar com conta: 'edições registradas' sobe sem que haja gente nova.",
    "São poucos artigos, vizinhos de uma página-semente: o resultado vale para esse recorte, não para a Wikipédia inteira.",
    "Robôs que combatem vandalismo também revertem; menos vandalismo anônimo reduz o trabalho deles, e isso entra na conta das reversões.",
]


def estimation_start(experiment: Dict[str, Any]) -> pd.Timestamp:
    """Primeiro mês usado na estimativa (depois do período de elegibilidade)."""
    return pd.Timestamp(experiment["start"]) + pd.DateOffset(months=experiment["eligibility_months"])


def eligible_pairs(units: pd.DataFrame, monthly: pd.DataFrame, experiment: Dict[str, Any], control_lang: str) -> List[str]:
    """
    Pares (mesmo artigo nos dois idiomas) que de fato sofreram a intervenção: criados antes
    da janela e com alguma edição anônima no período de elegibilidade, nos dois idiomas.
    """
    langs = [experiment["treated_lang"], control_lang]
    month = pd.to_datetime(monthly["month"])
    year_before = monthly[month < estimation_start(experiment)]
    ok = None
    for lang in langs:
        u = units[units["lang"] == lang]
        created = pd.to_datetime(u["created"], utc=True, errors="coerce").dt.tz_localize(None)
        existed = set(u.loc[created < pd.Timestamp(experiment["start"]), "pair"])
        anon = year_before[year_before["lang"] == lang].groupby("pair")["anon_edits"].sum()
        good = existed & set(anon[anon > 0].index)
        ok = good if ok is None else ok & good
    return sorted(ok or [])


def panel(monthly: pd.DataFrame, pairs: List[str], experiment: Dict[str, Any], control_lang: str, outcome: str) -> pd.DataFrame:
    """Painel unit, date, y, treated dos pares elegíveis, para os estimadores de `analysis`."""
    df = monthly[monthly["pair"].isin(pairs) & monthly["lang"].isin([experiment["treated_lang"], control_lang])
                 & (pd.to_datetime(monthly["month"]) >= estimation_start(experiment))]
    return pd.DataFrame({
        "unit": df["lang"] + ":" + df["pair"],
        "date": pd.to_datetime(df["month"]),
        "y": df[outcome].astype(float),
        "treated": df["lang"] == experiment["treated_lang"],
    })
