"""
Testes da análise de conteúdo (Bardin): livro de códigos, codificador e confiabilidade.

Execute com: pytest tests/test_content_analysis.py -v
"""

import json
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
import pytest
from fastapi.testclient import TestClient

import app.main as main
from src.collectors.db_storage import GA4DatabaseStorage
from src.content_analysis import coder, reliability
from src.content_analysis.codebooks import CODEBOOKS
from tests.simulador_dados import ExperimentSimulator


def code_one(corpus, **unit):
    units = pd.DataFrame([{"unit_id": "u", **unit}])
    out = coder.code_units(CODEBOOKS[corpus], units)
    return dict(zip(out["variable"], out["category"]))


# ===== LIVRO DE CÓDIGOS =====

def test_codebooks_are_exhaustive_and_well_formed():
    """Regra de Bardin: categorias exaustivas (há sempre uma residual) e mutuamente exclusivas (um código por unidade)."""
    for corpus, book in CODEBOOKS.items():
        assert book["unidade_de_registro"] and book["regra_de_enumeracao"], corpus
        for name, var in book["variaveis"].items():
            codes = [c["codigo"] for c in var["categorias"]]
            assert len(codes) == len(set(codes)), (corpus, name)
            assert var["padrao"] in codes, (corpus, name)
            assert all(c["definicao"] for c in var["categorias"]), (corpus, name)
    json.dumps(CODEBOOKS)   # tem de ser serializável: a API publica o livro


# ===== CODIFICADOR POR REGRAS =====

@pytest.mark.parametrize("query,expected", [
    ("comprar tênis de corrida", "transacional"),
    ("tênis de corrida preço", "transacional"),
    ("onde comprar mochila de trilha", "transacional"),
    ("como escolher barraca de camping", "informacional"),
    ("o que é garrafa térmica", "informacional"),
    ("trilhamax login", "navegacional"),
    ("melhor fone bluetooth", "comercial"),
    ("bota de trekking ou jaqueta impermeável", "comercial"),
    ("lanterna de cabeça", "indefinida"),          # consulta seca: o texto não diz a intenção
])
def test_query_intent(query, expected):
    assert code_one("seo_consultas", text=query, serp_features="links_organicos:1.0")["intencao"] == expected


def test_serp_format_is_the_largest_area():
    assert code_one("seo_consultas", text="x", serp_features="video:0.3|shopping:0.7")["formato_serp"] == "shopping"
    assert code_one("seo_consultas", text="x", serp_features=None)["formato_serp"] == "links_organicos"


@pytest.mark.parametrize("unit,expected", [
    ({"unit_id": "https://example.com/", "word_count": 100, "byline": ""},
     {"tipo_pagina": "home", "profundidade": "rasa", "autoria": "sem_autoria"}),
    ({"unit_id": "https://example.com/produtos/item-03", "word_count": 300, "byline": "Por Ana Lima"},
     {"tipo_pagina": "produto", "profundidade": "media", "autoria": "autor_identificado"}),
    ({"unit_id": "https://example.com/blog/artigo-01", "word_count": 2000,
      "byline": "Por Ana Lima, fisioterapeuta com 10 anos de experiência"},
     {"tipo_pagina": "post", "profundidade": "profunda", "autoria": "autor_com_credenciais"}),
    ({"unit_id": "https://example.com/produtos/categoria-02", "word_count": 1200, "byline": "Equipe Editorial"},
     {"tipo_pagina": "categoria", "profundidade": "profunda", "autoria": "sem_autoria"}),
    ({"unit_id": "https://example.com/sobre", "word_count": None, "byline": None},
     {"tipo_pagina": "institucional", "profundidade": "rasa", "autoria": "sem_autoria"}),
])
def test_page_codes(unit, expected):
    out = coder.code_units(CODEBOOKS["seo_paginas"], pd.DataFrame([{"text": "t", **unit}]))
    assert dict(zip(out["variable"], out["category"])) == expected


