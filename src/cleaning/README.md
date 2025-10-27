# Módulo de Limpeza e Validação de Dados

Este módulo fornece ferramentas completas para limpeza, validação e pré-processamento de dados do Google Analytics 4 (GA4) e Google Search Console (GSC).

## 📋 Funcionalidades

### 🧹 Limpeza de Dados (`data_cleaner.py`)

**Tratamento de valores nulos:**
- Métricas numéricas: preenchimento com zero ou estratégias customizadas
- Dimensões texto: substituição por valores padrão como `"(not set)"`, `"(direct)"`, etc.
- Validação de tipos: conversão segura de strings para números

**Recálculo de métricas:**
- **CTR (Click-Through Rate)**: recalcula quando nulo usando `clicks / impressions`
- **Percentuais**: normaliza para range 0.0-1.0
- **Posição de busca**: valida posições válidas (>= 1.0)

**Classes disponíveis:**
- `DataCleaner`: Classe base com métodos utilitários
- `GA4DataCleaner`: Especializada em dados GA4
- `GSCDataCleaner`: Especializada em dados GSC
- `JSONCleaner`: Limpa arquivos JSON completos

### 🔄 Remoção de Duplicatas (`deduplicator.py`)

**Estratégias de deduplicação:**
- Identifica chaves únicas por tipo de report
- Mantém registro mais recente (`collected_at`)
- Gera relatórios de duplicatas encontradas

**Métodos por tipo de dados:**

**GA4:**
- `deduplicate_ga4_traffic()`: (property_id, date, source, medium, campaign)
- `deduplicate_ga4_conversions()`: (property_id, date, event_name, source, medium)
- `deduplicate_ga4_engagement()`: (property_id, date, page_path, screen_name, device)

**GSC:**
- `deduplicate_gsc_query()`: (site_url, query, start_date, end_date)
- `deduplicate_gsc_page()`: (site_url, page, start_date, end_date)
- `deduplicate_gsc_country()`: (site_url, country, start_date, end_date)
- `deduplicate_gsc_device()`: (site_url, device, start_date, end_date)
- `deduplicate_gsc_date()`: (site_url, date)
- `deduplicate_gsc_query_page()`: (site_url, query, page, start_date, end_date)

### ✅ Validação de Dados (`validators.py`)

**Validações implementadas:**
- Formato de datas (YYYY-MM-DD)
- Valores numéricos positivos
- Percentuais no range 0-1
- Consistência CTR vs clicks/impressions
- Posições de busca válidas (>= 1)
- Lógica de negócio (ex: new_users <= active_users)

**Classes de validação:**
- `DataValidator`: Validações base
- `GA4Validator`: Regras específicas GA4
- `GSCValidator`: Regras específicas GSC
- `ValidationReport`: Gera relatórios completos

## 🚀 Uso

### Exemplo 1: Limpeza Manual de Dados

```python
from src.cleaning import GA4DataCleaner, GSCDataCleaner

# Limpar row GA4
raw_row = {
    "property_id": None,
    "date": "2024-10-21",
    "sessions": None,
    "active_users": 150,
    "new_users": None,
}

cleaned = GA4DataCleaner.clean_traffic_row(raw_row)
# Resultado:
# {
#     "property_id": "(not set)",
#     "date": "2024-10-21",
#     "sessions": 0.0,
#     "active_users": 150.0,
#     "new_users": 0.0,
#     ...
# }

# Limpar row GSC com recálculo de CTR
gsc_row = {
    "site_url": "https://example.com",
    "query": "python tutorial",
    "clicks": 100,
    "impressions": 1000,
    "ctr": None,  # Será calculado automaticamente
    "position": 3.5,
}

cleaned_gsc = GSCDataCleaner.clean_query_row(gsc_row)
# cleaned_gsc["ctr"] == 0.1 (100/1000)
```

### Exemplo 2: Limpeza de Arquivo JSON

```python
from src.cleaning import JSONCleaner

# Limpa arquivo JSON completo
cleaned_data = JSONCleaner.clean_json_file(
    input_path="data/raw/ga4_traffic_20241021.json",
    output_path="data/processed/cleaned_ga4_traffic.json",
    source="ga4"
)

print(f"Linhas limpas: {len(cleaned_data['rows'])}")
```

