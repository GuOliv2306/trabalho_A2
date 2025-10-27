#!/usr/bin/env python3
"""
Script configurável: Coleta de dados do Google Analytics 4.

Configure seu PROPERTY_ID abaixo e execute.
"""

import os
import sys
from pathlib import Path

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.collectors.ga_orchestrator import GA4Orchestrator

def main():
    print("=" * 70)
    print("COLETA DE DADOS DO GOOGLE ANALYTICS 4")
    print("=" * 70)
    
    # ========================================================================
    # CONFIGURAÇÃO - EDITE AQUI!
    # ========================================================================
    
    # OPÇÃO 1: Use sua própria propriedade GA4
    # Substitua pelo ID da SUA propriedade (ex: "123456789")
    YOUR_PROPERTY_ID = "509656370"  # ← Property ID configurado
    
    # Caminho para credenciais (já configurado)
    CREDENTIALS_PATH = "config/credentials.json"
    
    # ========================================================================
    
    if not os.path.exists(CREDENTIALS_PATH):
        print(f"\n❌ Arquivo de credenciais não encontrado: {CREDENTIALS_PATH}")
        return 1
    
    print(f"\n✓ Property ID: {YOUR_PROPERTY_ID}")
    print(f"✓ Credentials: {CREDENTIALS_PATH}")
    print(f"✓ Service Account: ga4-account-test@projeto-analiseseo.iam.gserviceaccount.com")
    
    print("\n" + "=" * 70)
    print("IMPORTANTE: Adicione a Service Account ao Google Analytics!")
    print("=" * 70)
    print("\n1. Acesse: https://analytics.google.com/")
    print("2. Admin → Property Access Management")
    print("3. Adicione: ga4-account-test@projeto-analiseseo.iam.gserviceaccount.com")
    print("4. Permissão: Viewer")
    print("\nPressione Enter para continuar após adicionar a permissão...")
    input()
    
    # ========================================================================
    # INICIALIZAÇÃO
    # ========================================================================
    print("\n[1/3] Inicializando orchestrator...")
    
    orchestrator = GA4Orchestrator(
        property_id=YOUR_PROPERTY_ID,
        credentials_path=CREDENTIALS_PATH,
        output_dir="data/raw",
    )
    print("  ✓ Orchestrator inicializado")
    
    # ========================================================================
    # COLETA DE DADOS
    # ========================================================================
    print("\n[2/3] Coletando dados do GA4...")
    print("  Período: últimos 7 dias")
    print("  Reports: traffic, conversions, engagement")
    
    try:
        saved_files = orchestrator.collect_and_save(
            report_types=["traffic", "conversions", "engagement"],
            start_date="7daysAgo",
            end_date="yesterday",
            include_realtime=False,
        )
        
        print(f"\n  ✓ {len(saved_files)} arquivos JSON salvos!")
        
        for report_type, filepath in saved_files.items():
            print(f"    - {report_type}: {filepath}")
        
        # ====================================================================
        # ARMAZENAMENTO EM BANCO
        # ====================================================================
        print("\n[3/3] Armazenando dados no banco DuckDB...")
        
        from src.collectors.db_storage import GA4DatabaseStorage
        
        db = GA4DatabaseStorage(db_path="data/processed/ga4_data.duckdb")
        
        total_inserted = 0
        for report_type, filepath in saved_files.items():
            print(f"\n  Processando: {report_type}")
            count = db.insert_from_json(filepath)
            total_inserted += count
        
        print(f"\n  ✓ Total: {total_inserted} linhas inseridas no banco")
        
        print("\n" + "=" * 70)
        print("✅ SUCESSO! Coleta finalizada com sucesso!")
        print("=" * 70)
        print(f"\nArquivos salvos em: data/raw/")
        print(f"Banco de dados: data/processed/ga4_data.duckdb")
        
        return 0
        
    except Exception as e:
        print("\n" + "=" * 70)
        print("❌ ERRO durante a coleta")
        print("=" * 70)
        print(f"\n{str(e)}")
        
        if "403" in str(e):
            print("\n🔧 SOLUÇÃO:")
            print("  1. Verifique se adicionou a Service Account no Google Analytics")
            print("  2. Email: ga4-account-test@projeto-analiseseo.iam.gserviceaccount.com")
            print("  3. Permissão: Viewer")
            print("  4. Aguarde alguns minutos para as permissões propagarem")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())
