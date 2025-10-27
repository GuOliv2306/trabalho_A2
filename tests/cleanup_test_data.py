"""
Script para LIMPAR todos os dados de teste do banco DuckDB.
CUIDADO: Este script apaga TODOS os dados das tabelas!
"""

import sys
from pathlib import Path

# Adiciona src ao path
sys.path.append(str(Path(__file__).parent.parent))

from src.collectors.db_storage import GA4DatabaseStorage


def cleanup_test_data():
    """Remove todos os dados de teste do banco."""
    db = GA4DatabaseStorage()
    
    print("🗑️  Limpando dados de teste...")
    
    tables = ['traffic', 'engagement', 'conversions', 'gsc_query_performance', 'gsc_page_performance']
    
    for table in tables:
        # Conta registros antes
        count_before = db.conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
        
        # Limpa a tabela
        db.conn.execute(f'DELETE FROM {table}')
        
        print(f"  ✓ {table}: {count_before} registros removidos")
    
    # Verifica se está tudo limpo
    print("\n📊 Verificação pós-limpeza:")
    for table in tables:
        count = db.conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
        print(f"  • {table}: {count} registros restantes")
    
    db.close()
    print("\n✅ Limpeza concluída!")


if __name__ == "__main__":
    resposta = input("⚠️  Tem certeza que deseja APAGAR TODOS os dados? (sim/não): ")
    if resposta.lower() in ['sim', 's', 'yes', 'y']:
        cleanup_test_data()
    else:
        print("❌ Operação cancelada.")
