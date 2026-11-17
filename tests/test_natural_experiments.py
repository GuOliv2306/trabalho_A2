"""
Testes do experimento natural na Wikipedia (fim da edição anônima na pt.wikipedia).

Sem rede: o histórico é fabricado. Ao vivo: RUN_NETWORK=1 pytest tests/test_natural_experiments.py -k live
"""

import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

import app.main as main
from src.collectors.db_storage import GA4DatabaseStorage
from src.digital_methods import wikipedia
from src.quasi_experiments import analysis as qe


# ===== REVERSÃO POR IDENTIDADE DE CONTEÚDO =====

def test_detect_reverts_by_identical_content():
    # A -> B (vandalismo) -> A (reversão) -> C -> C (edição nula, não é reversão) -> A (reversão antiga)
    assert wikipedia.detect_reverts(["A", "B", "A", "C", "C", "A"]) == [False, False, True, False, False, True]
    # fora da janela de 15 revisões não conta; sha1 ausente (conteúdo oculto) nunca é reversão
    far = ["A"] + [f"x{i}" for i in range(20)] + ["A"]
    assert wikipedia.detect_reverts(far)[-1] is False
    assert wikipedia.detect_reverts([None, None, "A", None]) == [False] * 4


def raw(ts, user="Ana", sha="s", anon=False):
    r = {"revid": 1, "timestamp": ts, "user": user, "sha1": sha}
    if anon:
        r["anon"] = True
    return r


def test_monthly_counts_fills_zero_months_and_separates_actors():
    revs = [raw("2020-01-05T00:00:00Z", sha="A"), raw("2020-01-06T00:00:00Z", "9.9.9.9", "B", anon=True),
            raw("2020-01-07T00:00:00Z", "RoboBot", "A"), raw("2020-03-01T00:00:00Z", "~2025-1", "C")]
    m = wikipedia.monthly_counts(revs, bots={"RoboBot"}, start="2020-01-01", end="2020-04-01")
    m = m.assign(month=m["month"].astype(str)).set_index("month")
    assert list(m.index) == ["2020-01-01", "2020-02-01", "2020-03-01"]
    jan = m.loc["2020-01-01"]
    assert (jan["human_edits"], jan["registered_edits"], jan["anon_edits"], jan["bot_edits"], jan["reverts"]) == (2, 1, 1, 1, 1)
    assert m.loc["2020-02-01", "human_edits"] == 0
    assert m.loc["2020-03-01", "anon_edits"] == 1        # conta temporária é anônima
    empty = wikipedia.monthly_counts([], bots=set(), start="2020-01-01", end="2020-03-01")
    assert len(empty) == 2 and empty["human_edits"].sum() == 0


# ===== DiD DE RAZÕES: FEITO PARA CONTAGENS PEQUENAS =====

def small_panel(effect, seed, n_units=40, months=48, t0=24, common=-0.2):
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2018-10-01", periods=months, freq="MS")
    rows = []
    for u in range(n_units):
        treated, base = u < n_units // 2, rng.uniform(0.3, 3.0)
        for i, d in enumerate(dates):
            lam = base * (1 + common if i >= t0 else 1) * (1 + effect if treated and i >= t0 else 1)
            rows.append({"unit": f"u{u}", "date": d, "y": rng.poisson(lam), "treated": treated})
    return pd.DataFrame(rows), dates[t0]


def test_ratio_did_is_unbiased_with_small_counts_where_log_did_is_not():
    est_ratio, est_log, cover = [], [], 0
    for seed in range(40):
        panel, t0 = small_panel(-0.40, seed)
        r = qe.ratio_did(panel, t0, n_boot=300, seed=seed)
        est_ratio.append(r["relative_effect"])
        est_log.append(qe.diff_in_diff(panel, t0)["relative_effect"])
        cover += r["ci95"][0] <= -0.40 <= r["ci95"][1]
    assert abs(np.mean(est_ratio) + 0.40) < 0.03
    assert np.mean(est_log) > -0.30                 # o log(1 + y) puxa para zero
    assert cover >= 34                              # ~95% de 40


