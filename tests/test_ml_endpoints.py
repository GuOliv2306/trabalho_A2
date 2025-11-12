"""
Testes para os novos endpoints de Machine Learning.

Valida os 3 endpoints ML:
- /api/v1/ml/channel_clusters
- /api/v1/ml/keyword_clusters  
- /api/v1/ml/page_clusters
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_channel_clusters():
    """Testa clustering de canais de tráfego."""
    print("\n" + "="*60)
    print("🧪 TESTE 1: Channel Clustering (K-Means)")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/ml/channel_clusters?n_clusters=3")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"📊 Algoritmo: {data['algoritmo']}")
            print(f"📈 Total de canais: {data['total_canais']}")
            print(f"🎯 Número de clusters: {data['n_clusters']}")
            print(f"\n📋 Resumo dos Segmentos:")
            for segment in data['segment_summary']:
                print(f"  • Cluster {segment['cluster']}: {segment['count']} canais")
                print(f"    - Média sessões: {segment['avg_sessions']:.0f}")
                print(f"    - Média usuários ativos: {segment['avg_activeUsers']:.0f}")
            
            print(f"\n🎨 Exemplos de canais por cluster:")
            for i in range(min(5, len(data['canais']))):
                canal = data['canais'][i]
                print(f"  • {canal['source']}/{canal['medium']} → Cluster {canal['cluster']}")
            
            return True
        else:
            print(f"❌ Erro: {response.status_code}")
            print(f"   {response.json()}")
            return False
            
    except Exception as e:
        print(f"❌ Exceção: {str(e)}")
        return False


def test_keyword_clusters():
    """Testa clustering de keywords do GSC."""
    print("\n" + "="*60)
    print("🧪 TESTE 2: Keyword Clustering (K-Means)")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/ml/keyword_clusters?n_clusters=4")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"📊 Algoritmo: {data['algoritmo']}")
            print(f"📈 Total de keywords: {data['total_keywords']}")
            print(f"🎯 Número de clusters: {data['n_clusters']}")
            print(f"\n📋 Resumo dos Segmentos:")
            for segment in data['segment_summary']:
                print(f"  • Cluster {segment['cluster']}: {segment['count']} keywords")
                print(f"    - Média clicks: {segment['avg_clicks']:.0f}")
                print(f"    - Média CTR: {segment['avg_ctr']:.4f}")
                print(f"    - Média posição: {segment['avg_position']:.1f}")
            
            print(f"\n🔑 Exemplos de keywords por cluster:")
            for i in range(min(5, len(data['keywords']))):
                kw = data['keywords'][i]
                print(f"  • '{kw['query']}' → Cluster {kw['cluster']} (CTR: {kw['ctr']:.4f})")
            
            return True
        else:
            print(f"❌ Erro: {response.status_code}")
            print(f"   {response.json()}")
            return False
            
    except Exception as e:
        print(f"❌ Exceção: {str(e)}")
        return False


def test_page_clusters():
    """Testa clustering de páginas por engajamento."""
    print("\n" + "="*60)
    print("🧪 TESTE 3: Page Clustering (K-Means)")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/ml/page_clusters?n_clusters=5")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"📊 Algoritmo: {data['algoritmo']}")
            print(f"📈 Total de páginas: {data['total_paginas']}")
            print(f"🎯 Número de clusters: {data['n_clusters']}")
            print(f"\n📋 Resumo dos Segmentos:")
            for segment in data['segment_summary']:
                print(f"  • Cluster {segment['cluster']}: {segment['count']} páginas")
                print(f"    - Média engagement: {segment['avg_engagement_rate']:.2f}")
                print(f"    - Média eventos: {segment['avg_event_count']:.0f}")
                print(f"    - Média duração: {segment['avg_average_session_duration']:.0f}s")
            
            print(f"\n📄 Exemplos de páginas por cluster:")
            for i in range(min(5, len(data['paginas']))):
                page = data['paginas'][i]
                print(f"  • {page['page_path']} → Cluster {page['cluster']} (Eng: {page['engagement_rate']:.2f})")
            
            return True
        else:
            print(f"❌ Erro: {response.status_code}")
            print(f"   {response.json()}")
            return False
            
    except Exception as e:
        print(f"❌ Exceção: {str(e)}")
        return False


def test_cluster_centers():
    """Testa os centros dos clusters (valores médios)."""
    print("\n" + "="*60)
    print("🧪 TESTE 4: Centros dos Clusters")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/ml/page_clusters?n_clusters=3")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"\n🎯 Centros dos Clusters (valores médios):")
            for i, center in enumerate(data['cluster_centers']):
                print(f"\n  Cluster {i}:")
                print(f"    - Engagement Rate: {center['engagement_rate']:.2f}")
                print(f"    - Event Count: {center['event_count']:.0f}")
                print(f"    - Session Duration: {center['average_session_duration']:.0f}s")
            
            return True
        else:
            print(f"❌ Erro: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exceção: {str(e)}")
        return False


if __name__ == "__main__":
    print("\n" + "🚀"*30)
    print("TESTES DOS ENDPOINTS DE MACHINE LEARNING")
    print("🚀"*30)
    
    print("\n⚠️  CERTIFIQUE-SE DE QUE:")
    print("  1. A API está rodando: uvicorn app.main:app --reload")
    print("  2. O banco foi populado: python tests/simulador_dados.py --clear --days 30")
    
    input("\n▶️  Pressione ENTER para iniciar os testes...")
    
    # Executa os testes
    results = []
    results.append(("Channel Clustering", test_channel_clusters()))
    results.append(("Keyword Clustering", test_keyword_clusters()))
    results.append(("Page Clustering", test_page_clusters()))
    results.append(("Cluster Centers", test_cluster_centers()))
    
    # Sumário final
    print("\n" + "="*60)
    print("📊 SUMÁRIO DOS TESTES")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{status} - {test_name}")
    
    print(f"\n🎯 Resultado: {passed}/{total} testes passaram")
    
    if passed == total:
        print("\n🎉 TODOS OS TESTES PASSARAM! Os módulos ML estão funcionando perfeitamente!")
    else:
        print("\n⚠️  Alguns testes falharam. Verifique se o banco está populado e a API está rodando.")
