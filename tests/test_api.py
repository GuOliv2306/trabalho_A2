"""
Testes para endpoints da API FastAPI.

Execute com: pytest tests/test_api.py -v
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# ===== TESTES DE HEALTH CHECK =====

def test_health_check():
    """Testa endpoint de health check."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ===== TESTES DE DASHBOARD OVERVIEW =====

def test_get_kpis():
    """Testa endpoint de KPIs principais."""
    response = client.get("/api/v1/overview/kpis")
    assert response.status_code == 200
    
    data = response.json()
    assert "totalPaginas" in data
    assert "sessoesTotais" in data
    assert "conversoesTotais" in data
    assert "mediaBounceRate" in data
    assert "mediaSessionDuration" in data
    
    # Valida tipos
    assert isinstance(data["totalPaginas"], int)
    assert isinstance(data["sessoesTotais"], int)
    assert isinstance(data["conversoesTotais"], int)
    assert isinstance(data["mediaBounceRate"], (int, float))
    assert isinstance(data["mediaSessionDuration"], (int, float))
    
    # Valida ranges
    assert data["totalPaginas"] >= 0
    assert data["sessoesTotais"] >= 0
    assert data["conversoesTotais"] >= 0
    assert 0 <= data["mediaBounceRate"] <= 1
    assert data["mediaSessionDuration"] >= 0
    
    print("\n✓ KPIs retornados:")
    print(f"  - Total de Páginas: {data['totalPaginas']}")
    print(f"  - Sessões Totais: {data['sessoesTotais']}")
    print(f"  - Conversões Totais: {data['conversoesTotais']}")
    print(f"  - Média Bounce Rate: {data['mediaBounceRate']:.2%}")
    print(f"  - Média Session Duration: {data['mediaSessionDuration']:.1f}s")


# ===== TESTES DE ANÁLISES ESTÁTICAS =====

def test_get_correlation_matrix():
    """Testa endpoint de matriz de correlação."""
    response = client.get("/api/v1/analysis/correlation_matrix")
    assert response.status_code == 200
    
    data = response.json()
    assert "conversions" in data
    assert "engagementRate" in data
    assert "averageSessionDuration" in data
    
    # Valida estrutura de cada grupo
    for key in ["conversions", "engagementRate", "averageSessionDuration"]:
        assert isinstance(data[key], dict)
        # Cada grupo deve ter pelo menos 1 correlação
        assert len(data[key]) > 0
        # Valores de correlação devem estar entre -1 e 1
        for corr_key, corr_value in data[key].items():
            assert -1 <= corr_value <= 1, f"Correlação inválida: {corr_key}={corr_value}"
    
    print("\n✓ Matriz de Correlação:")
    print(f"  - Conversions: {data['conversions']}")
    print(f"  - Engagement Rate: {data['engagementRate']}")
    print(f"  - Session Duration: {data['averageSessionDuration']}")


# ===== TESTE DE DOCUMENTAÇÃO =====

def test_openapi_docs():
    """Testa se documentação OpenAPI está acessível."""
    response = client.get("/docs")
    assert response.status_code == 200
    print("\n✓ Documentação OpenAPI disponível em /docs")
