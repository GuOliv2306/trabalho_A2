"""
Testes dos quase-experimentos: cada método tem de recuperar um efeito conhecido.

Execute com: pytest tests/test_quasi_experiments.py -v
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

import app.main as main
from src.collectors.db_storage import GA4DatabaseStorage
from src.quasi_experiments import analysis as qe
from tests.simulador_dados import ExperimentSimulator

START = pd.Timestamp("2025-01-01")


def make_panel(effect=0.20, shock=-0.15, n_units=40, days=100, t0=60, shock_day=80, seed=1, treated_bigger=True):
    """Painel unidade×dia: sazonalidade semanal, choque comum (o 'update do algoritmo') e efeito só nos tratados."""
    rng = np.random.default_rng(seed)
    base = rng.lognormal(4, 0.6, n_units)
    order = np.argsort(-base) if treated_bigger else rng.permutation(n_units)
    treated = np.zeros(n_units, dtype=bool)
    treated[order[: n_units // 2]] = True
    rows = []
    for d in range(days):
        season = 1 + 0.2 * np.sin(2 * np.pi * d / 7)
        common = (1 + shock) if d >= shock_day else 1.0
        for u in range(n_units):
            lift = (1 + effect) if (treated[u] and d >= t0) else 1.0
            rows.append({"unit": f"u{u}", "date": START + pd.Timedelta(days=d), "treated": bool(treated[u]),
                         "y": rng.poisson(base[u] * season * common * lift)})
    return pd.DataFrame(rows), START + pd.Timedelta(days=t0)


def daily(panel, treated=True):
    return panel[panel["treated"] == treated].groupby("date", as_index=False)["y"].sum()


# ===== DIFERENÇA-EM-DIFERENÇAS =====

def test_did_recovers_effect_despite_common_shock_and_selection():
    panel, t0 = make_panel(effect=0.20, shock=-0.15)
    r = qe.diff_in_diff(panel, t0)
    assert abs(r["relative_effect"] - 0.20) < 0.04
    assert r["ci95"][0] < 0.20 < r["ci95"][1]
    assert r["p_value"] < 0.01
    # antes/depois ingênuo absorve o choque comum e erra para baixo
    assert r["naive_before_after"] < r["relative_effect"] - 0.04
    assert r["n_treated"] == 20 and r["n_control"] == 20


def test_did_no_effect_is_not_significant():
    panel, t0 = make_panel(effect=0.0, shock=-0.15)
    r = qe.diff_in_diff(panel, t0)
    assert abs(r["relative_effect"]) < 0.03
    assert r["ci95"][0] < 0 < r["ci95"][1]


def test_did_parallel_trends_placebo_and_event_study():
    panel, t0 = make_panel()
    r = qe.diff_in_diff(panel, t0)
    assert r["placebo_pre"]["ci95"][0] < 0 < r["placebo_pre"]["ci95"][1]
    weeks = {w["week"]: w["gap"] for w in r["event_study"]}
    assert abs(weeks[-1]) < 0.05 and weeks[1] > 0.12
    # tendências não paralelas: os tratados já vinham crescendo antes -> o placebo acusa
    bad = panel.copy()
    day = (bad["date"] - START).dt.days
    bad.loc[bad["treated"], "y"] = (bad.loc[bad["treated"], "y"] * (1 + 0.01 * day[bad["treated"]])).round()
    rb = qe.diff_in_diff(bad, t0)
    assert not (rb["placebo_pre"]["ci95"][0] < 0 < rb["placebo_pre"]["ci95"][1])


def test_did_needs_both_groups_and_both_periods():
    panel, t0 = make_panel(n_units=6, days=30, t0=20, shock_day=25)
    with pytest.raises(ValueError):
        qe.diff_in_diff(panel[panel["treated"]], t0)
    with pytest.raises(ValueError):
        qe.diff_in_diff(panel, START + pd.Timedelta(days=500))


# ===== SÉRIE TEMPORAL INTERROMPIDA =====

def test_its_recovers_effect_without_confounder():
    panel, t0 = make_panel(effect=0.20, shock=0.0)
    r = qe.interrupted_time_series(daily(panel), t0)
    assert abs(r["relative_effect"] - 0.20) < 0.05
    assert r["ci95"][0] < 0.20 < r["ci95"][1]
    assert r["n_pre"] == 60 and r["n_post"] == 40
    point = r["series"][-1]
    assert set(point) == {"date", "actual", "counterfactual"} and point["actual"] > point["counterfactual"]


def test_its_is_biased_by_a_later_common_shock_unless_windowed():
    panel, t0 = make_panel(effect=0.20, shock=-0.15)
    full = qe.interrupted_time_series(daily(panel), t0)
    assert full["relative_effect"] < 0.15                      # o update contamina o pós
    cut = qe.interrupted_time_series(daily(panel), t0, end_date=START + pd.Timedelta(days=79))
    assert abs(cut["relative_effect"] - 0.20) < 0.06           # janela antes do update


def test_its_requires_enough_points():
    panel, t0 = make_panel(n_units=4, days=30, t0=20, shock_day=25)
    with pytest.raises(ValueError):
        qe.interrupted_time_series(daily(panel), START + pd.Timedelta(days=5))


def test_its_is_deterministic():
    panel, t0 = make_panel()
    assert qe.interrupted_time_series(daily(panel), t0) == qe.interrupted_time_series(daily(panel), t0)


# ===== CONTRAFACTUAL POR CONTROLES (lógica do CausalImpact) =====

def test_control_counterfactual_absorbs_common_shock():
    panel, t0 = make_panel(effect=0.20, shock=-0.15)
    r = qe.control_counterfactual(daily(panel, True), daily(panel, False), t0)
    assert abs(r["relative_effect"] - 0.20) < 0.04
    assert r["ci95"][0] < 0.20 < r["ci95"][1]
    assert r["pre_fit_r2"] > 0.8


# ===== TESTE A/B DE SEO =====

def test_ab_split_is_balanced_and_deterministic():
    pages = pd.DataFrame({"unit": [f"p{i}" for i in range(41)], "pre_metric": np.arange(41) * 10.0})
    a = qe.ab_split(pages, seed=7)
    assert a["assignment"] == qe.ab_split(pages, seed=7)["assignment"]
    assert a["assignment"] != qe.ab_split(pages, seed=8)["assignment"]
    groups = pd.Series(a["assignment"]).value_counts()
    assert abs(groups["tratado"] - groups["controle"]) <= 1
    assert abs(a["balance"]["relative_gap"]) < 0.1


def test_ab_test_randomization_inference():
    panel, t0 = make_panel(effect=0.10, shock=-0.15, treated_bigger=False)
    r = qe.ab_test(panel, t0)
    assert abs(r["relative_effect"] - 0.10) < 0.04
    assert r["permutation_p_value"] < 0.01
    null, t0 = make_panel(effect=0.0, treated_bigger=False, seed=3)
    assert qe.ab_test(null, t0)["permutation_p_value"] > 0.05


# ===== SIMULADOR =====

def test_simulator_is_deterministic_and_has_ground_truth():
    a, b = ExperimentSimulator(seed=42).generate(days=120), ExperimentSimulator(seed=42).generate(days=120)
    assert a["daily"].equals(b["daily"])
    assert set(a["pages"]["template"]) >= {"produto", "categoria", "post"}
    assert a["daily"].groupby("page")["date"].nunique().eq(120).all()
    inter = a["interventions"].set_index("intervention_id")
    assert inter.loc["descricao_produtos_ab", "randomized"] and not inter.loc["schema_categorias", "randomized"]
    assert (inter["kind"] == "externo").sum() == 1
    groups = a["intervention_pages"].groupby(["intervention_id", "grp"]).size()
    assert groups["descricao_produtos_ab", "tratado"] == groups["descricao_produtos_ab", "controle"] == 20


def test_methods_recover_simulator_truth():
    data = ExperimentSimulator(seed=42).generate(days=120)
    truth = data["interventions"].set_index("intervention_id")

    def panel_for(iid):
        m = data["intervention_pages"].query("intervention_id == @iid")
        p = data["daily"].merge(m, on="page").rename(columns={"page": "unit", "clicks": "y"})
        return p.assign(treated=p["grp"] == "tratado"), pd.Timestamp(truth.loc[iid, "date"])

    for iid, method in [("schema_categorias", qe.diff_in_diff), ("descricao_produtos_ab", qe.ab_test)]:
        panel, t0 = panel_for(iid)
        r = method(panel, t0)
        assert r["ci95"][0] < truth.loc[iid, "true_effect"] < r["ci95"][1], (iid, r["relative_effect"])
        assert abs(r["relative_effect"] - truth.loc[iid, "true_effect"]) < 0.05, (iid, r["relative_effect"])


# ===== ROTAS =====

@pytest.fixture
def client(tmp_path, monkeypatch):
    storage = GA4DatabaseStorage(db_path=str(tmp_path / "t.duckdb"))
    storage.save_seo_experiment(ExperimentSimulator(seed=42).generate(days=120))
    monkeypatch.setattr(main, "db", storage)
    yield TestClient(main.app)
    storage.close()


BASE = "/api/v1/quasi-experiments"


def test_routes_interventions_and_estimates(client):
    r = client.get(f"{BASE}/interventions")
    assert r.status_code == 200, r.text
    items = {i["intervention_id"]: i for i in r.json()["interventions"]}
    assert items["schema_categorias"]["n_treated"] == 12 and items["schema_categorias"]["true_effect"] == 0.20

    did = client.get(f"{BASE}/did", params={"intervention_id": "schema_categorias"}).json()
    assert abs(did["relative_effect"] - 0.20) < 0.05 and did["true_effect"] == 0.20
    assert did["pressupostos"] and did["leitura_do_meio"]

    ab = client.get(f"{BASE}/ab-test", params={"intervention_id": "descricao_produtos_ab"})
    assert ab.status_code == 200 and ab.json()["permutation_p_value"] < 0.05

    its = client.get(f"{BASE}/its", params={"intervention_id": "titulos_blog"})
    assert its.status_code == 200, its.text
    assert len(its.json()["series"]) == 120

    cf = client.get(f"{BASE}/control-counterfactual", params={"intervention_id": "titulos_blog"})
    assert cf.status_code == 200 and abs(cf.json()["relative_effect"] - cf.json()["true_effect"]) < 0.06


def test_routes_errors(client):
    assert client.get(f"{BASE}/did", params={"intervention_id": "nao_existe"}).status_code == 404
    # A/B exige sorteio: uma intervenção escolhida a dedo não é teste A/B
    assert client.get(f"{BASE}/ab-test", params={"intervention_id": "schema_categorias"}).status_code == 400
    # evento externo não tem páginas tratadas
    assert client.get(f"{BASE}/did", params={"intervention_id": "update_algoritmo"}).status_code == 400


def test_populate_database_also_generates_experiment_panel(tmp_path, monkeypatch):
    storage = GA4DatabaseStorage(db_path=str(tmp_path / "p.duckdb"))
    monkeypatch.setattr(main, "db", storage)
    monkeypatch.delenv("ADMIN_KEY", raising=False)
    c = TestClient(main.app)
    r = c.post("/api/v1/admin/populate-database", json={"days": 7, "overwrite": True})
    assert r.status_code == 200, r.text
    assert r.json()["statistics"]["experiment_panel_rows"] == 99 * 120
    assert c.get(f"{BASE}/did", params={"intervention_id": "schema_categorias"}).status_code == 200
    # as intervenções acompanham a data de hoje: o update do algoritmo fica 24 dias antes do fim
    dates = storage.query_df("SELECT MAX(date) AS last FROM seo_page_daily")["last"][0]
    upd = storage.query_df("SELECT date FROM seo_interventions WHERE kind = 'externo'")["date"][0]
    assert (pd.Timestamp(dates) - pd.Timestamp(upd)).days == 24
    storage.close()


def test_route_ab_split(client):
    r = client.get(f"{BASE}/ab-split", params={"template": "produto", "seed": 1})
    assert r.status_code == 200, r.text
    assert len(r.json()["assignment"]) == 40
    assert client.get(f"{BASE}/ab-split", params={"template": "nada"}).status_code == 404