### Exemplo 3: Remoção de Duplicatas

```python
from src.cleaning import DeduplicateData

# Remove duplicatas de queries GSC
queries = [
    {"site_url": "https://example.com", "query": "python", "clicks": 100, ...},
    {"site_url": "https://example.com", "query": "python", "clicks": 105, ...},  # Duplicata
    {"site_url": "https://example.com", "query": "java", "clicks": 50, ...},
]

unique = DeduplicateData.deduplicate_gsc_query(queries)
# unique terá 2 elementos (mantém o mais recente para "python")

# Gerar relatório de duplicatas
report = DeduplicateData.find_duplicates_report(
    queries,
    key_fields=["site_url", "query"]
)
print(f"Duplicatas encontradas: {report['duplicate_keys']}")
```

### Exemplo 4: Validação de Dataset

```python
from src.cleaning import GA4Validator, ValidationReport

# Valida lista de registros
traffic_data = [
    {"date": "2024-10-21", "sessions": 100, "active_users": 80, ...},
    {"date": "21/10/2024", "sessions": -10, "active_users": 50, ...},  # Inválido
]

report = ValidationReport.validate_dataset(
    traffic_data,
    validator_func=GA4Validator.validate_traffic_row
)

print(f"Taxa de validação: {report['validation_rate']*100:.1f}%")
print(f"Linhas válidas: {report['valid_rows']}")
print(f"Linhas inválidas: {report['invalid_rows']}")

# Ver erros
for error_type, count in report['error_types'].items():
    print(f"  - {error_type}: {count}x")
```

### Exemplo 5: Integração Automática com Banco

```python
from src.collectors.db_storage import GA4DatabaseStorage

# Inicializa com limpeza automática
db = GA4DatabaseStorage(
    db_path="data/processed/ga4_data.duckdb",
    auto_clean=True,           # Limpa dados automaticamente
    auto_deduplicate=True      # Remove duplicatas automaticamente
)

# Insere dados - limpeza acontece automaticamente
count = db.insert_from_json("data/raw/ga4_traffic.json")

db.close()
```

## 📊 Estratégias de Preenchimento

### Métricas Numéricas (GA4 e GSC)

| Métrica | Valor Nulo | Estratégia |
|---------|-----------|------------|
| `clicks` | `None` | → `0.0` |
| `impressions` | `None` | → `0.0` |
| `sessions` | `None` | → `0.0` |
| `active_users` | `None` | → `0.0` |
| `revenue` | `None` | → `0.0` |
| `average_session_duration` | `None` | → `0.0` |

### Métricas Calculadas

| Métrica | Cálculo | Validação |
|---------|---------|-----------|
| `ctr` | `clicks / impressions` | Range: 0.0-1.0 |
| `engagement_rate` | Fornecido pela API | Range: 0.0-1.0 |
| `position` | Fornecido pela API | Mínimo: 1.0, nulo → 100.0 |

### Dimensões de Texto (GA4)

| Dimensão | Valor Nulo/Vazio | Estratégia |
|----------|------------------|------------|
| `property_id` | `None` | → `"(not set)"` |
| `session_source` | `None` | → `"(direct)"` |
| `session_medium` | `None` | → `"(none)"` |
| `session_campaign_name` | `None` | → `"(not set)"` |
| `page_path` | `None` | → `"/"` |
| `device_category` | `None` | → `"desktop"` |

### Dimensões de Texto (GSC)

| Dimensão | Valor Nulo/Vazio | Estratégia |
|----------|------------------|------------|
| `query` | `None` | → `"(not provided)"` |
| `page` | `None` | → `"/"` |
| `country` | `None` | → `"(not set)"` |
| `device` | `None` | → `"DESKTOP"` |

## 🔍 Validações de Integridade

### Validações GA4

**Traffic (Tráfego):**
- `new_users <= active_users` (novos usuários não podem exceder total)
- `sessions >= 0` (não pode ser negativo)
- `date` no formato YYYY-MM-DD

**Conversions (Conversões):**
- `purchase_revenue <= total_revenue` (receita de compra é subset de total)
- `total_revenue >= 0`
- `transactions >= 0`

