#!/usr/bin/env python3
"""
Teste rápido: Verificar acesso ao GA4 com sua propriedade.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.analytics.data_v1beta.types import (
        DateRange,
        Dimension,
        Metric,
        RunReportRequest,
    )
    
    print("=" * 70)
    print("TESTE: Acesso à sua Propriedade GA4")
    print("=" * 70)
    
    PROPERTY_ID = "509656370"
    CREDENTIALS_PATH = "config/credentials.json"
    
    print(f"\n✓ Property ID: {PROPERTY_ID}")
    print(f"✓ Measurement ID: G-MDVLRDYZFE")
    print(f"✓ Credentials: {CREDENTIALS_PATH}")
    
    # Configura credenciais
    if os.path.exists(CREDENTIALS_PATH):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDENTIALS_PATH
    
    print("\n[1/3] Criando cliente...")
    client = BetaAnalyticsDataClient()
    print("  ✓ Cliente criado com sucesso!")
    
    print("\n[2/3] Testando query básica (últimos 7 dias)...")
    
    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        dimensions=[Dimension(name="date")],
        metrics=[Metric(name="activeUsers")],
        date_ranges=[DateRange(start_date="7daysAgo", end_date="yesterday")],
        limit=10,
    )
    
    response = client.run_report(request)
    
    print(f"\n  ✓ Query executada com sucesso!")
    print(f"  Total de linhas: {response.row_count}")
    
    print("\n[3/3] Resultados:")
    print("-" * 70)
    
    if response.row_count > 0:
        print("\n📊 Usuários ativos por dia (últimos 7 dias):")
        for row in response.rows:
            date = row.dimension_values[0].value
            users = row.metric_values[0].value
            print(f"  {date}: {users} usuários ativos")
    else:
        print("\n⚠️  Nenhum dado encontrado ainda.")
        print("\nIsso é normal se:")
        print("  • A propriedade foi criada recentemente")
        print("  • O código de rastreamento ainda não foi instalado no site")
        print("  • O site ainda não recebeu visitas")
        print("\n💡 Para gerar dados de teste:")
        print("  1. Adicione o código gtag.js ao seu site")
        print("  2. Visite algumas páginas do site")
        print("  3. Aguarde 24-48h para os dados aparecerem")
    
    print("\n" + "=" * 70)
    print("✅ SUCESSO! Conexão funcionando perfeitamente!")
    print("=" * 70)
    print("\n🎯 Próximos passos:")
    print("  1. Execute: python scripts/exemplo_coleta_ga4.py")
    print("  2. Os dados serão salvos em: data/raw/")
    print("  3. E armazenados no banco: data/processed/ga4_data.duckdb")
    
except Exception as e:
    print("\n" + "=" * 70)
    print("❌ ERRO")
    print("=" * 70)
    print(f"\n{str(e)}\n")
    
    if "403" in str(e) or "permission" in str(e).lower():
        print("🔧 SOLUÇÃO - Adicione a Service Account:")
        print("\n1. Acesse: https://analytics.google.com/")
        print("2. Selecione a propriedade com ID: 509656370")
        print("3. Admin → Property Access Management")
        print("4. '+' → Add users")
        print("5. Email: ga4-account-test@projeto-analiseseo.iam.gserviceaccount.com")
        print("6. Permissão: Viewer")
        print("7. Aguarde 2-3 minutos e tente novamente")
    
    sys.exit(1)
