"""
Testes de métodos digitais (análises puras, storage e rotas).

Não usam rede: a coleta da Wikipedia é substituída por dados fixos.
Execute com: pytest tests/test_digital_methods.py -v
Teste ao vivo (rede): RUN_NETWORK=1 pytest tests/test_digital_methods.py -v
"""

import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
import pytest
from fastapi.testclient import TestClient

import app.main as main
from src.collectors.db_storage import GA4DatabaseStorage
from src.digital_methods import analysis, wikipedia


def rev(revid, ts, user, actor="registered", size=100, tags=()):
    return {"revid": revid, "timestamp": ts, "user": user, "actor_type": actor,
            "size": size, "minor": False, "comment": "", "tags": list(tags)}


REVS = [
    rev(10, "2024-03-20T10:00:00Z", "Ana", size=900),
    rev(9, "2024-03-19T10:00:00Z", "Ana", size=800, tags=["mw-undo"]),
    rev(8, "2024-03-18T10:00:00Z", "1.2.3.4", "anon", size=950, tags=["mw-reverted", "mobile edit"]),
    rev(7, "2024-03-17T10:00:00Z", "Ana", size=800, tags=["mw-rollback"]),
    rev(6, "2024-03-16T10:00:00Z", "~2024-1", "anon", size=100, tags=["mw-reverted", "visualeditor"]),
    rev(5, "2024-03-15T10:00:00Z", "Ana", size=800, tags=["visualeditor"]),
    rev(4, "2024-01-10T10:00:00Z", "RoboBot", "bot", size=700),
    rev(3, "2023-06-10T10:00:00Z", "Beto", size=650),
    rev(2, "2022-06-10T10:00:00Z", "Ana", size=600),
    rev(1, "2021-06-10T10:00:00Z", "Caio", size=500),
]


# ===== HISTÓRICO DE EDIÇÕES =====

def test_edit_history_counts_and_actors():
    p = analysis.edit_history_profile(pd.DataFrame(REVS))
    assert p["total_edits"] == 10
    assert p["unique_editors"] == 6
    assert p["actor_shares"] == {"registered": 0.7, "anon": 0.2, "bot": 0.1}


def test_edit_history_reverts():
    p = analysis.edit_history_profile(pd.DataFrame(REVS))
    assert p["reverts"]["reverting_edits"] == 2   # mw-undo + mw-rollback
    assert p["reverts"]["reverted_edits"] == 2    # mw-reverted
    assert p["reverts"]["revert_rate"] == 0.2
    # só anônimos foram revertidos: o meio marca quem é "vandalismo"
    assert p["reverts"]["reverted_by_actor"] == {"anon": 2}
    # a taxa comparável só conta a era em que o meio já marcava reversões (5 edições desde 16/03)
    assert p["reverts"]["tagged_era_start"].startswith("2024-03-16")
    assert p["reverts"]["edits_in_tagged_era"] == 5
    assert p["reverts"]["revert_rate_tagged_era"] == 0.4


def test_edit_history_tagged_era_from_corpus():
    # era definida pelo corpus (outro artigo já tinha a tag em 2022): 9 edições desde então
    p = analysis.edit_history_profile(pd.DataFrame(REVS), tagged_era_start="2022-01-01T00:00:00Z")
    assert p["reverts"]["edits_in_tagged_era"] == 9
    assert p["reverts"]["revert_rate_tagged_era"] == round(2 / 9, 4)
    # sem nenhuma tag de reversão não há taxa comparável
    none = analysis.edit_history_profile(pd.DataFrame([rev(1, "2010-01-01T00:00:00Z", "u")]))
    assert none["reverts"]["revert_rate_tagged_era"] is None


def test_edit_history_concentration():
    p = analysis.edit_history_profile(pd.DataFrame(REVS))
    assert p["concentration"]["top_editor_share"] == 0.5   # Ana: 5 de 10
    assert 0 < p["concentration"]["gini"] < 1
    assert p["top_editors"][0] == {"user": "Ana", "edits": 5, "actor_type": "registered"}
    # todos com 1 edição -> gini 0
    flat = analysis.edit_history_profile(pd.DataFrame([rev(i, "2024-01-01T00:00:00Z", f"u{i}") for i in range(4)]))
    assert flat["concentration"]["gini"] == 0.0