**Engagement (Engajamento):**
- `engagement_rate` entre 0.0 e 1.0
- `engaged_sessions >= 0`
- `event_count >= 0`

### Validações GSC

**Performance (Todas as tabelas):**
- `clicks <= impressions` (cliques não podem exceder impressões)
- `ctr = clicks / impressions` (consistência com tolerância de 1%)
- `position >= 1.0` (posição mínima é 1)
- `ctr` entre 0.0 e 1.0

**Device:**
- Valores permitidos: `"DESKTOP"`, `"MOBILE"`, `"TABLET"`

## 📈 Relatórios de Qualidade

### Relatório de Duplicatas

```python
{
    "total_rows": 1000,
    "unique_keys": 950,
    "duplicate_keys": 50,
    "duplicate_rows_count": 50,
    "examples": [
        {"key": {"query": "python", "date": "2024-10-21"}, "count": 2},
        ...
    ]
}
```

### Relatório de Validação

```python
{
    "total_rows": 500,
    "valid_rows": 475,
    "invalid_rows": 25,
    "validation_rate": 0.95,  # 95%
    "error_count": 32,
    "error_types": {
        "Formato de data inválido": 10,
        "sessions não pode ser negativo": 5,
        ...
    },
    "invalid_samples": [...]
}
```

## 🛠️ Script de Teste Completo

Execute o script de exemplo para ver todas as funcionalidades:

```bash
python scripts/exemplo_limpeza_dados.py
```

Este script demonstra:
1. Limpeza de arquivos JSON
2. Tratamento de valores nulos
3. Validação e recálculo de CTR
4. Remoção de duplicatas
5. Validação de dataset completo
6. Pipeline completo (limpeza → deduplicação → validação)

## 💡 Melhores Práticas

### 1. Sempre Use Limpeza Automática

```python
# ✅ Recomendado
db = GA4DatabaseStorage(auto_clean=True, auto_deduplicate=True)

# ❌ Evitar (dados sujos no banco)
db = GA4DatabaseStorage(auto_clean=False)
```

### 2. Valide Antes de Análises Críticas

```python
# Antes de gerar relatórios importantes
report = ValidationReport.validate_dataset(data, GA4Validator.validate_traffic_row)

if report['validation_rate'] < 0.90:
    print(f"⚠️  Qualidade baixa: {report['validation_rate']*100:.1f}%")
    # Investigar erros
```

### 3. Monitore Duplicatas

```python
dup_report = DeduplicateData.find_duplicates_report(data, key_fields)

if dup_report['duplicate_rows_count'] > len(data) * 0.1:
    print(f"⚠️  Muitas duplicatas: {dup_report['duplicate_rows_count']}")
    # Verificar lógica de coleta
```

### 4. Use CTR Recalculado

Para dados GSC, sempre confie no CTR recalculado:

```python
# O cleaner automaticamente recalcula CTR quando nulo ou inconsistente
cleaned = GSCDataCleaner.clean_query_row(row)
# cleaned["ctr"] sempre será clicks/impressions validado
```

## 🔧 Personalização

### Criar Validador Customizado

```python
from src.cleaning import DataValidator

class MyCustomValidator(DataValidator):
    @classmethod
    def validate_custom_rule(cls, row: Dict[str, Any]) -> List[str]:
        errors = []
        
        # Sua regra customizada
        if row.get("sessions") > 10000:
            errors.append("Sessions suspeitas (>10k)")
        
        return errors
```

### Estratégia de Preenchimento Customizada

```python
from src.cleaning import DataCleaner

# Preencher com média ao invés de zero
cleaner = DataCleaner()
value = cleaner.fill_null_numeric(None, strategy="mean", fallback=0.0)
```

## 📚 Referências

- **GA4 Data API**: [Official Docs](https://developers.google.com/analytics/devguides/reporting/data/v1)
- **Search Console API**: [Official Docs](https://developers.google.com/webmaster-tools/v1)
- **DuckDB**: [Documentation](https://duckdb.org/docs/)

## 🤝 Contribuindo

Para adicionar novas validações ou estratégias de limpeza:

1. Adicione método em `DataValidator` ou `DataCleaner`
2. Implemente testes em `scripts/exemplo_limpeza_dados.py`
3. Documente a nova funcionalidade neste README