def test_ratio_did_output_and_errors():
    panel, t0 = small_panel(-0.40, 1)
    r = qe.ratio_did(panel, t0, n_boot=200)
    assert r == qe.ratio_did(panel, t0, n_boot=200)
    assert r["n_treated"] == 20 and r["n_control"] == 20
    assert set(r["totals"]) == {"treated_pre", "treated_post", "control_pre", "control_post"}
    assert r["placebo_pre"]["ci95"][0] < 0 < r["placebo_pre"]["ci95"][1]
    assert abs(r["naive_before_after"] - (r["totals"]["treated_post"] / r["totals"]["treated_pre"] - 1)) < 1e-4
    with pytest.raises(ValueError):
        qe.ratio_did(panel[panel["treated"]], t0)
    zero = panel.assign(y=0)
    with pytest.raises(ValueError):
        qe.ratio_did(zero, t0)


# ===== ROTAS =====

def fake_collection(effect_on_reverts=-0.5):
    """12 pares pt/es, 48 meses. Em pt os anônimos somem em 2020-10 e as reversões caem pela metade."""
    rng = np.random.default_rng(5)
    months = pd.date_range("2018-10-01", periods=48, freq="MS")
    rows, units = [], []
    for i in range(14):
        for lang in ("pt", "es"):
            title = f"Artigo {i}" if lang == "pt" else f"Artículo {i}"
            # pares 12 e 13 nunca tiveram anônimos em pt (protegidos): não são elegíveis
            open_to_anons = i < 12 or lang == "es"
            units.append({"pair": f"Artigo {i}", "lang": lang, "title": title, "created": "2010-01-01T00:00:00Z"})
            for m in months:
                post = m >= pd.Timestamp("2020-10-01")
                anon = 0 if (lang == "pt" and post) or not open_to_anons else int(rng.poisson(4))
                registered = int(rng.poisson(6))
                reverts = int(rng.poisson(3 * (1 + effect_on_reverts if lang == "pt" and post else 1)))
                rows.append({"pair": f"Artigo {i}", "lang": lang, "title": title, "month": m.date(),
                             "human_edits": anon + registered, "registered_edits": registered, "anon_edits": anon,
                             "bot_edits": 1, "reverts": reverts})
    return {"experiment": "fim_edicao_anonima_ptwiki", "units": pd.DataFrame(units), "monthly": pd.DataFrame(rows)}


@pytest.fixture
def client(tmp_path, monkeypatch):
    storage = GA4DatabaseStorage(db_path=str(tmp_path / "t.duckdb"))
    monkeypatch.setattr(main, "db", storage)
    monkeypatch.delenv("ADMIN_KEY", raising=False)
    yield TestClient(main.app)
    storage.close()


BASE = "/api/v1/quasi-experiments/natural"


def test_natural_flow(client, monkeypatch):
    monkeypatch.setattr(wikipedia, "collect_history_pairs", lambda **kw: fake_collection())
    r = client.post(f"{BASE}/collect", json={"experiment": "fim_edicao_anonima_ptwiki"})
    assert r.status_code == 200, r.text
    assert r.json()["stored"]["units"] == 28
    # coletar de novo substitui
    client.post(f"{BASE}/collect", json={"experiment": "fim_edicao_anonima_ptwiki"})
    assert main.get_db().query_df("SELECT COUNT(*) AS n FROM wiki_monthly")["n"][0] == 28 * 48

    info = client.get(f"{BASE}/experiments").json()["experiments"][0]
    assert info["date"] == "2020-10-04" and info["pairs_collected"] == 14
    assert info["pairs_eligible"] == {"es": 12}         # os 2 pares já fechados a anônimos em pt saem

    est = client.get(f"{BASE}/estimate", params={"experiment": "fim_edicao_anonima_ptwiki", "outcome": "reverts"})
    assert est.status_code == 200, est.text
    j = est.json()
    assert j["n_treated"] == 12 and j["n_control"] == 12
    assert abs(j["relative_effect"] + 0.5) < 0.12 and j["ci95"][1] < 0
    assert j["method"] == "ratio_did" and j["control_lang"] == "es"
    # os 6 primeiros meses só servem para decidir quem entra; a estimativa começa depois deles
    assert len(j["series"]) == 42 and j["series"][0]["month"] == "2019-04-01"
    assert {"month", "treated", "control"} <= set(j["series"][0])
    assert j["n_pre"] == 18 and j["n_post"] == 24
    assert j["eligibility"]["months"] == ["2018-10-01", "2019-03-01"]
    assert j["referencia_externa"] and j["pressupostos"] and j["leitura_do_meio"]

    # checagem do tratamento: os anônimos somem mesmo
    anon = client.get(f"{BASE}/estimate", params={"experiment": "fim_edicao_anonima_ptwiki", "outcome": "anon_edits"}).json()
    assert anon["relative_effect"] == -1.0

    cf = client.get(f"{BASE}/estimate", params={"experiment": "fim_edicao_anonima_ptwiki", "outcome": "reverts",
                                                "method": "control_counterfactual"})
    assert cf.status_code == 200, cf.text
    assert cf.json()["relative_effect"] < -0.3