def test_edit_history_timeline_and_bursts():
    p = analysis.edit_history_profile(pd.DataFrame(REVS))
    by_period = {t["period"]: t for t in p["timeline"]}
    assert by_period["2024-03"]["edits"] == 6
    assert by_period["2024-03"]["reverted"] == 2
    # meses sem edição entram como zero (silêncio também é dado)
    assert by_period["2023-07"]["edits"] == 0
    assert [b["period"] for b in p["bursts"]] == ["2024-03"]


def test_edit_history_interfaces():
    p = analysis.edit_history_profile(pd.DataFrame(REVS))
    assert p["interface_shares"]["visualeditor"] == 0.2
    assert p["interface_shares"]["mobile"] == 0.1


def test_edit_history_empty():
    assert analysis.edit_history_profile(pd.DataFrame())["total_edits"] == 0


# ===== REDE DE HIPERLINKS =====

def test_link_network():
    edges = pd.DataFrame([("A", "B"), ("B", "A"), ("A", "C"), ("D", "A")], columns=["source", "target"])
    net = analysis.link_network(edges, ["A", "B", "C", "D", "E"])
    nodes = {n["id"]: n for n in net["nodes"]}
    assert nodes["A"]["in_degree"] == 2 and nodes["A"]["out_degree"] == 2
    assert nodes["E"]["in_degree"] == 0 and nodes["E"]["out_degree"] == 0
    assert net["edge_count"] == 4
    assert net["density"] == round(4 / 20, 4)
    assert net["reciprocity"] == 0.5          # 2 das 4 arestas têm volta
    assert net["nodes"][0]["id"] == "A"       # ordenado por in_degree
    assert {"source": "A", "target": "B", "reciprocal": True} in net["edges"]


# ===== BUSCA: O RANKING PRODUZ O CLIQUE =====

QUERIES = pd.DataFrame([
    {"query": "comprar produto", "clicks": 300, "impressions": 1000, "position": 1.2},
    {"query": "produto barato", "clicks": 100, "impressions": 1000, "position": 2.8},
    {"query": "loja online", "clicks": 50, "impressions": 1000, "position": 5.1},
    {"query": "comprar online barato", "clicks": 10, "impressions": 1000, "position": 9.4},
])


def test_rank_effect():
    r = analysis.rank_effect(QUERIES)
    assert [b["position"] for b in r["curve"]] == [1, 3, 5, 9]
    assert r["curve"][0]["ctr"] == 0.3
    assert r["top3_click_share"] == round(400 / 460, 4)
    assert r["top3_impression_share"] == 0.5
    assert r["spearman_position_ctr"] == -1.0   # pior posição, menor CTR


def test_rank_effect_empty():
    assert analysis.rank_effect(pd.DataFrame())["curve"] == []


def test_query_term_network():
    net = analysis.query_term_network(QUERIES)
    nodes = {n["id"]: n for n in net["nodes"]}
    assert nodes["comprar"]["queries"] == 2
    assert nodes["comprar"]["impressions"] == 2000
    assert "de" not in nodes
    edges = {(e["source"], e["target"]): e["weight"] for e in net["edges"]}
    assert edges[("barato", "comprar")] == 1
    assert edges[("barato", "online")] == 1
    assert net["nodes"][0]["impressions"] >= net["nodes"][-1]["impressions"]


# ===== COLETOR (sem rede) =====

def test_parse_revisions_actor_and_diff():
    raw = [
        {"revid": 3, "parentid": 2, "user": "RoboBot", "timestamp": "2024-01-03T00:00:00Z", "size": 120, "tags": []},
        {"revid": 2, "parentid": 1, "user": "9.9.9.9", "anon": True, "timestamp": "2024-01-02T00:00:00Z", "size": 150, "tags": ["mw-reverted"]},
        {"revid": 1, "parentid": 0, "user": "~2024-77", "timestamp": "2024-01-01T00:00:00Z", "size": 100, "tags": []},
        {"revid": 0, "parentid": 0, "userhidden": True, "timestamp": "2023-12-31T00:00:00Z", "size": 90, "tags": []},
    ]
    rows = wikipedia.parse_revisions(raw, bots={"RoboBot"})
    assert [r["actor_type"] for r in rows] == ["bot", "anon", "anon", "hidden"]
    assert [r["size_diff"] for r in rows] == [-30, 50, 10, None]
    assert rows[3]["user"] is None


