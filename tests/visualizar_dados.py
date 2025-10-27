#!/usr/bin/env python3
"""
Script para visualizar os dados gerados pelo simulador no banco DuckDB.
"""

import duckdb
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "data" / "processed" / "ga4_data.duckdb"

def print_header(title: str):
    """Imprime um cabeçalho formatado."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print('='*70)

def show_table_info(conn: duckdb.DuckDBPyConnection):
    """Mostra informações gerais de todas as tabelas."""
    print_header("📊 RESUMO DO BANCO DE DADOS")
    
    tables = [
        "traffic",
        "conversions", 
        "engagement",
        "gsc_query_performance",
        "gsc_page_performance",
        "gsc_country_performance",
        "gsc_device_performance",
        "gsc_date_performance"
    ]
    
    print(f"\n{'Tabela':<30} {'Registros':>15} {'Período':>25}")
    print('-'*70)
    
    for table in tables:
        try:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            
            # Tenta pegar o período de datas
            if table.startswith("gsc_"):
                if table == "gsc_date_performance":
                    date_col = "date"
                elif table in ["gsc_query_performance", "gsc_page_performance", 
                              "gsc_country_performance", "gsc_device_performance"]:
                    date_col = "start_date"
                else:
                    date_col = None
            else:
                date_col = "date"
            
            if date_col:
                dates = conn.execute(
                    f"SELECT MIN({date_col}), MAX({date_col}) FROM {table}"
                ).fetchone()
                period = f"{dates[0]} a {dates[1]}"
            else:
                period = "N/A"
                
            print(f"{table:<30} {count:>15,} {period:>25}")
        except Exception as e:
            print(f"{table:<30} {'ERRO':>15} {str(e)[:25]:>25}")
    
    total = sum(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in tables)
    print('-'*70)
    print(f"{'TOTAL':<30} {total:>15,}")

def show_traffic_sample(conn: duckdb.DuckDBPyConnection, limit: int = 10):
    """Mostra amostra de dados de tráfego."""
    print_header("🚗 AMOSTRA: Traffic (GA4)")
    
    df = conn.execute(f"""
        SELECT 
            date,
            session_source,
            session_medium,
            sessions,
            active_users,
            new_users,
            screen_page_views,
            ROUND(average_session_duration, 2) as avg_duration
        FROM traffic 
        ORDER BY date DESC, sessions DESC
        LIMIT {limit}
    """).df()
    
    print(df.to_string(index=False))

def show_conversions_summary(conn: duckdb.DuckDBPyConnection):
    """Mostra resumo de conversões por evento."""
    print_header("💰 RESUMO: Conversões por Evento")
    
    df = conn.execute("""
        SELECT 
            event_name,
            COUNT(*) as registros,
            SUM(key_events) as total_conversoes,
            SUM(event_count) as total_eventos,
            ROUND(SUM(total_revenue), 2) as receita_total,
            SUM(transactions) as transacoes
        FROM conversions 
        GROUP BY event_name
        ORDER BY total_conversoes DESC
    """).df()
    
    print(df.to_string(index=False))

def show_gsc_queries(conn: duckdb.DuckDBPyConnection, limit: int = 15):
    """Mostra queries do Search Console."""
    print_header("🔍 TOP QUERIES: Google Search Console")
    
    df = conn.execute(f"""
        SELECT 
            query,
            clicks,
            impressions,
            ROUND(ctr * 100, 2) as ctr_percent,
            ROUND(position, 1) as pos_avg
        FROM gsc_query_performance 
        ORDER BY impressions DESC
        LIMIT {limit}
    """).df()
    
    print(df.to_string(index=False))

def show_engagement_by_page(conn: duckdb.DuckDBPyConnection):
    """Mostra engajamento por página."""
    print_header("📱 ENGAJAMENTO: Por Página")
    
    df = conn.execute("""
        SELECT 
            page_path,
            COUNT(*) as registros,
            ROUND(AVG(engagement_rate) * 100, 1) as eng_rate_avg,
            SUM(engaged_sessions) as total_engaged,
            ROUND(AVG(average_session_duration), 1) as avg_duration
        FROM engagement 
        GROUP BY page_path
        ORDER BY total_engaged DESC
    """).df()
    
    print(df.to_string(index=False))

def show_traffic_sources_summary(conn: duckdb.DuckDBPyConnection):
    """Mostra resumo por fonte de tráfego."""
    print_header("📊 TRÁFEGO: Por Fonte/Médio")
    
    df = conn.execute("""
        SELECT 
            session_source,
            session_medium,
            COUNT(*) as registros,
            SUM(sessions) as total_sessions,
            SUM(active_users) as total_users,
            SUM(new_users) as total_new_users,
            ROUND(AVG(average_session_duration), 1) as avg_duration
        FROM traffic 
        GROUP BY session_source, session_medium
        ORDER BY total_sessions DESC
    """).df()
    
    print(df.to_string(index=False))

def show_gsc_devices(conn: duckdb.DuckDBPyConnection):
    """Mostra performance por dispositivo."""
    print_header("📱 GSC: Performance por Dispositivo")
    
    df = conn.execute("""
        SELECT 
            device,
            clicks,
            impressions,
            ROUND(ctr * 100, 2) as ctr_percent,
            ROUND(position, 1) as pos_avg
        FROM gsc_device_performance 
        ORDER BY clicks DESC
    """).df()
    
    print(df.to_string(index=False))

def show_daily_trend(conn: duckdb.DuckDBPyConnection):
    """Mostra tendência diária do GSC."""
    print_header("📈 SÉRIE TEMPORAL: Últimos 10 dias (GSC)")
    
    df = conn.execute("""
        SELECT 
            date,
            clicks,
            impressions,
            ROUND(ctr * 100, 2) as ctr_percent,
            ROUND(position, 1) as pos_avg
        FROM gsc_date_performance 
        ORDER BY date DESC
        LIMIT 10
    """).df()
    
    print(df.to_string(index=False))

def main():
    """Função principal."""
    # Configura encoding UTF-8 para Windows
    import sys
    import io
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    print("\n" + "🎯 VISUALIZADOR DE DADOS SIMULADOS ".center(70, "="))
    print(f"📁 Banco de dados: {DB_PATH}")
    print(f"🕐 Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not DB_PATH.exists():
        print(f"\n❌ ERRO: Banco de dados não encontrado em {DB_PATH}")
        print("\n💡 Execute primeiro: python tests/simulador_dados.py --days 30")
        return
    
    # Conecta ao banco
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    try:
        # Mostra todas as visualizações
        show_table_info(conn)
        show_traffic_sample(conn)
        show_traffic_sources_summary(conn)
        show_conversions_summary(conn)
        show_engagement_by_page(conn)
        show_gsc_queries(conn)
        show_gsc_devices(conn)
        show_daily_trend(conn)
        
        print("\n" + "="*70)
        print("✨ Visualização concluída!")
        print("="*70)
        
        print("\n💡 DICAS:")
        print("  • Use DBeaver ou outro client SQL para explorar mais: duckdb://data/processed/ga4_data.duckdb")
        print("  • Execute queries customizadas: python -c 'import duckdb; conn = duckdb.connect(\"data/processed/ga4_data.duckdb\"); print(conn.execute(\"SELECT * FROM traffic LIMIT 5\").df())'")
        print("  • Gere novos dados: python tests/simulador_dados.py --clear --days 60")
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()