def test_natural_errors(client, monkeypatch):
    q = {"experiment": "fim_edicao_anonima_ptwiki", "outcome": "reverts"}
    assert client.get(f"{BASE}/estimate", params=q).status_code == 404            # nada coletado
    assert client.get(f"{BASE}/estimate", params={**q, "experiment": "x"}).status_code == 404
    assert client.get(f"{BASE}/estimate", params={**q, "outcome": "drop"}).status_code == 422
    assert client.post(f"{BASE}/collect", json={"experiment": "x"}).status_code == 404
    monkeypatch.setattr(wikipedia, "collect_history_pairs", lambda **kw: fake_collection())
    client.post(f"{BASE}/collect", json={"experiment": "fim_edicao_anonima_ptwiki"})
    assert client.get(f"{BASE}/estimate", params={**q, "control_lang": "fr"}).status_code == 404   # idioma não coletado
    monkeypatch.setenv("ADMIN_KEY", "k")
    assert client.post(f"{BASE}/collect", json={"experiment": "fim_edicao_anonima_ptwiki"}).status_code == 403


def test_eligibility_period_is_not_used_in_the_estimate():
    """Escolher artigos por terem anônimos e medir no mesmo período inflaria o 'antes' (regressão à média)."""
    from src.quasi_experiments import natural
    exp = natural.NATURAL_EXPERIMENTS["fim_edicao_anonima_ptwiki"]
    data = fake_collection()
    monthly, units = data["monthly"], data["units"]
    # o par 0 só teve anônimos em pt DEPOIS do período de elegibilidade: não entra
    late = (monthly["pair"] == "Artigo 0") & (monthly["lang"] == "pt") & (pd.to_datetime(monthly["month"]) < "2019-04-01")
    monthly.loc[late, "anon_edits"] = 0
    pairs = natural.eligible_pairs(units, monthly, exp, "es")
    assert "Artigo 0" not in pairs and len(pairs) == 11
    panel = natural.panel(monthly, pairs, exp, "es", "reverts")
    assert panel["date"].min() == pd.Timestamp("2019-04-01")


# ===== COLETOR (sem rede) =====

def test_collect_history_pairs_structure(monkeypatch):
    monkeypatch.setattr(wikipedia, "fetch_links", lambda s, lang, title, only=None: {"A", "B", "C"})
    monkeypatch.setattr(wikipedia, "fetch_langlinks", lambda s, lang, titles, target: {"A": "A-es", "B": "B-es"})
    monkeypatch.setattr(wikipedia, "fetch_history", lambda s, lang, title, start, end: [
        raw("2019-01-05T00:00:00Z", "9.9.9.9", "A", anon=True), raw("2021-01-05T00:00:00Z", "Ana", "B")])
    monkeypatch.setattr(wikipedia, "fetch_creation", lambda s, lang, title: "2010-01-01T00:00:00Z")
    monkeypatch.setattr(wikipedia, "fetch_bots", lambda s, lang, users: set())
    data = wikipedia.collect_history_pairs(seed="S", treated_lang="pt", control_langs=["es"],
                                           start="2018-10-01", end="2022-10-01", max_candidates=10, rng_seed=0)
    assert sorted(data["units"]["pair"].unique()) == ["A", "B"]          # "C" não existe em espanhol
    assert set(data["units"]["lang"]) == {"pt", "es"}
    assert len(data["monthly"]) == 2 * 2 * 48
    assert data["monthly"]["anon_edits"].sum() == 4


# ===== AO VIVO =====

@pytest.mark.skipif(not os.getenv("RUN_NETWORK"), reason="defina RUN_NETWORK=1 para testar a API real")
def test_live_history_small():
    data = wikipedia.collect_history_pairs(seed="Inteligência artificial", treated_lang="pt", control_langs=["es"],
                                           start="2020-06-01", end="2021-02-01", max_candidates=2, rng_seed=1)
    assert set(data["units"]["lang"]) == {"pt", "es"}
    assert data["monthly"]["month"].nunique() == 8
    assert data["monthly"]["human_edits"].sum() > 0
