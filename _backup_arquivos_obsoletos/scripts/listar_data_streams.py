#!/usr/bin/env python3
"""
Lista todos os Data Streams da propriedade para verificar o Measurement ID correto
"""

from google.analytics.admin import AnalyticsAdminServiceClient
from google.oauth2 import service_account

CREDENTIALS_FILE = "config/credentials.json"
PROPERTY_ID = "509656370"

print("=" * 70)
print("VERIFICANDO DATA STREAMS DA PROPRIEDADE")
print("=" * 70)

try:
    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=['https://www.googleapis.com/auth/analytics.readonly']
    )
    
    client = AnalyticsAdminServiceClient(credentials=credentials)
    
    print(f"\n📊 Propriedade: {PROPERTY_ID} (website teste)")
    print(f"\n🔍 Buscando Data Streams...\n")
    
    # Lista todos os data streams
    parent = f"properties/{PROPERTY_ID}"
    streams = client.list_data_streams(parent=parent)
    
    stream_count = 0
    for stream in streams:
        stream_count += 1
        print(f"{'='*70}")
        print(f"Stream #{stream_count}")
        print(f"{'='*70}")
        print(f"Nome: {stream.display_name}")
        print(f"Tipo: {stream.type_.name}")
        print(f"Stream ID: {stream.name.split('/')[-1]}")
        
        # Se for Web Stream, mostra Measurement ID
        if stream.type_.name == "WEB_DATA_STREAM":
            print(f"🎯 Measurement ID: {stream.web_stream_data.measurement_id}")
            print(f"   URL: {stream.web_stream_data.default_uri}")
            
            # Verifica se é o mesmo que estamos usando
            if stream.web_stream_data.measurement_id == "G-MDVLRDYZFE":
                print(f"   ✅ CORRETO! Estamos usando este Measurement ID")
            else:
                print(f"   ⚠️ DIFERENTE! Estamos usando: G-MDVLRDYZFE")
        
        print()
    
    if stream_count == 0:
        print("❌ Nenhum Data Stream encontrado!")
        print("\n⚠️ PROBLEMA: Propriedade sem Data Streams!")
        print("\nSOLUÇÃO:")
        print("1. Acesse: https://analytics.google.com/")
        print("2. Admin → Data Streams")
        print("3. Adicione um Web Stream")
    else:
        print(f"\n✅ Total de streams encontrados: {stream_count}")
        
        print("\n" + "=" * 70)
        print("💡 PRÓXIMO PASSO:")
        print("=" * 70)
        print("\n1. Confirme o Measurement ID acima")
        print("2. Se estiver DIFERENTE de G-MDVLRDYZFE, me avise!")
        print("3. Se estiver CORRETO, o problema pode ser:")
        print("   - DebugView demora alguns segundos")
        print("   - Stream precisa ser reativado")
        print("   - Filtros no DebugView")
        
except Exception as e:
    print(f"\n❌ Erro: {e}")
