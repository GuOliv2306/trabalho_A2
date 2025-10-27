#!/usr/bin/env python3
"""
Script de exemplo: Coleta completa de dados do Google Search Console.

Demonstra o fluxo completo de coleta, armazenamento em JSON e inserção em banco.

Uso:
    python scripts/exemplo_coleta_gsc.py
"""

import os
import sys
from pathlib import Path

# Adiciona src ao path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.collectors.gsc_orchestrator import GSCOrchestrator
from src.collectors.db_storage import GA4DatabaseStorage


def main():
    """Executa exemplo de coleta GSC."""
    print("=" * 70)
    print("EXEMPLO: Coleta de Dados do Google Search Console")
    print("=" * 70)

    # ========================================================================
    # 1. CONFIGURAÇÃO
    # ========================================================================
    print("\n[1/5] Configurando credenciais...")
    
    # Substitua pelos seus valores
    SITE_URL = os.getenv("GSC_SITE_URL", "https://www.example.com/")
    CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "path/to/credentials.json")

    if SITE_URL == "https://www.example.com/":
        print("⚠️  ATENÇÃO: Configure GSC_SITE_URL antes de executar!")
        print("\nDefina variáveis de ambiente:")
        print("  export GSC_SITE_URL='https://seusite.com/'")
        print("  export GOOGLE_APPLICATION_CREDENTIALS='/path/to/credentials.json'")
        print("\nOu edite este script diretamente.")
        print("\n📖 Nota: Use a mesma Service Account do GA4 (já tem acesso ao GSC)")
        return

    print(f"  Site URL: {SITE_URL}")
    print(f"  Credentials: {CREDENTIALS_PATH}")

    # ========================================================================
    # 2. INICIALIZAÇÃO DO ORCHESTRATOR
    # ========================================================================
    print("\n[2/5] Inicializando orchestrator...")
    
    orchestrator = GSCOrchestrator(
        site_url=SITE_URL,
        credentials_path=CREDENTIALS_PATH,
        output_dir="data/raw",
    )
    print("  ✓ Orchestrator GSC inicializado")

    # ========================================================================
    # 3. COLETA DE DADOS
    # ========================================================================
    print("\n[3/5] Coletando dados do Google Search Console...")
    print("  Período: últimos 7 dias")
    print("  Reports: queries, pages, countries, devices, dates")
    
    saved_files = orchestrator.collect_and_save(
        report_types=[
            "query_performance",
            "page_performance",
            "country_performance",
            "device_performance",
            "date_performance",
        ],
        # Datas automáticas: últimos 7 dias
        max_rows_queries=5000,
        max_rows_pages=1000,
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
    print("\n  Resumo por tabela (GSC):")
    for table, info in stats.items():
        if table.startswith("gsc_"):
            print(f"    {table}: {info['row_count']} linhas", end="")
            if "date_range" in info and info["date_range"]["min"]:
                print(f" ({info['date_range']['min']} a {info['date_range']['max']})")
            else:
                print()

    # Exemplo de queries customizadas
    print("\n  Top 10 queries por cliques:")
    top_queries = db.query("""
        SELECT 
            query,
            SUM(clicks) as total_clicks,
            SUM(impressions) as total_impressions,
            AVG(ctr) as avg_ctr,
            AVG(position) as avg_position
        FROM gsc_query_performance
        GROUP BY query
        ORDER BY total_clicks DESC
        LIMIT 10
    """)
    
    for row in top_queries:
        query, clicks, impressions, ctr, position = row
        print(f"    '{query}': {clicks} cliques, {impressions} impressões, "
              f"CTR {ctr*100:.2f}%, posição {position:.1f}")

    print("\n  Top 5 páginas por cliques:")
    top_pages = db.query("""
        SELECT 
            page,
            SUM(clicks) as total_clicks,
            AVG(position) as avg_position
        FROM gsc_page_performance
        GROUP BY page
        ORDER BY total_clicks DESC
        LIMIT 5
    """)
    
    for row in top_pages:
        page, clicks, position = row
        # Trunca URL longa
        page_short = page if len(page) <= 60 else page[:57] + "..."
        print(f"    {page_short}")
        print(f"      {clicks} cliques, posição média {position:.1f}")

    # Fecha conexão com banco
    db.close()

    # ========================================================================
    # FINALIZAÇÃO
    # ========================================================================
    print("\n" + "=" * 70)
    print("✓ COLETA GSC CONCLUÍDA COM SUCESSO!")
    print("=" * 70)
    print("\nArquivos gerados:")
    print(f"  JSONs: data/raw/gsc_*.json ({len(saved_files)} arquivos)")
    print(f"  Banco: data/processed/ga4_data.duckdb (tabelas gsc_*)")
    print("\nPróximos passos:")
    print("  1. Explore os JSONs em data/raw/")
    print("  2. Execute queries SQL no banco DuckDB")
    print("  3. Combine dados GA4 + GSC para análise completa")
    print("  4. Use src/ml/ para modelos preditivos")
    print()


def exemplo_coleta_incremental():
    """Exemplo de coleta incremental (atualização diária)."""
    print("\n" + "=" * 70)
    print("EXEMPLO: Coleta Incremental GSC (atualização diária)")
    print("=" * 70)

    SITE_URL = os.getenv("GSC_SITE_URL", "https://www.example.com/")
    CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    orchestrator = GSCOrchestrator(SITE_URL, CREDENTIALS_PATH)

    # Coleta apenas dados de ontem
    from datetime import datetime, timedelta
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    print(f"\nColetando dados de {yesterday} (incremental)...")
    filepath = orchestrator.collect_incremental(
        report_type="query_performance",
        start_date=yesterday,
        end_date=yesterday,
        max_rows=5000,
    )

    print(f"\n✓ Arquivo salvo: {filepath}")

    # Insere no banco
    db = GA4DatabaseStorage()
    count = db.insert_from_json(filepath)
    db.close()

    print(f"✓ {count} linhas inseridas/atualizadas no banco\n")


def exemplo_analise_combinada():
    """Exemplo de análise combinada GA4 + GSC."""
    print("\n" + "=" * 70)
    print("EXEMPLO: Análise Combinada GA4 + GSC")
    print("=" * 70)

    db = GA4DatabaseStorage()

    # Combina tráfego GA4 com queries GSC
    print("\n  Correlação: Tráfego orgânico (GA4) x Queries (GSC)")
    
    combined = db.query("""
        SELECT 
            g.date,
            SUM(t.sessions) as ga4_sessions,
            SUM(g.clicks) as gsc_clicks,
            AVG(g.position) as avg_position
        FROM gsc_date_performance g
        LEFT JOIN traffic t ON g.date = t.date 
            AND t.session_medium = 'organic'
        GROUP BY g.date
        ORDER BY g.date DESC
        LIMIT 7
    """)

    print("\n  Últimos 7 dias:")
    print("  Data       | Sessões GA4 | Cliques GSC | Posição Média")
    print("  " + "-" * 60)
    for row in combined:
        date, sessions, clicks, position = row
        sessions = sessions or 0
        print(f"  {date} | {sessions:11.0f} | {clicks:11.0f} | {position:13.1f}")

    db.close()


if __name__ == "__main__":
    # Executa exemplo principal
    main()

    # Descomente para executar exemplos adicionais:
    # exemplo_coleta_incremental()
    # exemplo_analise_combinada()
