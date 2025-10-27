#!/usr/bin/env python3
"""
Visualizador rápido de dados JSON em data/raw/
"""

import json
import sys
import io
from pathlib import Path
from glob import glob

# Configura encoding UTF-8 para Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def show_json_file(filepath: str):
    """Mostra conteúdo de um arquivo JSON."""
    print(f"\n{'='*70}")
    print(f"📄 Arquivo: {Path(filepath).name}")
    print('='*70)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, dict):
            if 'metadata' in data and 'rows' in data:
                # Formato GA4/GSC
                metadata = data.get('metadata', {})
                rows = data.get('rows', [])
                
                print(f"\n📊 Metadados:")
                for key, value in metadata.items():
                    print(f"  {key}: {value}")
                
                print(f"\n📈 Dados: {len(rows)} registros")
                
                if rows:
                    print(f"\n🔍 Primeiros 5 registros:")
                    for i, row in enumerate(rows[:5], 1):
                        print(f"\n  #{i}:")
                        if isinstance(row, dict):
                            for k, v in row.items():
                                print(f"    {k}: {v}")
                        else:
                            print(f"    {row}")
            else:
                print(f"\n📊 Tipo: dict com {len(data)} chaves")
                print(f"Chaves: {list(data.keys())[:10]}")
        
        elif isinstance(data, list):
            print(f"\n📊 Lista com {len(data)} itens")
            if data:
                print(f"\n🔍 Primeiros 3 itens:")
                for i, item in enumerate(data[:3], 1):
                    print(f"\n  #{i}: {json.dumps(item, indent=2, ensure_ascii=False)[:200]}...")
        
        else:
            print(f"\n📊 Tipo: {type(data)}")
            print(f"Conteúdo: {str(data)[:500]}")
            
    except Exception as e:
        print(f"❌ Erro ao ler arquivo: {e}")

def main():
    print("\n" + "🔍 VISUALIZADOR DE DADOS RAW ".center(70, "="))
    
    # Lista arquivos em data/raw
    raw_path = Path(__file__).parent.parent / "data" / "raw"
    
    if not raw_path.exists():
        print(f"\n❌ Diretório {raw_path} não encontrado!")
        return
    
    json_files = list(raw_path.glob("*.json"))
    
    if not json_files:
        print(f"\n❌ Nenhum arquivo JSON encontrado em {raw_path}")
        return
    
    print(f"\n📁 Diretório: {raw_path}")
    print(f"📊 Arquivos encontrados: {len(json_files)}\n")
    
    # Organiza por tipo
    files_by_type = {}
    for f in json_files:
        file_type = f.stem.split('_')[1] if '_' in f.stem else 'outros'
        if file_type not in files_by_type:
            files_by_type[file_type] = []
        files_by_type[file_type].append(f)
    
    # Mostra um arquivo de cada tipo
    for file_type, files in sorted(files_by_type.items()):
        print(f"\n{'='*70}")
        print(f"📦 Tipo: {file_type.upper()} ({len(files)} arquivos)")
        print('='*70)
        
        # Pega o mais recente
        latest_file = sorted(files)[-1]
        show_json_file(latest_file)
    
    print(f"\n{'='*70}")
    print("✨ Visualização concluída!")
    print('='*70)
    
    print("\n💡 RESUMO DOS DADOS:")
    for file_type, files in sorted(files_by_type.items()):
        print(f"  • {file_type}: {len(files)} arquivo(s)")
    
    print("\n📌 NOTA: Estes são os dados ORIGINAIS coletados das APIs")
    print("   O simulador gera dados NOVOS que vão para o banco DuckDB")

if __name__ == "__main__":
    main()
