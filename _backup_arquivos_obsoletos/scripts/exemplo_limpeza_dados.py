#!/usr/bin/env python3
"""
Script de exemplo: Limpeza e validação de dados.

Demonstra o uso completo do módulo de limpeza para:
- Identificar e tratar valores nulos
- Remover duplicatas
- Validar integridade dos dados
- Gerar relatórios de qualidade
"""

import sys
from pathlib import Path

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.cleaning import (
    JSONCleaner,
    GA4DataCleaner,
    GSCDataCleaner,
    DeduplicateData,
    GA4Validator,
    GSCValidator,
    ValidationReport,
)
import json


def exemplo_limpeza_json():
    """Demonstra limpeza de arquivo JSON."""
    print("=" * 70)
    print("EXEMPLO 1: Limpeza de Arquivo JSON")
    print("=" * 70)
    
    # Exemplo com dados GA4
    print("\n[GA4] Limpando arquivo de tráfego...")
    
    input_file = "data/raw/ga4_traffic_20241021_20241027.json"
    output_file = "data/processed/cleaned_ga4_traffic.json"
    
    if not Path(input_file).exists():
        print(f"⚠️  Arquivo não encontrado: {input_file}")
        print("Execute primeiro: python scripts/exemplo_coleta_ga4.py")
        return
    
    # Limpa arquivo
    cleaned_data = JSONCleaner.clean_json_file(
        input_path=input_file,
        output_path=output_file,
        source="ga4"
    )
    
    print(f"✓ Arquivo limpo salvo em: {output_file}")
    print(f"  Total de linhas: {len(cleaned_data.get('rows', []))}")
    
    # Exemplo com dados GSC
    print("\n[GSC] Limpando arquivo de queries...")
    
    gsc_input = "data/raw/gsc_query_performance_20241014_20241020.json"
    gsc_output = "data/processed/cleaned_gsc_queries.json"
    
    if Path(gsc_input).exists():
        cleaned_gsc = JSONCleaner.clean_json_file(
            input_path=gsc_input,
            output_path=gsc_output,
            source="gsc"
        )
        
        print(f"✓ Arquivo limpo salvo em: {gsc_output}")
        print(f"  Total de linhas: {len(cleaned_gsc.get('rows', []))}")
    else:
        print(f"⚠️  Arquivo não encontrado: {gsc_input}")


def exemplo_tratamento_nulos():
    """Demonstra tratamento de valores nulos."""
    print("\n" + "=" * 70)
    print("EXEMPLO 2: Tratamento de Valores Nulos")
    print("=" * 70)
    
    # Dados de exemplo com valores nulos
    raw_data = {
        "property_id": None,
        "date": "2024-10-21",
        "session_source": None,
        "session_medium": "",
        "sessions": None,
        "active_users": 150,
        "new_users": None,
        "screen_page_views": "invalid",
        "average_session_duration": 45.2,
    }
    
    print("\n📋 Dados brutos:")
    for key, value in raw_data.items():
        print(f"  {key}: {repr(value)}")
    
    # Limpa usando GA4DataCleaner
    cleaned = GA4DataCleaner.clean_traffic_row(raw_data)
    
    print("\n✨ Dados limpos:")
    for key, value in cleaned.items():
        if key in raw_data:
            original = raw_data[key]
            if original != value:
                print(f"  {key}: {repr(value)} [MODIFICADO de {repr(original)}]")
            else:
                print(f"  {key}: {repr(value)}")
    
    print("\n📊 Estratégias aplicadas:")
    print("  - Strings nulas → '(not set)' ou valor padrão")
    print("  - Números nulos → 0.0")
    print("  - Strings inválidas em números → 0.0")
    print("  - property_id nulo → '(not set)'")