@pytest.mark.parametrize("summary,tipo,origem", [
    ("", "sem_informacao", "em_branco"),
    ("/* Aplicações */", "sem_informacao", "gerado_pelo_software"),
    ("Desfeita a edição 123 de [[Special:Contribs/X|X]]", "reversao", "gerado_pelo_software"),
    ("Foram [[WP:REV|revertidas]] as edições de [[X]] para a última revisão de [[Y]]", "reversao", "gerado_pelo_software"),
    ("bot: revertidas edições de [[X]] ( modificação suspeita : -30)", "reversao", "gerado_pelo_software"),
    ("[[Wikipédia:Robôs|robô]]: Arquivamento de 14 URLs", "manutencao_assistida", "gerado_pelo_software"),
    ("adicionou [[Categoria:Tecnologia]] usando [[WP:HC|HotCat]]", "manutencao_assistida", "gerado_pelo_software"),
    ("Protegeu \"[[ChatGPT]]\": alterações indevidas", "administrativa", "gerado_pelo_software"),
    ("/* História */ Corrigiu erro ortográfico", "forma", "escrito_pelo_editor"),
    ("inserindo referência sobre o estudo de 2023", "fontes", "escrito_pelo_editor"),
    ("Adição de conteúdo", "conteudo", "escrito_pelo_editor"),
    ("muito obrigado", "sem_informacao", "escrito_pelo_editor"),
    # nome de seção não conta como conteúdo do resumo
    ("/* Referências */", "sem_informacao", "gerado_pelo_software"),
    # revisão 2 do livro, depois da primeira rodada de validação
    ("Adicionei preocupações na área de educação, com referências internacionais", "conteudo", "escrito_pelo_editor"),
    ("Foram inseridas seis referências em pontos importantes", "fontes", "escrito_pelo_editor"),
    ("Citei um pouco da introdução da IA na medicina", "sem_informacao", "escrito_pelo_editor"),
    ("+correções [[WP:SR|semiautomáticas]] (v0.57)", "manutencao_assistida", "gerado_pelo_software"),
    ("/* growthexperiments-addlink-summary-summary:3|0|0 */", "manutencao_assistida", "gerado_pelo_software"),
    ("Fulano moveu [[A]] para [[B]]", "administrativa", "gerado_pelo_software"),
    ("Substituí a imagem por outra de resolução melhor.", "conteudo", "escrito_pelo_editor"),
    ("negrito", "forma", "escrito_pelo_editor"),
    ("nova página: O viés algorítmico ocorre quando um sistema", "conteudo", "gerado_pelo_software"),
    ("[[WP:SPAM]] Desfeita a edição [[Special:Diff/1|1]] de [[X]]", "reversao", "gerado_pelo_software"),
    ("Ajuste nas Predefinições", "forma", "escrito_pelo_editor"),
])
def test_wikipedia_summary_codes(summary, tipo, origem):
    codes = code_one("wikipedia_resumos", text=summary)
    assert (codes["tipo_edicao"], codes["origem_do_resumo"]) == (tipo, origem)


def test_decision_rules_are_published():
    for corpus, book in CODEBOOKS.items():
        for name, var in book["variaveis"].items():
            assert isinstance(var.get("regras_de_decisao", []), list)
    assert CODEBOOKS["wikipedia_resumos"]["variaveis"]["tipo_edicao"]["regras_de_decisao"]
    assert CODEBOOKS["wikipedia_resumos"]["versao"] == 2


def test_code_units_shape_and_one_code_per_unit():
    units = pd.DataFrame({"unit_id": ["a", "b"], "text": ["comprar x", None], "serp_features": [None, None]})
    out = coder.code_units(CODEBOOKS["seo_consultas"], units)
    assert list(out.columns) == ["unit_id", "variable", "category"]
    assert len(out) == 4 and not out.duplicated(["unit_id", "variable"]).any()


# ===== CODIFICADOR POR IA (com dublê) =====

class FakeLLM:
    """Dublê do cliente OpenAI: devolve o que mandarmos e guarda o prompt."""
    def __init__(self, payload):
        self.payload, self.prompts = payload, []
        self.chat = self
        self.completions = self

    def create(self, **kw):
        self.prompts.append(kw["messages"][-1]["content"])
        msg = type("M", (), {"content": json.dumps(self.payload)})
        return type("R", (), {"choices": [type("C", (), {"message": msg})]})


def test_llm_coder_uses_codebook_and_rejects_invented_codes():
    units = pd.DataFrame({"unit_id": ["a", "b"], "text": ["comprar x", "lanterna"], "serp_features": [None, None]})
    fake = FakeLLM({"codes": [
        {"unit_id": "a", "variable": "intencao", "category": "transacional"},
        {"unit_id": "b", "variable": "intencao", "category": "categoria_inventada"},
        {"unit_id": "zzz", "variable": "intencao", "category": "comercial"},
    ]})
    out = coder.code_units_llm(CODEBOOKS["seo_consultas"], units, client=fake, variables=["intencao"])
    got = dict(zip(out["unit_id"], out["category"]))
    # código fora do livro e unidade sem resposta caem na categoria residual; unidade inventada é ignorada
    assert got == {"a": "transacional", "b": "indefinida"}
    assert "transacional" in fake.prompts[0] and "comprar x" in fake.prompts[0]


