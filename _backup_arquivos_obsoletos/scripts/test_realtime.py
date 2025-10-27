#!/usr/bin/env python3
"""
Teste: Coletar dados em tempo real do GA4.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    Dimension,
    Metric,
    RunRealtimeReportRequest,
)

PROPERTY_ID = "509656370"
CREDENTIALS_PATH = "config/credentials.json"

print("=" * 70)
print("TESTE: Dados em Tempo Real")
print("=" * 70)

if os.path.exists(CREDENTIALS_PATH):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDENTIALS_PATH

client = BetaAnalyticsDataClient()

print("\n🔄 Coletando dados em tempo real...")

request = RunRealtimeReportRequest(
    property=f"properties/{PROPERTY_ID}",
    dimensions=[
        Dimension(name="city"),
    ],
    metrics=[Metric(name="activeUsers")],
)

response = client.run_realtime_report(request)

print(f"\n✓ Total de linhas: {response.row_count}")

if response.row_count > 0:
    print("\n📊 Usuários ativos AGORA:")
    print("-" * 70)
    for row in response.rows[:20]:  # Mostra até 20
        city = row.dimension_values[0].value
        source = row.dimension_values[1].value
        users = row.metric_values[0].value
        print(f"  {city} ({source}): {users} usuário(s)")
    
    print("\n🎉 SUCESSO! Dados em tempo real funcionando!")
else:
    print("\n⚠️  Nenhum usuário ativo no momento.")
    print("   Execute o script gerar_dados_teste.py novamente!")

print("\n💡 Próximo: Aguardar 24-48h e executar coleta completa")
print("   python scripts/exemplo_coleta_ga4.py")
