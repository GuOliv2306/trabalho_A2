#!/usr/bin/env python3
"""
Gerar dados simulados para propriedade GA4 usando Measurement Protocol.

Este script envia eventos fictícios para popular a propriedade GA4 com dados de teste.
Os dados aparecem nos relatórios em 24-48 horas.
"""

import requests
import urllib3
import random
import time
import uuid
from datetime import datetime, timedelta

# Desabilita avisos SSL (workaround para Windows)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ========================================================================
# CONFIGURAÇÃO - Suas credenciais GA4
# ========================================================================

MEASUREMENT_ID = "G-MDVLRDYZFE"  # Seu Measurement ID
API_SECRET = "E_AABYDGRHSYMNNnWyz"  # API Secret configurado

# Para gerar o API_SECRET:
# 1. Acesse: https://analytics.google.com/
# 2. Admin → Data Streams → Selecione seu stream web
# 3. Measurement Protocol API secrets → Create
# 4. Copie o secret gerado

# ========================================================================
# CONFIGURAÇÃO DOS DADOS SIMULADOS
# ========================================================================

# Cidades brasileiras para simular
CITIES = ["São Paulo", "Rio de Janeiro", "Brasília", "Belo Horizonte", "Curitiba", 
          "Porto Alegre", "Salvador", "Fortaleza", "Recife", "Manaus"]

# Páginas do site
PAGES = ["/", "/produtos", "/sobre", "/contato", "/blog", "/checkout", "/carrinho"]

# Fontes de tráfego
SOURCES = [
    {"source": "google", "medium": "organic"},
    {"source": "google", "medium": "cpc"},
    {"source": "facebook", "medium": "social"},
    {"source": "direct", "medium": "(none)"},
    {"source": "newsletter", "medium": "email"},
]

# ========================================================================
# FUNÇÕES DE SIMULAÇÃO
# ========================================================================

def send_event(client_id, event_name, params=None):
    """
    Envia um evento para o GA4 via Measurement Protocol.
    
    Args:
        client_id: ID único do cliente (simula um usuário)
        event_name: Nome do evento (ex: page_view, purchase)
        params: Parâmetros adicionais do evento
    """
    
    if API_SECRET == "YOUR_API_SECRET":
        print("⚠️  Configure o API_SECRET antes de executar!")
        print("\nPara gerar:")
        print("  1. https://analytics.google.com/")
        print("  2. Admin → Data Streams → Web stream")
        print("  3. Measurement Protocol API secrets → Create")
        return False
    
    url = f"https://www.google-analytics.com/mp/collect?measurement_id={MEASUREMENT_ID}&api_secret={API_SECRET}"
    
    payload = {
        "client_id": client_id,
        "events": [{
            "name": event_name,
            "params": params or {}
        }]
    }
    
    try:
        response = requests.post(url, json=payload, verify=False, timeout=10)
        if response.status_code == 204:
            return True
        else:
            print(f"Erro: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Erro ao enviar evento: {e}")
        return False


def simulate_user_session():
    """Simula uma sessão completa de um usuário."""
    
    # Gera ID único para o usuário
    client_id = str(uuid.uuid4())
    
    # Gera session_id único para esta sessão (timestamp em milissegundos)
    session_id = str(int(time.time() * 1000))
    
    # Escolhe atributos aleatórios
    city = random.choice(CITIES)
    traffic = random.choice(SOURCES)
    
    # 1. Page view inicial
    page = random.choice(PAGES)
    params = {
        "session_id": session_id,  # Mantém o mesmo session_id para toda a sessão
        "page_location": f"https://example.com{page}",
        "page_title": page.replace("/", "").title() or "Home",
        "engagement_time_msec": random.randint(5000, 30000),
    }
    
    print(f"  📄 {city} - {traffic['source']}/{traffic['medium']} → {page}")
    send_event(client_id, "page_view", params)
    
    # 2. Navegação adicional (50% de chance)
    if random.random() > 0.5:
        time.sleep(0.1)
        page2 = random.choice(PAGES)
        params["page_location"] = f"https://example.com{page2}"
        params["page_title"] = page2.replace("/", "").title() or "Home"
        params["engagement_time_msec"] = random.randint(5000, 30000)  # Novo tempo de engajamento
        send_event(client_id, "page_view", params)
    
    # 3. Conversão (10% de chance)
    if random.random() > 0.9:
        time.sleep(0.1)
        send_event(client_id, "purchase", {
            "session_id": session_id,  # Mesmo session_id da sessão
            "currency": "BRL",
            "value": random.uniform(50, 500),
            "transaction_id": str(uuid.uuid4())[:8],
        })
        print(f"  💰 Conversão!")
    
    time.sleep(0.1)  # Evita rate limit


def generate_test_data(num_sessions=50):
    """
    Gera dados de teste simulando múltiplas sessões.
    
    Args:
        num_sessions: Número de sessões a simular
    """
    
    print("=" * 70)
    print("GERADOR DE DADOS SIMULADOS PARA GA4")
    print("=" * 70)
    print(f"\nMeasurement ID: {MEASUREMENT_ID}")
    print(f"Sessões a simular: {num_sessions}")
    
    if API_SECRET == "YOUR_API_SECRET":
        print("\n" + "=" * 70)
        print("❌ CONFIGURE O API_SECRET PRIMEIRO!")
        print("=" * 70)
        print("\nPassos:")
        print("  1. Acesse: https://analytics.google.com/")
        print("  2. Admin → Data Streams")
        print("  3. Clique no seu web stream (G-MDVLRDYZFE)")
        print("  4. Role até 'Measurement Protocol API secrets'")
        print("  5. Clique em 'Create'")
        print("  6. Dê um nome: 'test-data-generator'")
        print("  7. Copie o 'Secret value'")
        print("  8. Cole no topo deste arquivo na variável API_SECRET")
        print("\nDepois execute novamente:")
        print("  python scripts/gerar_dados_teste.py")
        return
    
    print("\n🚀 Iniciando simulação...\n")
    
    success_count = 0
    for i in range(num_sessions):
        print(f"[{i+1}/{num_sessions}]", end=" ")
        
        if simulate_user_session():
            success_count += 1
    
    print("\n" + "=" * 70)
    print(f"✅ SIMULAÇÃO CONCLUÍDA!")
    print("=" * 70)
    print(f"\nSessões simuladas: {success_count}/{num_sessions}")
    print("\n⏰ Aguarde 24-48 horas para os dados aparecerem no GA4")
    print("\n💡 Dica: Dados em tempo real podem aparecer em alguns minutos!")
    print("   Acesse: https://analytics.google.com/ → Reports → Realtime")


if __name__ == "__main__":
    # Simula 50 sessões de usuários
    generate_test_data(num_sessions=50)