# ===== CONFIABILIDADE =====

def test_cohen_kappa_textbook():
    a = ["s"] * 25 + ["n"] * 25
    b = ["s"] * 20 + ["n"] * 5 + ["s"] * 10 + ["n"] * 15
    r = reliability.agreement(pd.Series(a), pd.Series(b))
    assert r["n"] == 50 and r["percent_agreement"] == 0.7 and r["cohen_kappa"] == 0.4


def test_krippendorff_alpha_textbook():
    # exemplo de Krippendorff (2011), dois observadores, dados binários: alfa = 0,095
    a = [0, 1, 0, 0, 0, 0, 0, 0, 1, 0]
    b = [1, 1, 1, 0, 0, 1, 0, 0, 0, 0]
    assert reliability.agreement(pd.Series(a), pd.Series(b))["krippendorff_alpha"] == 0.0952


def test_agreement_details_and_edge_cases():
    r = reliability.agreement(pd.Series(["x", "x", "y", "y"]), pd.Series(["x", "y", "y", "y"]))
    assert r["confusion"]["labels"] == ["x", "y"] and r["confusion"]["matrix"] == [[1, 1], [0, 2]]
    by = {c["category"]: c for c in r["per_category"]}
    # b é a referência: a disse "x" duas vezes e acertou uma (precisão 0,5); o único "x" de b foi achado (revocação 1)
    assert by["x"]["precision"] == 0.5 and by["x"]["recall"] == 1.0
    perfect = reliability.agreement(pd.Series(["x", "y"]), pd.Series(["x", "y"]))
    assert perfect["cohen_kappa"] == 1.0 and perfect["krippendorff_alpha"] == 1.0
    # uma categoria só: concordância total, mas kappa e alfa não têm o que medir
    const = reliability.agreement(pd.Series(["x", "x"]), pd.Series(["x", "x"]))
    assert const["percent_agreement"] == 1.0 and const["cohen_kappa"] is None and const["krippendorff_alpha"] is None
    assert reliability.agreement(pd.Series([], dtype=str), pd.Series([], dtype=str))["n"] == 0


# ===== ROTAS =====

REVS = {"lang": "pt", "seed": "Tema", "pages": [{"title": "Tema", "pageid": 1, "length": 1, "pageviews_30d": 1}],
        "links": [], "editions": [],
        "revisions": {"Tema": [
            {"revid": i, "parentid": 0, "timestamp": "2024-01-01T00:00:00Z", "user": "u", "actor_type": "registered",
             "size": 1, "size_diff": 1, "minor": False, "comment": c, "tags": t}
            for i, (c, t) in enumerate([("", []), ("Desfeita a edição 1 de [[X]]", ["mw-undo"]),
                                        ("Adição de conteúdo", ["mw-reverted"]), ("corrigiu erro ortográfico", [])], start=1)]}}


