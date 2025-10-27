#!/usr/bin/env python3
"""
Script para descobrir o Property ID a partir do Measurement ID.

Usa a Google Analytics Admin API para listar propriedades.
"""

import os
import sys
from pathlib import Path

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from google.analytics.admin import AnalyticsAdminServiceClient
    from google.analytics.admin_v1beta.types import ListAccountsRequest, ListPropertiesRequest
    
    print("=" * 70)
    print("DESCOBRIR PROPERTY ID DO GA4")
    print("=" * 70)
    
    # Configura credenciais
    credentials_path = "config/credentials.json"
    if os.path.exists(credentials_path):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        print(f"\n✓ Usando credenciais: {credentials_path}")
    
    # Cria cliente
    client = AnalyticsAdminServiceClient()
    
    print("\n[1/2] Buscando contas do Google Analytics...")
    
    # Lista contas
    accounts = client.list_accounts()
    
    print("\n📋 Contas encontradas:")
    print("-" * 70)
    
    account_list = []
    for account in accounts:
        account_name = account.name
        account_display_name = account.display_name
        account_list.append((account_name, account_display_name))
        print(f"\n  Conta: {account_display_name}")
        print(f"  Nome técnico: {account_name}")
        
        # Lista propriedades desta conta
        print(f"\n  🔍 Propriedades nesta conta:")
        
        try:
            properties = client.list_properties(parent=account_name)
            
            for prop in properties:
                property_id = prop.name.split('/')[-1]
                property_name = prop.display_name
                
                # Tenta pegar o Measurement ID
                try:
                    # Lista data streams para pegar o Measurement ID
                    streams = client.list_data_streams(parent=prop.name)
                    for stream in streams:
                        if hasattr(stream, 'web_stream_data'):
                            measurement_id = stream.web_stream_data.measurement_id
                            
                            print(f"\n    ✓ Propriedade: {property_name}")
                            print(f"      Property ID: {property_id}")
                            print(f"      Measurement ID: {measurement_id}")
                            
                            if measurement_id == "G-MDVLRDYZFE":
                                print("\n" + "=" * 70)
                                print("🎯 ENCONTRADO! Esta é sua propriedade:")
                                print("=" * 70)
                                print(f"\n  Property ID: {property_id}")
                                print(f"  Measurement ID: {measurement_id}")
                                print(f"  Nome: {property_name}")
                                print("\n💡 Use este Property ID no seu script de coleta!")
                                
                except Exception as e:
                    print(f"      Property ID: {property_id}")
                    print(f"      Nome: {property_name}")
                    
        except Exception as e:
            print(f"    ⚠️  Erro ao listar propriedades: {e}")
    
    if not account_list:
        print("\n⚠️  Nenhuma conta encontrada.")
        print("\nIsso pode significar que:")
        print("  1. A Service Account ainda não tem acesso às contas GA4")
        print("  2. Você precisa adicionar a Service Account no Google Analytics")
        print("\n📧 Service Account Email:")
        print("  ga4-account-test@projeto-analiseseo.iam.gserviceaccount.com")
        
except ImportError:
    print("\n❌ Biblioteca google-analytics-admin não instalada!")
    print("\nInstale com:")
    print("  pip install google-analytics-admin")
    
except Exception as e:
    print("\n" + "=" * 70)
    print("❌ ERRO")
    print("=" * 70)
    print(f"\n{str(e)}")
    
    if "403" in str(e) or "permission" in str(e).lower():
        print("\n🔧 SOLUÇÃO:")
        print("\n1. Acesse: https://analytics.google.com/")
        print("2. Selecione a propriedade com Measurement ID: G-MDVLRDYZFE")
        print("3. Admin → Property Access Management")
        print("4. Clique em '+' → Add users")
        print("5. Adicione: ga4-account-test@projeto-analiseseo.iam.gserviceaccount.com")
        print("6. Permissão: Viewer")
        print("7. Salve e aguarde alguns minutos")
