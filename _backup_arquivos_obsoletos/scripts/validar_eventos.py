#!/usr/bin/env python3
"""
Validar eventos do Measurement Protocol.

Este script valida a estrutura dos eventos antes de enviá-los em produção.
"""

import requests
import urllib3
import uuid

# Desabilita avisos SSL (workaround para Windows)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ========================================================================
# CONFIGURAÇÃO
# ========================================================================

MEASUREMENT_ID = "G-MDVLRDYZFE"
API_SECRET = "E_AABYDGRHSYMNNnWyz"

# ========================================================================
# FUNÇÃO DE VALIDAÇÃO
# ========================================================================

def validate_event():
    """
    Envia um evento para o endpoint de validação do Measurement Protocol.
    Retorna se o evento é válido ou não.
    
    Ref: https://developers.google.com/analytics/devguides/collection/protocol/ga4/validating-events
    """
    
    # URL de validação com validation_behavior para validação rigorosa
    url = (
        f"https://www.google-analytics.com/debug/mp/collect"
        f"?measurement_id={MEASUREMENT_ID}"
        f"&api_secret={API_SECRET}"
        f"&validation_behavior=ENFORCE_RECOMMENDATIONS"
    )
    
    client_id = str(uuid.uuid4())
    
    payload = {
        "client_id": client_id,
        "events": [{
            "name": "page_view",
            "params": {
                "page_location": "https://example.com/",
                "page_title": "Home",
                "engagement_time_msec": 10000,
            }
        }]
    }
    
    print("=" * 70)
    print("VALIDAÇÃO DE EVENTOS - MEASUREMENT PROTOCOL")
    print("=" * 70)
    print(f"\nMeasurement ID: {MEASUREMENT_ID}")
    print(f"Client ID: {client_id}")
    
    print("\n🔄 Validando estrutura do evento...")
    
    try:
        response = requests.post(url, json=payload, verify=False, timeout=10)
        
        print(f"\n✓ Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print("\n📋 Resposta do GA4:")
            print("-" * 70)
            
            if "validationMessages" in result:
                messages = result["validationMessages"]
                
                if not messages:
                    print("✅ SUCESSO! Evento válido!")
                    print("\n💡 Estrutura correta:")
                    print("   • API Secret válido")
                    print("   • Measurement ID válido")
                    print("   • Formato do evento correto")
                    print("\n⏰ Eventos enviados aparecem nos relatórios em 24-48h")
                    return True
                else:
                    print("⚠️ AVISOS/ERROS encontrados:")
                    for i, msg in enumerate(messages, 1):
                        print(f"\n{i}. {msg.get('description', 'Sem descrição')}")
                        print(f"   Tipo: {msg.get('validationCode', 'N/A')}")
                    return False
            else:
                print("⚠️ Resposta sem mensagens de validação")
                print(f"Resposta completa: {result}")
                return False
        else:
            print(f"\n❌ Erro HTTP: {response.status_code}")
            print(f"Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        return False


if __name__ == "__main__":
    valid = validate_event()
    
    if valid:
        print("\n" + "=" * 70)
        print("🎯 PRÓXIMOS PASSOS")
        print("=" * 70)
        
        print("\n🔄 Para gerar eventos de teste:")
        print("   python scripts/gerar_dados_teste.py")
        
        print("\n📊 Para coletar dados do GA4:")
        print("   python scripts/exemplo_coleta_ga4.py")
        print("   (Aguarde 24-48h após enviar eventos)")
    else:
        print("\n" + "=" * 70)
        print("🔧 CORREÇÕES NECESSÁRIAS")
        print("=" * 70)
        print("\nVerifique:")
        print("  1. API Secret está correto?")
        print("  2. Measurement ID está correto?")
        print("  3. Propriedade GA4 está ativa?")
