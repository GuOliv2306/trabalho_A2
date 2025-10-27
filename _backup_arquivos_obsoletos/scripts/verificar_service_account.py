#!/usr/bin/env python3
"""
Verifica se o Service Account tem acesso à propriedade
"""

from google.analytics.admin import AnalyticsAdminServiceClient
from google.oauth2 import service_account

CREDENTIALS_FILE = "config/credentials.json"
PROPERTY_ID = "509656370"

print("=" * 70)
print("VERIFICAÇÃO DE PERMISSÕES - SERVICE ACCOUNT")
print("=" * 70)

try:
    # Carrega credenciais
    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=['https://www.googleapis.com/auth/analytics.readonly']
    )
    
    print(f"\n✅ Credenciais carregadas")
    print(f"   Service Account: {credentials.service_account_email}")
    
    # Tenta acessar a propriedade
    client = AnalyticsAdminServiceClient(credentials=credentials)
    property_name = f"properties/{PROPERTY_ID}"
    
    print(f"\n🔍 Verificando acesso à propriedade {PROPERTY_ID}...")
    
    try:
        property_info = client.get_property(name=property_name)
        print(f"\n✅ ACESSO CONCEDIDO!")
        print(f"   Nome: {property_info.display_name}")
        print(f"   Property ID: {PROPERTY_ID}")
        print(f"   Timezone: {property_info.time_zone}")
        print(f"   Currency: {property_info.currency_code}")
        
        print("\n" + "=" * 70)
        print("✅ Service Account está configurado corretamente!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ ACESSO NEGADO!")
        print(f"   Erro: {e}")
        print("\n" + "=" * 70)
        print("⚠️ PROBLEMA: Service Account não tem permissão!")
        print("=" * 70)
        print("\nSOLUÇÃO:")
        print("1. Acesse: https://analytics.google.com/")
        print("2. Admin → Property Access Management")
        print("3. Adicione: ga4-account-test@projeto-analiseseo.iam.gserviceaccount.com")
        print("4. Função: Viewer")
        
except FileNotFoundError:
    print(f"\n❌ Arquivo não encontrado: {CREDENTIALS_FILE}")
except Exception as e:
    print(f"\n❌ Erro: {e}")
