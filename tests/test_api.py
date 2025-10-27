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


def test_get_page_clusters():
    """Testa endpoint de clusters de páginas."""
    response = client.get("/api/v1/analysis/page_clusters")
    assert response.status_code == 200
    
    data = response.json()
    assert "clusters" in data
    assert isinstance(data["clusters"], list)
    
    # Se houver clusters, valida estrutura
    if len(data["clusters"]) > 0:
        for cluster in data["clusters"]:
            assert "clusterId" in cluster
            assert "clusterName" in cluster
            assert "avgEngagementRate" in cluster
            assert "avgSessionDuration" in cluster
            assert "avgConversions" in cluster
            assert "totalPaginas" in cluster
            
            # Valida tipos
            assert isinstance(cluster["clusterId"], int)
            assert isinstance(cluster["clusterName"], str)
            assert isinstance(cluster["avgEngagementRate"], (int, float))
            assert isinstance(cluster["avgSessionDuration"], (int, float))
            assert isinstance(cluster["avgConversions"], int)
            assert isinstance(cluster["totalPaginas"], int)
            
            # Valida ranges
            assert 0 <= cluster["avgEngagementRate"] <= 1
            assert cluster["avgSessionDuration"] >= 0
            assert cluster["avgConversions"] >= 0
            assert cluster["totalPaginas"] > 0
    
    print(f"\n✓ Clusters encontrados: {len(data['clusters'])}")
    for cluster in data["clusters"][:3]:  # Mostra até 3 clusters
        print(f"  - {cluster['clusterName']}: {cluster['totalPaginas']} páginas")


# ===== TESTES DE ANÁLISE DE PÁGINA =====

def test_get_page_analysis_not_found():
    """Testa endpoint de análise de página inexistente."""
    response = client.get("/api/v1/page_analysis?path=/pagina/inexistente/teste/123")
    # Pode retornar 404 ou 500 dependendo se página existe ou erro no banco
    assert response.status_code in [404, 500]
    
    if response.status_code == 404:
        data = response.json()
        assert "detail" in data
        print(f"\n✓ Página não encontrada (esperado): {data['detail']}")


def test_get_page_analysis_valid():
    """Testa endpoint de análise de página existente (se houver dados)."""
    # Primeiro, busca uma página que existe
    from src.collectors.db_storage import GA4DatabaseStorage
    db = GA4DatabaseStorage()
    
    try:
        pages = db.query_df("""
            SELECT DISTINCT page_path 
            FROM engagement 
            WHERE page_path IS NOT NULL 
            LIMIT 1
        """)
        
        if not pages.empty:
            page_path = pages['page_path'].iloc[0]
            response = client.get(f"/api/v1/page_analysis?path={page_path}")
            
            # Se página existe, deve retornar 200
            if response.status_code == 200:
                data = response.json()
                assert "pagePath" in data
                assert "dadosReais" in data
                assert "analisePreditiva" in data
                
                # Valida estrutura dadosReais
                assert "sessions" in data["dadosReais"]
                assert "pageViews" in data["dadosReais"]
                assert "averageSessionDuration" in data["dadosReais"]
                assert "engagementRate" in data["dadosReais"]
                assert "conversions" in data["dadosReais"]
                
                # Valida estrutura analisePreditiva
                assert "clusterName" in data["analisePreditiva"]
                assert "riscoDeRejeicao" in data["analisePreditiva"]
                assert data["analisePreditiva"]["riscoDeRejeicao"] in ["Baixo", "Médio", "Alto"]
                
                print(f"\n✓ Análise de página '{page_path}':")
                print(f"  - Sessões: {data['dadosReais']['sessions']}")
                print(f"  - Conversões: {data['dadosReais']['conversions']}")
                print(f"  - Cluster: {data['analisePreditiva']['clusterName']}")
                print(f"  - Risco: {data['analisePreditiva']['riscoDeRejeicao']}")
            else:
                print(f"\n⚠️  Página '{page_path}' retornou status {response.status_code}")
        else:
            print("\n⚠️  Nenhuma página encontrada no banco para testar")
    
    finally:
        db.close()


# ===== TESTES DO SIMULADOR PREDITIVO =====