def test_reciprocal_neighbors_ranked_by_views():
    out = wikipedia.pick_neighbors(links={"A", "B", "C"}, backlinks={"B", "C", "D"},
                                   views={"B": 10, "C": 99}, max_pages=1)
    assert out == ["C"]


def test_collect_topic_with_curated_titles(monkeypatch):
    """Com `titles`, o corpus é o da pesquisadora: não há descoberta de vizinhos."""
    def links(s, lang, title, only=None):
        assert only is not None, "não deveria buscar vizinhos"
        return {"B"} if title == "A" else set()
    monkeypatch.setattr(wikipedia, "fetch_page_info", lambda s, lang, titles: {
        t: {"title": t, "pageid": 1, "length": 1, "pageviews_30d": 1} for t in titles if t != "Inexistente"})
    monkeypatch.setattr(wikipedia, "fetch_links", links)
    monkeypatch.setattr(wikipedia, "fetch_revisions", lambda *a: [])
    monkeypatch.setattr(wikipedia, "fetch_bots", lambda *a: set())
    monkeypatch.setattr(wikipedia, "fetch_editions", lambda *a: [])
    data = wikipedia.collect_topic(seed="A", titles=["B", "Inexistente", "A"])
    assert [p["title"] for p in data["pages"]] == ["A", "B"]
    assert data["links"] == [("A", "B")]
    assert data["not_found"] == ["Inexistente"]


def test_get_waits_retry_after_on_429(monkeypatch):
    class Resp:
        def __init__(self, status, headers=None):
            self.status_code, self.headers = status, headers or {}
        def raise_for_status(self):
            if self.status_code >= 400:
                raise wikipedia.requests.HTTPError(str(self.status_code))

    class Sess:
        def __init__(self, responses):
            self.responses = list(responses)
        def get(self, *a, **kw):
            return self.responses.pop(0)

    slept = []
    monkeypatch.setattr(wikipedia.time, "sleep", slept.append)
    r = wikipedia._get(Sess([Resp(429, {"Retry-After": "14"}), Resp(200)]), "u", {})
    assert r.status_code == 200 and 14 in slept
    # desiste depois de MAX_RETRIES e propaga o erro
    with pytest.raises(wikipedia.requests.HTTPError):
        wikipedia._get(Sess([Resp(429)] * wikipedia.MAX_RETRIES), "u", {})


# ===== STORAGE + ROTAS =====

@pytest.fixture
def client(tmp_path, monkeypatch):
    storage = GA4DatabaseStorage(db_path=str(tmp_path / "t.duckdb"))
    monkeypatch.setattr(main, "db", storage)
    monkeypatch.delenv("ADMIN_KEY", raising=False)
    yield TestClient(main.app)
    storage.close()


FAKE = {
    "lang": "pt", "seed": "Tema",
    "pages": [{"title": "Tema", "pageid": 1, "length": 900, "pageviews_30d": 50},
              {"title": "Vizinho", "pageid": 2, "length": 300, "pageviews_30d": 5}],
    "revisions": {"Tema": wikipedia.parse_revisions(
        [{**r, "parentid": 0} for r in REVS], bots={"RoboBot"}),
        "Vizinho": wikipedia.parse_revisions(
        [{"revid": 50, "parentid": 0, "user": "Ana", "timestamp": "2024-01-01T00:00:00Z", "size": 300, "tags": []}], bots=set())},
    "links": [("Tema", "Vizinho"), ("Vizinho", "Tema")],
    "editions": [{"lang": "pt", "title": "Tema", "length": 900, "pageviews_30d": 50},
                 {"lang": "en", "title": "Topic", "length": 5000, "pageviews_30d": 900}],
}


