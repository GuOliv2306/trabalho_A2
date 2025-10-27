#!/usr/bin/env python3
"""
Script para testar os endpoints da API com os dados simulados.
"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def test_endpoint(endpoint: str, description: str) -> None:
    """Testa um endpoint e exibe o resultado."""
    print(f"\n{'='*60}")
    print(f"🔍 Testando: {description}")
    print(f"📍 Endpoint: {endpoint}")
    print('='*60)
    
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"✅ Status: {response.status_code}")
        print(f"📊 Resposta:")
        print(json.dumps(data, indent=2, ensure_ascii=False)[:500])
        
        if len(json.dumps(data)) > 500:
            print(f"\n... (resposta truncada, total: {len(json.dumps(data))} caracteres)")
            
    except requests.exceptions.ConnectionError:
        print("❌ ERRO: API não está rodando!")
        print("   Execute: python -m uvicorn app.main:app --reload --port 8000")
    except requests.exceptions.Timeout:
        print("❌ ERRO: Timeout ao acessar a API")
    except requests.exceptions.RequestException as e:
        print(f"❌ ERRO: {e}")

def main():
    """Testa todos os endpoints principais."""
    print("\n" + "🚀 TESTANDO API COM DADOS SIMULADOS " + "🚀".center(60))
    
    endpoints = [
        ("/api/v1/overview/kpis", "KPIs Gerais do Dashboard"),
        ("/api/v1/ga4/traffic", "Dados de Tráfego GA4"),
        ("/api/v1/ga4/conversions", "Dados de Conversões GA4"),
        ("/api/v1/ga4/engagement", "Dados de Engajamento GA4"),
        ("/api/v1/gsc/queries", "Performance de Queries GSC"),
        ("/api/v1/gsc/pages", "Performance de Páginas GSC"),
    ]
    
    for endpoint, description in endpoints:
        test_endpoint(endpoint, description)
        
    print(f"\n{'='*60}")
    print("✨ TESTES CONCLUÍDOS!")
    print(f"{'='*60}\n")
    print("💡 Dica: Acesse http://localhost:8000/docs para documentação interativa")

if __name__ == "__main__":
    main()