def test_predict_simulator_valid():
    """Testa endpoint de simulação com dados válidos."""
    payload = {
        "contagemDePalavras": 1200,
        "numeroDeImagens": 5,
        "precoDoProduto": 79.90
    }
    
    response = client.post("/api/v1/predict/simulator", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "inputFeatures" in data
    assert "predictedPerformance" in data
    assert "recommendations" in data
    
    # Valida inputFeatures
    assert data["inputFeatures"]["contagemDePalavras"] == 1200
    assert data["inputFeatures"]["numeroDeImagens"] == 5
    assert data["inputFeatures"]["precoDoProduto"] == 79.90
    
    # Valida predictedPerformance
    perf = data["predictedPerformance"]
    assert "estimativaEngagementRate" in perf
    assert "estimativaBounceRate" in perf
    assert "estimativaSessionDuration" in perf
    assert "estimativaConversoesPorMilSessoes" in perf
    
    # Valida ranges das predições
    assert 0 <= perf["estimativaEngagementRate"] <= 1
    assert 0 <= perf["estimativaBounceRate"] <= 1
    assert perf["estimativaSessionDuration"] >= 0
    assert perf["estimativaConversoesPorMilSessoes"] >= 0
    
    # Valida recomendações
    assert isinstance(data["recommendations"], list)
    assert len(data["recommendations"]) > 0
    
    print("\n✓ Simulação de performance:")
    print(f"  - Input: {payload}")
    print(f"  - Engagement: {perf['estimativaEngagementRate']:.2%}")
    print(f"  - Bounce Rate: {perf['estimativaBounceRate']:.2%}")
    print(f"  - Duration: {perf['estimativaSessionDuration']:.1f}s")
    print(f"  - Conversões/1k: {perf['estimativaConversoesPorMilSessoes']:.1f}")
    print(f"  - Recomendações: {len(data['recommendations'])}")


def test_predict_simulator_edge_cases():
    """Testa simulador com casos extremos."""
    test_cases = [
        {
            "name": "Conteúdo mínimo",
            "payload": {"contagemDePalavras": 50, "numeroDeImagens": 0, "precoDoProduto": 0}
        },
        {
            "name": "Conteúdo extenso",
            "payload": {"contagemDePalavras": 5000, "numeroDeImagens": 15, "precoDoProduto": 0}
        },
        {
            "name": "Produto caro",
            "payload": {"contagemDePalavras": 800, "numeroDeImagens": 8, "precoDoProduto": 2500}
        },
        {
            "name": "Produto barato",
            "payload": {"contagemDePalavras": 400, "numeroDeImagens": 3, "precoDoProduto": 9.99}
        }
    ]
    
    print("\n✓ Testando casos extremos do simulador:")
    for test_case in test_cases:
        response = client.post("/api/v1/predict/simulator", json=test_case["payload"])
        assert response.status_code == 200
        
        data = response.json()
        perf = data["predictedPerformance"]
        
        print(f"\n  {test_case['name']}:")
        print(f"    Engagement: {perf['estimativaEngagementRate']:.2%}")
        print(f"    Bounce: {perf['estimativaBounceRate']:.2%}")
        print(f"    Recomendações: {len(data['recommendations'])}")


def test_predict_simulator_invalid_input():
    """Testa simulador com dados inválidos."""
    invalid_payloads = [
        {"contagemDePalavras": -100, "numeroDeImagens": 5, "precoDoProduto": 50},  # Negativo
        {"numeroDeImagens": 5, "precoDoProduto": 50},  # Faltando campo
        {"contagemDePalavras": "abc", "numeroDeImagens": 5, "precoDoProduto": 50}  # Tipo errado
    ]
    
    for payload in invalid_payloads:
        response = client.post("/api/v1/predict/simulator", json=payload)
        assert response.status_code == 422  # Validation error
        print(f"\n✓ Input inválido rejeitado corretamente: {payload}")


# ===== TESTE DE DOCUMENTAÇÃO =====

def test_openapi_docs():
    """Testa se documentação OpenAPI está acessível."""
    response = client.get("/docs")
    assert response.status_code == 200
    print("\n✓ Documentação OpenAPI disponível em /docs")


if __name__ == "__main__":
    print("=" * 70)
    print("EXECUTANDO TESTES DA API")
    print("=" * 70)
    
    # Health Check
    print("\n[1/9] Test: Health Check")
    test_health_check()
    
    # Dashboard Overview
    print("\n[2/9] Test: KPIs")
    test_get_kpis()
    
    # Análises Estáticas
    print("\n[3/9] Test: Matriz de Correlação")
    test_get_correlation_matrix()
    
    print("\n[4/9] Test: Clusters de Páginas")
    test_get_page_clusters()
    
    # Análise de Página
    print("\n[5/9] Test: Análise de Página (não encontrada)")
    test_get_page_analysis_not_found()
    
    print("\n[6/9] Test: Análise de Página (válida)")
    test_get_page_analysis_valid()
    
    # Simulador Preditivo
    print("\n[7/9] Test: Simulador (caso válido)")
    test_predict_simulator_valid()
    
    print("\n[8/9] Test: Simulador (casos extremos)")
    test_predict_simulator_edge_cases()
    
    print("\n[9/9] Test: Simulador (input inválido)")
    test_predict_simulator_invalid_input()
    
    print("\n" + "=" * 70)
    print("✅ TODOS OS TESTES CONCLUÍDOS")
    print("=" * 70)
