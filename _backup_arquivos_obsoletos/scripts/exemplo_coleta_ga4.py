#!/usr/bin/env python3
"""
Script de exemplo: Coleta completa de dados do Google Analytics 4.

Demonstra o fluxo completo de coleta, armazenamento em JSON e inserção em banco.

Uso:
    python scripts/exemplo_coleta_ga4.py
"""

import os
import sys
from pathlib import Path

# Adiciona src ao path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.collectors.ga_orchestrator import GA4Orchestrator
from src.collectors.db_storage import GA4DatabaseStorage


def main():
    """Executa exemplo de coleta GA4."""
    print("=" * 70)
    print("EXEMPLO: Coleta de Dados do Google Analytics 4")
    print("=" * 70)

    # ========================================================================
    # 1. CONFIGURAÇÃO
    # ========================================================================
    print("\n[1/5] Configurando credenciais...")
    
    # Configuração para sua propriedade GA4
    PROPERTY_ID = os.getenv("GA4_PROPERTY_ID", "509656370")  # Sua propriedade GA4
    CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "config/credentials.json")

    if not os.path.exists(CREDENTIALS_PATH):
        print("⚠️  ATENÇÃO: Arquivo de credenciais não encontrado!")
        print(f"\nProcurando em: {CREDENTIALS_PATH}")
        print("\nVerifique se o arquivo JSON está no local correto.")
        print("Caminho esperado: config/credentials.json")
        return

    print(f"  Property ID: {PROPERTY_ID}")
    print(f"  Credentials: {CREDENTIALS_PATH}")

    # ========================================================================
    # 2. INICIALIZAÇÃO DO ORCHESTRATOR
    # ========================================================================
    print("\n[2/5] Inicializando orchestrator...")
    
    orchestrator = GA4Orchestrator(
        property_id=PROPERTY_ID,
        credentials_path=CREDENTIALS_PATH,
        output_dir="data/raw",
    )
    print("  ✓ Orchestrator inicializado")

    # ========================================================================
    # 3. COLETA DE DADOS
    # ========================================================================
    print("\n[3/5] Coletando dados do GA4...")
    print("  Período: últimos 7 dias")
    print("  Reports: traffic, conversions, engagement")
    
    saved_files = orchestrator.collect_and_save(
        report_types=["traffic", "conversions", "engagement"],
        start_date="7daysAgo",
        end_date="yesterday",
        include_realtime=False,
    )

    print(f"\n  ✓ {len(saved_files)} arquivos JSON salvos em data/raw/")

    # ========================================================================
    # 4. ARMAZENAMENTO EM BANCO
    # ========================================================================
    print("\n[4/5] Armazenando dados no banco DuckDB...")
    
    db = GA4DatabaseStorage(db_path="data/processed/ga4_data.duckdb")
    
    total_inserted = 0
    for report_type, filepath in saved_files.items():
        print(f"\n  Processando: {report_type}")
        count = db.insert_from_json(filepath)
        total_inserted += count

    print(f"\n  ✓ Total: {total_inserted} linhas inseridas no banco")

    # ========================================================================
    # 5. ESTATÍSTICAS E QUERIES DE EXEMPLO
    # ========================================================================
    print("\n[5/5] Estatísticas do banco de dados...")
    
    stats = db.get_summary_stats()
    print("\n  Resumo por tabela:")
    for table, info in stats.items():
        print(f"    {table}: {info['row_count']} linhas", end="")
        if "date_range" in info and info["date_range"]["min"]:
            print(f" ({info['date_range']['min']} a {info['date_range']['max']})")
        else:
            print()

    # Exemplo de query customizada
    print("\n  Top 5 fontes de tráfego (últimos 7 dias):")
    top_sources = db.query("""
        SELECT 
            session_source,
            SUM(sessions) as total_sessions,
            SUM(active_users) as total_users
        FROM traffic
        GROUP BY session_source
        ORDER BY total_sessions DESC
        LIMIT 5
    """)
    
    for row in top_sources:
        source, sessions, users = row
        print(f"    {source}: {sessions} sessões, {users} usuários")

    # Fecha conexão com banco
    db.close()

    # ========================================================================
    # FINALIZAÇÃO
    # ========================================================================
    print("\n" + "=" * 70)
    print("✓ COLETA CONCLUÍDA COM SUCESSO!")
    print("=" * 70)
    print("\nArquivos gerados:")
    print(f"  JSONs: data/raw/ga4_*.json ({len(saved_files)} arquivos)")
    print(f"  Banco: data/processed/ga4_data.duckdb")
    print("\nPróximos passos:")
    print("  1. Explore os JSONs em data/raw/")
    print("  2. Execute queries SQL no banco DuckDB")
    print("  3. Use src/cleaning/ para processar dados")
    print("  4. Implemente modelos ML em src/ml/")
    print()


def exemplo_coleta_incremental():
    """Exemplo de coleta incremental (atualização diária)."""
    print("\n" + "=" * 70)
    print("EXEMPLO: Coleta Incremental (atualização diária)")
    print("=" * 70)

    PROPERTY_ID = os.getenv("GA4_PROPERTY_ID", "YOUR_GA4_PROPERTY_ID")
    CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    orchestrator = GA4Orchestrator(PROPERTY_ID, CREDENTIALS_PATH)

    # Coleta apenas dados de ontem
    print("\nColetando dados de ontem (incremental)...")
    filepath = orchestrator.collect_incremental(
        report_type="traffic",
        start_date="yesterday",
        end_date="yesterday",
    )

    print(f"\n✓ Arquivo salvo: {filepath}")

    # Insere no banco
    db = GA4DatabaseStorage()
    count = db.insert_from_json(filepath)
    db.close()

    print(f"✓ {count} linhas inseridas/atualizadas no banco\n")


def exemplo_listagem_reports():
    """Exemplo de listagem de reports coletados."""
    print("\n" + "=" * 70)
    print("EXEMPLO: Listar Reports Coletados")
    print("=" * 70)

    PROPERTY_ID = os.getenv("GA4_PROPERTY_ID", "YOUR_GA4_PROPERTY_ID")
    orchestrator = GA4Orchestrator(PROPERTY_ID)

    reports = orchestrator.list_collected_reports()

    print(f"\nTotal de reports salvos: {len(reports)}\n")
    
    for i, report in enumerate(reports[:10], 1):  # Mostra até 10 mais recentes
        size_kb = report["size_bytes"] / 1024
        print(f"{i}. {report['filename']}")
        print(f"   Tamanho: {size_kb:.1f} KB | Modificado: {report['modified']}")


if __name__ == "__main__":
    # Executa exemplo principal
    main()

    # Descomente para executar exemplos adicionais:
    # exemplo_coleta_incremental()
    # exemplo_listagem_reports()
