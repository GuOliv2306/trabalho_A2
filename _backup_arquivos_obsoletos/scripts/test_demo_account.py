#!/usr/bin/env python3
"""
Script de teste: Verifica acesso à conta DEMO do Google Analytics 4.

Testa se consegue acessar a conta demo (54516992) sem credenciais.
"""

import sys
from pathlib import Path

# Adiciona src ao path
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
    print("TESTE: Acesso à Conta DEMO do Google Analytics 4")
    print("=" * 70)
    print("\nProperty ID: 54516992 (Conta Demo Pública do Google)")
    print("\n[1/2] Configurando credenciais...")
    
    # Configura caminho das credenciais
    import os
    credentials_path = "config/credentials.json"
    
    if os.path.exists(credentials_path):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        print(f"✓ Credenciais encontradas: {credentials_path}")
    else:
        print(f"⚠️  Credenciais não encontradas em: {credentials_path}")
    
    # Cria cliente
    client = BetaAnalyticsDataClient()
    
    print("✓ Cliente criado com sucesso!")
    
    print("\n[2/2] Executando query de teste (últimos 7 dias)...")
    
    request = RunReportRequest(
        property="properties/54516992",
        dimensions=[Dimension(name="city")],
        metrics=[Metric(name="activeUsers")],
        date_ranges=[DateRange(start_date="7daysAgo", end_date="yesterday")],
        limit=10,  # Apenas 10 resultados para teste
    )
    
    response = client.run_report(request)
    
    print(f"\n✓ Query executada com sucesso!")
    print(f"   Total de linhas: {response.row_count}")
    
    if response.row_count > 0:
        print("\n📊 Primeiras 10 cidades com mais usuários ativos:")
        print("-" * 50)
        for i, row in enumerate(response.rows[:10], 1):
            city = row.dimension_values[0].value
            users = row.metric_values[0].value
            print(f"   {i}. {city}: {users} usuários")
    
    print("\n" + "=" * 70)
    print("✅ SUCESSO! Você tem acesso à conta demo do GA4!")
    print("=" * 70)
    print("\n💡 Próximos passos:")
    print("   1. Execute: python scripts/exemplo_coleta_ga4.py")
    print("   2. Configure PROPERTY_ID='54516992' no script")
    print("   3. Os dados serão salvos em data/raw/")
    
except Exception as e:
    print("\n" + "=" * 70)
    print("❌ ERRO: Não foi possível acessar a conta demo")
    print("=" * 70)
    print(f"\nDetalhes do erro:\n{str(e)}\n")
    
    print("🔧 SOLUÇÃO: Você precisa de credenciais!")
    print("\nEscolha uma opção:\n")
    
    print("OPÇÃO 1 - Service Account (Recomendado):")
    print("  1. Acesse: https://console.cloud.google.com/")
    print("  2. Crie/selecione um projeto")
    print("  3. Ative: 'Google Analytics Data API'")
    print("  4. IAM & Admin → Service Accounts → Create")
    print("  5. Baixe o arquivo JSON de credenciais")
    print("  6. Configure: export GOOGLE_APPLICATION_CREDENTIALS='credentials.json'")
    
    print("\nOPÇÃO 2 - Usar suas próprias credenciais do Google:")
    print("  1. Faça login no Google Analytics")
    print("  2. Adicione a propriedade 54516992 à sua conta")
    print("  3. Use OAuth 2.0 (mais complexo)")
    
    print("\n📚 Documentação:")
    print("   https://developers.google.com/analytics/devguides/reporting/data/v1/quickstart-client-libraries")
    
    sys.exit(1)
