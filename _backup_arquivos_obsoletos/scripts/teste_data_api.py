#!/usr/bin/env python3
"""
Verifica acesso usando Data API (não precisa Admin API)
"""

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Metric
from google.oauth2 import service_account

CREDENTIALS_FILE = "config/credentials.json"
PROPERTY_ID = "509656370"

print("=" * 70)
print("TESTE DE ACESSO - DATA API (sem Admin API)")
print("=" * 70)

try:
    # Carrega credenciais
    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=['https://www.googleapis.com/auth/analytics.readonly']
    )
    
    print(f"\n✅ Credenciais carregadas")
    print(f"   Service Account: {credentials.service_account_email}")
    
    # Cliente Data API
    client = BetaAnalyticsDataClient(credentials=credentials)
    
    print(f"\n🔍 Testando acesso à propriedade {PROPERTY_ID}...")
    
    # Tenta fazer uma consulta simples
    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        date_ranges=[DateRange(start_date="yesterday", end_date="today")],
        metrics=[Metric(name="activeUsers")]
    )
    
    response = client.run_report(request)
    
    print(f"\n✅ ACESSO CONCEDIDO!")
    print(f"   Property ID: {PROPERTY_ID}")
    print(f"   Service Account tem permissão de leitura!")
    
    if response.row_count > 0:
        print(f"   Dados encontrados: {response.row_count} linhas")
    else:
        print(f"   Sem dados (normal para propriedade nova)")
    
    print("\n" + "=" * 70)
    print("✅ SERVICE ACCOUNT ESTÁ FUNCIONANDO!")
    print("=" * 70)
    print("\n💡 Measurement Protocol é diferente:")
    print("   - Measurement Protocol usa API_SECRET (não Service Account)")
    print("   - Service Account é apenas para COLETAR dados")
    print("   - Os eventos estão sendo enviados corretamente (status 204)")
    
    print("\n🔍 PROBLEMA DO DEBUGVIEW:")
    print("   Pode ser configuração do Data Stream no GA4")
    print("   Vamos verificar o Measurement ID...")
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    
    if "403" in str(e):
        print("\n" + "=" * 70)
        print("⚠️ Service Account SEM PERMISSÃO na propriedade!")
        print("=" * 70)
        print("\nSOLUÇÃO:")
        print("1. Acesse: https://analytics.google.com/")
        print("2. Selecione a propriedade correta (canto superior esquerdo)")
        print("3. Admin (rodinha) → Property Access Management")
        print("4. Clique '+' (Add users)")
        print("5. Email: ga4-account-test@projeto-analiseseo.iam.gserviceaccount.com")
        print("6. Role: Viewer")
        print("7. Clique 'Add'")
    else:
        print(f"\n❌ Erro inesperado: {e}")