@pytest.fixture
def client(tmp_path, monkeypatch):
    storage = GA4DatabaseStorage(db_path=str(tmp_path / "t.duckdb"))
    storage.save_seo_experiment(ExperimentSimulator(seed=42).generate(days=120))
    storage.save_wiki(REVS)
    monkeypatch.setattr(main, "db", storage)
    monkeypatch.setattr(main, "REFERENCE_CODES", tmp_path / "ref.json")
    (tmp_path / "ref.json").write_text(json.dumps([
        {"corpus": "wikipedia_resumos", "unit_id": "2", "variable": "tipo_edicao", "category": "reversao"},
        {"corpus": "wikipedia_resumos", "unit_id": "3", "variable": "tipo_edicao", "category": "conteudo"},
        {"corpus": "wikipedia_resumos", "unit_id": "4", "variable": "tipo_edicao", "category": "conteudo"},
        {"corpus": "wikipedia_resumos", "unit_id": "4", "variable": "tipo_edicao", "category": "forma",
         "coder": "referencia_ia_desenvolvimento"},
    ]), encoding="utf-8")
    monkeypatch.delenv("ADMIN_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    yield TestClient(main.app)
    storage.close()


BASE = "/api/v1/content-analysis"


def test_codebook_route(client):
    r = client.get(f"{BASE}/codebooks")
    assert set(r.json()["corpora"]) == {"seo_consultas", "seo_paginas", "wikipedia_resumos"}
    one = client.get(f"{BASE}/codebooks", params={"corpus": "seo_consultas"}).json()
    assert "intencao" in one["codebook"]["variaveis"]
    assert client.get(f"{BASE}/codebooks", params={"corpus": "nada"}).status_code == 404


def test_code_then_results_then_reliability(client):
    r = client.post(f"{BASE}/code", json={"corpus": "seo_consultas"})
    assert r.status_code == 200, r.text
    assert r.json()["units"] == 231 and r.json()["coder"] == "regras"
    # codificar de novo não duplica
    client.post(f"{BASE}/code", json={"corpus": "seo_consultas"})
    n = main.get_db().query_df("SELECT COUNT(*) AS n FROM content_codes WHERE coder = 'regras'")["n"][0]
    assert n == 231 * 2

    res = client.get(f"{BASE}/results", params={"corpus": "seo_consultas", "variable": "intencao"}).json()
    rows = {c["category"]: c for c in res["categories"]}
    assert sum(c["n"] for c in res["categories"]) == 231
    assert rows["transacional"]["n"] == 72 and 0 < rows["transacional"]["ctr"] < 1
    assert res["leitura_do_meio"]

    rel = client.get(f"{BASE}/reliability", params={"corpus": "seo_consultas", "variable": "intencao",
                                                    "coder_b": "verdade_simulador"}).json()
    assert rel["n"] == 231 and rel["cohen_kappa"] > 0.8
    # as 12 consultas secas são o desacordo esperado, e a rota mostra quais são
    assert rel["percent_agreement"] == round(219 / 231, 4)
    assert len(rel["disagreements"]) == 12 and rel["disagreements"][0]["text"]


def test_wikipedia_corpus_results_and_reference(client):
    assert client.post(f"{BASE}/code", json={"corpus": "wikipedia_resumos"}).status_code == 200
    res = client.get(f"{BASE}/results", params={"corpus": "wikipedia_resumos", "variable": "tipo_edicao"}).json()
    rows = {c["category"]: c for c in res["categories"]}
    assert rows["conteudo"]["n"] == 1 and rows["conteudo"]["reverted_share"] == 1.0
    rel = client.get(f"{BASE}/reliability", params={"corpus": "wikipedia_resumos", "variable": "tipo_edicao"}).json()
    assert rel["coder_b"] == "referencia_ia" and rel["n"] == 3
    assert rel["percent_agreement"] == round(2 / 3, 4)      # a regra diz "forma" para a correção ortográfica
    assert "IA" in rel["aviso"]
    # a amostra de desenvolvimento (usada para revisar o livro) fica separada da de validação
    dev = client.get(f"{BASE}/reliability", params={"corpus": "wikipedia_resumos", "variable": "tipo_edicao",
                                                    "coder_b": "referencia_ia_desenvolvimento"}).json()
    assert dev["n"] == 1 and dev["percent_agreement"] == 1.0 and "IA" in dev["aviso"]


def test_sample_is_deterministic(client):
    a = client.get(f"{BASE}/sample", params={"corpus": "seo_consultas", "n": 10, "seed": 1}).json()["units"]
    b = client.get(f"{BASE}/sample", params={"corpus": "seo_consultas", "n": 10, "seed": 1}).json()["units"]
    assert a == b and len(a) == 10 and {"unit_id", "text"} <= set(a[0])


def test_content_routes_errors(client, monkeypatch):
    assert client.post(f"{BASE}/code", json={"corpus": "nada"}).status_code == 404
    assert client.get(f"{BASE}/results", params={"corpus": "seo_consultas", "variable": "nada"}).status_code == 404
    # nada codificado ainda
    assert client.get(f"{BASE}/results", params={"corpus": "seo_paginas", "variable": "autoria"}).status_code == 404
    # codificador por IA sem chave
    assert client.post(f"{BASE}/code", json={"corpus": "seo_consultas", "coder": "llm"}).status_code == 503
    monkeypatch.setenv("ADMIN_KEY", "k")
    assert client.post(f"{BASE}/code", json={"corpus": "seo_consultas"}).status_code == 403