def test_wikipedia_flow(client, monkeypatch):
    monkeypatch.setattr(wikipedia, "collect_topic", lambda **kw: FAKE)

    r = client.post("/api/v1/digital-methods/wikipedia/collect", json={"seed": "Tema"})
    assert r.status_code == 200, r.text
    assert r.json()["stored"] == {"pages": 2, "revisions": 11, "links": 2, "editions": 2}

    # coletar de novo não duplica
    client.post("/api/v1/digital-methods/wikipedia/collect", json={"seed": "Tema"})
    assert main.get_db().query_df("SELECT COUNT(*) AS n FROM wiki_revisions")["n"][0] == 11

    r = client.get("/api/v1/digital-methods/wikipedia/edit-history", params={"title": "Tema"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total_edits"] == 10
    assert body["reverts"]["revert_rate"] == 0.2
    assert body["leitura_do_meio"]

    r = client.get("/api/v1/digital-methods/wikipedia/controversy")
    rank = r.json()["articles"]
    assert [a["title"] for a in rank] == ["Tema", "Vizinho"]
    assert rank[0]["revert_rate"] == 0.4 and rank[0]["edits_in_tag_era"] == 5
    assert rank[0]["pageviews_30d"] == 50
    # Vizinho só tem edição anterior à era das tags: sem taxa, vai para o fim
    assert rank[1]["revert_rate"] is None and rank[1]["edits_in_tag_era"] == 0
    assert r.json()["plataforma"]["tag_era_start"].startswith("2024-03-16")
    assert r.json()["plataforma"]["last_anon_edit"].startswith("2024-03-16")

    r = client.get("/api/v1/digital-methods/wikipedia/link-network")
    assert r.json()["reciprocity"] == 1.0

    r = client.get("/api/v1/digital-methods/wikipedia/editions", params={"title": "Tema"})
    eds = r.json()["editions"]
    assert eds[0]["lang"] == "en" and eds[0]["pageviews_share"] == round(900 / 950, 4)


def test_recollect_same_seed_replaces_corpus(client, monkeypatch):
    monkeypatch.setattr(wikipedia, "collect_topic", lambda **kw: FAKE)
    client.post("/api/v1/digital-methods/wikipedia/collect", json={"seed": "Tema"})
    smaller = {**FAKE, "pages": FAKE["pages"][:1], "revisions": {"Tema": FAKE["revisions"]["Tema"]}, "links": []}
    monkeypatch.setattr(wikipedia, "collect_topic", lambda **kw: smaller)
    client.post("/api/v1/digital-methods/wikipedia/collect", json={"seed": "Tema"})
    db = main.get_db()
    assert db.query_df("SELECT title FROM wiki_pages")["title"].tolist() == ["Tema"]
    assert db.query_df("SELECT COUNT(*) AS n FROM wiki_revisions")["n"][0] == 10
    assert db.query_df("SELECT COUNT(*) AS n FROM wiki_links")["n"][0] == 0


def test_wikipedia_missing_article_404(client):
    r = client.get("/api/v1/digital-methods/wikipedia/edit-history", params={"title": "Nada"})
    assert r.status_code == 404


def test_collect_requires_admin_key_when_configured(client, monkeypatch):
    monkeypatch.setenv("ADMIN_KEY", "segredo")
    monkeypatch.setattr(wikipedia, "collect_topic", lambda **kw: FAKE)
    assert client.post("/api/v1/digital-methods/wikipedia/collect", json={"seed": "Tema"}).status_code == 403
    assert client.post("/api/v1/digital-methods/wikipedia/collect",
                       json={"seed": "Tema", "admin_key": "segredo"}).status_code == 200


def test_search_routes(client):
    main.get_db().conn.execute("""
        INSERT INTO gsc_query_performance (id, site_url, query, clicks, impressions, ctr, position, start_date, end_date)
        VALUES (1,'s','comprar produto',300,1000,0.3,1.2,'2024-01-01','2024-01-31'),
               (2,'s','produto barato',100,1000,0.1,2.8,'2024-01-01','2024-01-31'),
               (3,'s','loja online',50,1000,0.05,5.1,'2024-01-01','2024-01-31')
    """)
    r = client.get("/api/v1/digital-methods/search/rank-effect")
    assert r.status_code == 200, r.text
    assert r.json()["curve"][0]["ctr"] == 0.3 and r.json()["leitura_do_meio"]
    r = client.get("/api/v1/digital-methods/search/query-network")
    assert any(n["id"] == "produto" and n["queries"] == 2 for n in r.json()["nodes"])


# ===== AO VIVO =====

@pytest.mark.skipif(not os.getenv("RUN_NETWORK"), reason="defina RUN_NETWORK=1 para testar a API real")
def test_live_collect_small():
    data = wikipedia.collect_topic(seed="Inteligência artificial", lang="pt", max_pages=3,
                                   rev_limit=100, edition_langs=["en", "es"])
    assert len(data["pages"]) == 3
    assert len(data["revisions"]["Inteligência artificial"]) == 100
    assert any(e["lang"] == "en" for e in data["editions"])
    profile = analysis.edit_history_profile(pd.DataFrame(data["revisions"]["Inteligência artificial"]))
    assert profile["unique_editors"] > 1