def exemplo_validacao_ctr():
    """Demonstra validação e recálculo de CTR."""
    print("\n" + "=" * 70)
    print("EXEMPLO 3: Validação e Recálculo de CTR")
    print("=" * 70)
    
    # Casos de teste
    test_cases = [
        {"clicks": 100, "impressions": 1000, "ctr": None},
        {"clicks": 50, "impressions": 2000, "ctr": 0.03},  # Inconsistente
        {"clicks": 0, "impressions": 0, "ctr": None},
        {"clicks": 75, "impressions": 500, "ctr": 0.15},  # Correto
        {"clicks": 200, "impressions": 100, "ctr": 0.5},  # Impossível
    ]
    
    print("\n📊 Validando e corrigindo CTR:")
    print("\n  {:>8} {:>12} {:>10} {:>10} {:>8}".format(
        "Clicks", "Impressions", "CTR Orig", "CTR Calc", "Status"
    ))
    print("  " + "-" * 60)
    
    for case in test_cases:
        clicks = case["clicks"]
        impressions = case["impressions"]
        original_ctr = case["ctr"]
        
        # Limpa dados
        cleaned = GSCDataCleaner.clean_query_row({
            "site_url": "https://example.com",
            "query": "test",
            "clicks": clicks,
            "impressions": impressions,
            "ctr": original_ctr,
            "position": 5.0,
            "start_date": "2024-10-01",
            "end_date": "2024-10-31",
        })
        
        calculated_ctr = cleaned["ctr"]
        
        # Status
        if original_ctr is None:
            status = "CALCULADO"
        elif abs(calculated_ctr - original_ctr) > 0.01:
            status = "CORRIGIDO"
        else:
            status = "OK"
        
        print("  {:8.0f} {:12.0f} {:10} {:10.4f} {:>8}".format(
            clicks,
            impressions,
            f"{original_ctr:.4f}" if original_ctr is not None else "None",
            calculated_ctr,
            status
        ))


def exemplo_remocao_duplicatas():
    """Demonstra remoção de duplicatas."""
    print("\n" + "=" * 70)
    print("EXEMPLO 4: Remoção de Duplicatas")
    print("=" * 70)
    
    # Dados de exemplo com duplicatas
    traffic_data = [
        {
            "property_id": "123",
            "date": "2024-10-21",
            "session_source": "google",
            "session_medium": "organic",
            "session_campaign_name": "(not set)",
            "sessions": 100,
            "collected_at": "2024-10-21T10:00:00",
        },
        {
            "property_id": "123",
            "date": "2024-10-21",
            "session_source": "google",
            "session_medium": "organic",
            "session_campaign_name": "(not set)",
            "sessions": 105,  # Valor diferente
            "collected_at": "2024-10-21T11:00:00",  # Mais recente
        },
        {
            "property_id": "123",
            "date": "2024-10-21",
            "session_source": "facebook",
            "session_medium": "social",
            "session_campaign_name": "campaign1",
            "sessions": 50,
            "collected_at": "2024-10-21T10:00:00",
        },
    ]
    
    print(f"\n📋 Total de registros brutos: {len(traffic_data)}")
    
    # Remove duplicatas
    unique_data = DeduplicateData.deduplicate_ga4_traffic(traffic_data)
    
    print(f"✓ Total de registros únicos: {len(unique_data)}")
    print(f"  Duplicatas removidas: {len(traffic_data) - len(unique_data)}")
    
    print("\n📊 Registros únicos mantidos:")
    for idx, row in enumerate(unique_data, 1):
        print(f"\n  [{idx}] {row['session_source']}/{row['session_medium']}")
        print(f"      Sessions: {row['sessions']}")
        print(f"      Coletado em: {row['collected_at']}")
    
    # Relatório de duplicatas
    print("\n📈 Relatório de duplicatas:")
    report = DeduplicateData.find_duplicates_report(
        traffic_data,
        key_fields=["property_id", "date", "session_source", "session_medium"]
    )
    
    print(f"  Total de linhas: {report['total_rows']}")
    print(f"  Chaves únicas: {report['unique_keys']}")
    print(f"  Chaves duplicadas: {report['duplicate_keys']}")
    print(f"  Linhas duplicadas: {report['duplicate_rows_count']}")


def exemplo_validacao_dataset():
    """Demonstra validação completa de dataset."""
    print("\n" + "=" * 70)
    print("EXEMPLO 5: Validação de Dataset Completo")
    print("=" * 70)
    
    # Dataset de exemplo com erros
    test_data = [
        # Válido
        {
            "property_id": "123",
            "date": "2024-10-21",
            "session_source": "google",
            "sessions": 100,
            "active_users": 80,
            "new_users": 70,
        },
        # Inválido: new_users > active_users
        {
            "property_id": "123",
            "date": "2024-10-22",
            "session_source": "facebook",
            "sessions": 50,
            "active_users": 40,
            "new_users": 50,  # Erro!
        },
        # Inválido: data malformada
        {
            "property_id": "123",
            "date": "21/10/2024",  # Formato errado
            "session_source": "twitter",
            "sessions": 30,
            "active_users": 25,
            "new_users": 20,
        },
        # Inválido: sessions negativa
        {
            "property_id": "123",
            "date": "2024-10-23",
            "session_source": "linkedin",
            "sessions": -10,  # Erro!
            "active_users": 15,
            "new_users": 10,
        },
    ]
    
    print(f"\n📋 Validando {len(test_data)} registros...")
    
    # Valida dataset
    report = ValidationReport.validate_dataset(
        test_data,
        validator_func=GA4Validator.validate_traffic_row
    )
    
    print(f"\n✅ Resumo da validação:")
    print(f"  Total de linhas: {report['total_rows']}")
    print(f"  Linhas válidas: {report['valid_rows']}")
    print(f"  Linhas inválidas: {report['invalid_rows']}")
    print(f"  Taxa de validação: {report['validation_rate']*100:.1f}%")
    print(f"  Total de erros: {report['error_count']}")
    
    print(f"\n❌ Tipos de erros encontrados:")
    for error_type, count in report['error_types'].items():
        print(f"  - {error_type}: {count}x")
    
    print(f"\n📝 Exemplos de registros inválidos:")
    for sample in report['invalid_samples'][:3]:
        print(f"\n  Linha {sample['row_index']}:")
        for error in sample['errors']:
            print(f"    • {error}")


