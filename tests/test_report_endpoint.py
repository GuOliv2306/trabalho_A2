"""
Teste simples do endpoint de relatórios com Agno.
"""
import sys
from pathlib import Path

# Adiciona src ao path
sys.path.append(str(Path(__file__).parent.parent))

import asyncio
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_report_endpoint_basic():
    """Testa geração básica de relatório."""
    print("\n🧪 Testando endpoint de relatórios...")
    
    response = client.post(
        "/api/v1/reports/generate",
        json={
            "period_days": 7,
            "detail_level": "executive",
            "language": "pt-br"
        }
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Relatório gerado com sucesso!")
        print(f"   Report ID: {data.get('report_id')}")
        print(f"   Confidence Score: {data.get('metadata', {}).get('confidence_score')}")
        print(f"   Período: {data.get('period', {}).get('days')} dias")
        print(f"   Seções: {len(data.get('sections', []))}")
        print(f"   Recomendações: {len(data.get('recommendations', []))}")
        
        # Mostrar início do executive summary
        summary = data.get('executive_summary', '')
        if summary:
            preview = summary[:200] + "..." if len(summary) > 200 else summary
            print(f"\n📄 Executive Summary (preview):")
            print(f"   {preview}")
        
        return True
    else:
        print(f"❌ Erro: {response.status_code}")
        print(f"   Detalhes: {response.text}")
        return False


def test_report_with_focus_areas():
    """Testa relatório com áreas de foco."""
    print("\n🧪 Testando relatório com foco em traffic e conversions...")
    
    response = client.post(
        "/api/v1/reports/generate",
        json={
            "period_days": 30,
            "focus_areas": ["traffic", "conversions"],
            "detail_level": "detailed",
            "language": "pt-br"
        }
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Relatório gerado!")
        print(f"   Focus Areas: {data.get('metadata', {}).get('request_parameters', {}).get('focus_areas')}")
        return True
    else:
        print(f"❌ Erro: {response.status_code}")
        return False


def test_health_check():
    """Testa se API está rodando."""
    print("\n🧪 Testando health check...")
    response = client.get("/health")
    
    if response.status_code == 200:
        print("✅ API está funcionando!")
        return True
    else:
        print(f"❌ API não está respondendo: {response.status_code}")
        return False


if __name__ == "__main__":
    print("="*60)
    print("🚀 TESTE DO ENDPOINT DE RELATÓRIOS COM AGNO")
    print("="*60)
    
    # Verificar se API key está configurada
    import os
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  AVISO: OPENAI_API_KEY não configurada!")
        print("   Configure com: export OPENAI_API_KEY=sk-proj-...")
        print("   Ou crie arquivo .env na raiz do projeto")
        print("\n   O teste usará modo fallback (sem IA)")
    
    results = []
    
    # Teste 1: Health Check
    results.append(("Health Check", test_health_check()))
    
    # Teste 2: Relatório Básico
    results.append(("Relatório Básico", test_report_endpoint_basic()))
    
    # Teste 3: Relatório com Focus Areas
    results.append(("Relatório com Focus", test_report_with_focus_areas()))
    
    # Resumo
    print("\n" + "="*60)
    print("📊 RESUMO DOS TESTES")
    print("="*60)
    
    for name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{name:.<40} {status}")
    
    total = len(results)
    passed = sum(1 for _, r in results if r)
    print(f"\nTotal: {passed}/{total} testes passaram")
    
    if passed == total:
        print("\n🎉 Todos os testes passaram!")
    else:
        print("\n⚠️  Alguns testes falharam. Verifique os logs acima.")
