"""
Codificadores: aplicam um livro de códigos a um corpus.

- code_units: regras explícitas do livro (auditável, sem custo).
- code_units_llm: um modelo de linguagem recebe o livro como instrução (opcional, precisa de chave).

Entrada: DataFrame com `unit_id` e os campos que as variáveis leem.
Saída: DataFrame unit_id, variable, category — exatamente um código por unidade e variável.
"""

import json
import re
import unicodedata
from functools import lru_cache
from typing import Any, Dict, List, Optional

import pandas as pd


def _fold(text: str) -> str:
    """Minúsculas e sem acento: quem digita em buscador ou em resumo de edição costuma omiti-los."""
    return "".join(c for c in unicodedata.normalize("NFD", text.lower()) if not unicodedata.combining(c))


@lru_cache(maxsize=None)
def _compiled(pattern: str) -> "re.Pattern":
    return re.compile(_fold(pattern))


def _blank(value: Any) -> bool:
    return value is None or (isinstance(value, float) and pd.isna(value)) or value is pd.NA


def _largest_area(value: Any, default: str, valid: set) -> str:
    best, best_area = default, -1.0
    for part in ("" if _blank(value) else str(value)).split("|"):
        name, _, area = part.partition(":")
        name = name.strip().lower()
        try:
            area_value = float(area)
        except ValueError:
            continue
        if name in valid and area_value > best_area:
            best, best_area = name, area_value
    return best


def _code_value(variable: Dict[str, Any], value: Any) -> str:
    categories = variable["categorias"]
    if variable.get("maior_area"):
        return _largest_area(value, variable["padrao"], {c["codigo"] for c in categories})
    if any("faixa" in c for c in categories):
        number = pd.to_numeric(value, errors="coerce")
        if pd.isna(number):
            return variable["padrao"]
        for c in categories:
            low, high = c["faixa"]
            if number >= low and (high is None or number < high):
                return c["codigo"]
        return variable["padrao"]
    text = _fold("" if _blank(value) else str(value))
    if variable.get("remover"):
        text = _compiled(variable["remover"]).sub(" ", text)
    earliest = set(variable.get("primeira_no_texto", []))
    for c in categories:
        if c["codigo"] in earliest:
            continue
        if any(_compiled(pattern).search(text) for pattern in c.get("regex", [])):
            return c["codigo"]
    # entre estas categorias vale a ação declarada primeiro no texto, não a ordem do livro
    best, best_pos = variable["padrao"], len(text) + 1
    for c in categories:
        if c["codigo"] not in earliest:
            continue
        for pattern in c.get("regex", []):
            m = _compiled(pattern).search(text)
            if m and m.start() < best_pos:
                best, best_pos = c["codigo"], m.start()
    return best


def code_units(codebook: Dict[str, Any], units: pd.DataFrame, variables: Optional[List[str]] = None) -> pd.DataFrame:
    """Codificador por regras."""
    rows = []
    for name, variable in codebook["variaveis"].items():
        if variables and name not in variables:
            continue
        values = units[variable["campo"]] if variable["campo"] in units else pd.Series([None] * len(units), index=units.index)
        rows += [{"unit_id": str(u), "variable": name, "category": _code_value(variable, v)}
                 for u, v in zip(units["unit_id"], values)]
    return pd.DataFrame(rows, columns=["unit_id", "variable", "category"])


def _instructions(codebook: Dict[str, Any], variables: List[str]) -> str:
    lines = [f"Você é um codificador em uma análise de conteúdo. Unidade de registro: {codebook['unidade_de_registro']}.",
             "Para cada unidade e cada variável, escolha exatamente UM código da lista. Não invente códigos."]
    for name in variables:
        var = codebook["variaveis"][name]
        lines.append(f"\nVariável `{name}` (lê o campo `{var['campo']}`): {var['definicao']}")
        lines += [f"Regra de decisão: {rule}" for rule in var.get("regras_de_decisao", [])]
        for c in var["categorias"]:
            examples = f" Exemplos: {'; '.join(repr(e) for e in c['exemplos'])}." if c.get("exemplos") else ""
            lines.append(f"- {c['codigo']}: {c['definicao']}{examples}")
    lines.append('\nResponda só com JSON: {"codes": [{"unit_id": "...", "variable": "...", "category": "..."}]}')
    return "\n".join(lines)


def code_units_llm(codebook: Dict[str, Any], units: pd.DataFrame, client: Any, model: str = "gpt-5-mini",
                   variables: Optional[List[str]] = None, batch_size: int = 25) -> pd.DataFrame:
    """
    Codificador por IA. `client` é um cliente OpenAI (ou compatível). Resposta fora do
    livro, ou ausente, cai na categoria residual da variável; `.attrs["unanswered"]` conta
    quantos códigos caíram nela por falta de resposta válida.
    """
    variables = variables or list(codebook["variaveis"])
    fields = ["unit_id"] + sorted({codebook["variaveis"][v]["campo"] for v in variables} - {"unit_id"})
    instructions = _instructions(codebook, variables)
    valid = {v: {c["codigo"] for c in codebook["variaveis"][v]["categorias"]} for v in variables}
    answers: Dict[tuple, str] = {}
    records = units[[f for f in fields if f in units]].astype(object).where(units.notna(), None).to_dict("records")
    for start in range(0, len(records), batch_size):
        batch = records[start:start + batch_size]
        response = client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": "Você aplica livros de códigos com rigor e responde só em JSON."},
                      {"role": "user", "content": instructions + "\n\nUnidades:\n" + json.dumps(batch, ensure_ascii=False, default=str)}],
        )
        try:
            content = re.sub(r"^\s*```(?:json)?|```\s*$", "", response.choices[0].message.content.strip())
            codes = json.loads(content).get("codes")
        except (json.JSONDecodeError, AttributeError, TypeError):
            codes = None
        for c in codes if isinstance(codes, list) else []:
            if not isinstance(c, dict):
                continue
            variable, category = c.get("variable"), c.get("category")
            if isinstance(variable, str) and isinstance(category, str) and category in valid.get(variable, ()):
                answers[(str(c.get("unit_id")), variable)] = category
    wanted = [(str(u), v) for v in variables for u in units["unit_id"]]
    out = pd.DataFrame([{"unit_id": u, "variable": v, "category": answers.get((u, v), codebook["variaveis"][v]["padrao"])}
                        for u, v in wanted], columns=["unit_id", "variable", "category"])
    out.attrs["unanswered"] = sum(key not in answers for key in wanted)
    return out