def exemplo_pipeline_completo():
    """Demonstra pipeline completo de limpeza."""
    print("\n" + "=" * 70)
    print("EXEMPLO 6: Pipeline Completo de Limpeza")
    print("=" * 70)
    
    print("\n🔄 Pipeline: Dados brutos → Limpeza → Deduplicação → Validação")
    
    # 1. Dados brutos com problemas
    raw_data = [
        {"query": "python tutorial", "clicks": 100, "impressions": 1000, "ctr": None, "position": 3.5},
        {"query": None, "clicks": 50, "impressions": 500, "ctr": 0.1, "position": None},
        {"query": "python tutorial", "clicks": 100, "impressions": 1000, "ctr": 0.1, "position": 3.5},  # Duplicata
        {"query": "data science", "clicks": 200, "impressions": 100, "ctr": 2.0, "position": 1.0},  # Erro
    ]
    
    print(f"\n[1/3] Dados brutos: {len(raw_data)} registros")
    
    # 2. Limpeza
    cleaned_data = []
    for row in raw_data:
        cleaned_row = GSCDataCleaner.clean_query_row({
            "site_url": "https://example.com",
            "query": row.get("query"),
            "clicks": row.get("clicks"),
            "impressions": row.get("impressions"),
            "ctr": row.get("ctr"),
            "position": row.get("position"),
            "start_date": "2024-10-01",
            "end_date": "2024-10-31",
        })
        cleaned_data.append(cleaned_row)
    
    print(f"[2/3] Dados limpos: {len(cleaned_data)} registros")
    
    # 3. Deduplicação
    unique_data = DeduplicateData.deduplicate_gsc_query(cleaned_data)
    print(f"[3/3] Dados únicos: {len(unique_data)} registros")
    print(f"      Duplicatas removidas: {len(cleaned_data) - len(unique_data)}")
    
    # 4. Validação final
    report = ValidationReport.validate_dataset(
        unique_data,
        validator_func=lambda row: GSCValidator.validate_performance_row(row, check_dates=True)
    )
    
    print(f"\n✅ Resultado final:")
    print(f"  Linhas processadas: {len(raw_data)} → {len(unique_data)}")
    print(f"  Taxa de validação: {report['validation_rate']*100:.1f}%")
    print(f"  Linhas válidas: {report['valid_rows']}")
    print(f"  Linhas inválidas: {report['invalid_rows']}")
    
    if report['invalid_rows'] > 0:
        print(f"\n⚠️  Erros remanescentes:")
        for error_type, count in report['error_types'].items():
            print(f"  - {error_type}: {count}x")


def main():
    """Executa todos os exemplos."""
    print("\n")
    print("🧹" * 35)
    print("  EXEMPLOS: Limpeza e Validação de Dados GA4/GSC")
    print("🧹" * 35)
    
    try:
        exemplo_limpeza_json()
    except Exception as e:
        print(f"\n❌ Erro no exemplo 1: {e}")
    
    exemplo_tratamento_nulos()
    exemplo_validacao_ctr()
    exemplo_remocao_duplicatas()
    exemplo_validacao_dataset()
    exemplo_pipeline_completo()
    
    print("\n" + "=" * 70)
    print("✓ EXEMPLOS CONCLUÍDOS!")
    print("=" * 70)
    print("\n💡 Próximos passos:")
    print("  1. Integre a limpeza no fluxo de coleta")
    print("  2. Configure validações customizadas")
    print("  3. Automatize relatórios de qualidade de dados")
    print("  4. Use os cleaners antes de inserir no banco\n")


if __name__ == "__main__":
    main()
