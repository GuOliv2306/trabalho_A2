# 📊 Endpoints de Visualização de Dados

## Novos Endpoints Criados

Foram adicionados dois novos endpoints à API para visualização completa dos dados do banco DuckDB.

### 1. `/api/v1/data/all` - Visualização Completa

**Método:** `GET`  
**Tag:** `Dados Brutos`

Retorna uma visão completa de todos os dados de todas as 8 tabelas (GA4 + GSC).

#### Parâmetros

- `limit` (query parameter, opcional): Número máximo de registros por tabela
  - Tipo: `integer`
  - Padrão: `10`
  - Mínimo: `1`
  - Máximo: `1000`

#### Exemplo de Requisição

```bash
curl "http://localhost:8000/api/v1/data/all?limit=5"
```

#### Estrutura de Resposta

```json
{
  "resumo": {
    "tabelas": [
      {
        "tabela": "traffic",
        "registros": 240,
        "periodo": "2025-09-27 a 2025-10-26"
      },
      ...
    ],
    "total_registros": 1864
  },
  "ga4": {
    "traffic": {
      "total": 240,
      "dados": [
        {
          "id": 1,
          "date": "2025-10-26",
          "session_source": "google",
          "session_medium": "organic",
          "sessions": 269,
          "active_users": 243,
          "new_users": 79,
          "screen_page_views": 729,
          "average_session_duration": 218.26,
          "collected_at": "2025-10-26T18:20:15"
        },
        ...
      ]
    },
    "conversions": {
      "total": 750,
      "dados": [...]
    },
    "engagement": {
      "total": 810,
      "dados": [...]
    }
  },
  "gsc": {
    "query_performance": {
      "total": 15,
      "dados": [...]
    },
    "page_performance": {
      "total": 9,
      "dados": [...]
    },
    "country_performance": {
      "total": 7,
      "dados": [...]
    },
    "device_performance": {
      "total": 3,
      "dados": [...]
    },
    "date_performance": {
      "total": 30,
      "dados": [...]
    }
  }
}
```

---

### 2. `/api/v1/data/summary` - Resumo Estatístico

**Método:** `GET`  
**Tag:** `Dados Brutos`

Retorna apenas um resumo estatístico dos dados sem os registros completos. Útil para verificar rapidamente o estado do banco de dados.

#### Exemplo de Requisição

```bash
curl "http://localhost:8000/api/v1/data/summary"
```

#### Estrutura de Resposta

```json
{
  "database": "ga4_data.duckdb",
  "tabelas": [
    {
      "nome": "traffic",
      "descricao": "Tráfego GA4",
      "registros": 240,
      "periodo": {
        "inicio": "2025-09-27",
        "fim": "2025-10-26"
      },
      "metricas": {
        "sessions": {
          "total": 30636.0,
          "media": 127.65,
          "maximo": 311.0
        },
        "active_users": {
          "total": 28254.0,
          "media": 117.73,
          "maximo": 290.0
        },
        "screen_page_views": {
          "total": 76953.0,
          "media": 320.64,
          "maximo": 1062.0
        }
      }
    },
    {
      "nome": "conversions",
      "descricao": "Conversões GA4",
      "registros": 750,
      "periodo": {
        "inicio": "2025-09-27",
        "fim": "2025-10-26"
      },
      "metricas": {
        "key_events": {
          "total": 86115.0,
          "media": 114.82,
          "maximo": 1814.0
        },
        "event_count": {
          "total": 106553.0,
          "media": 142.07,
          "maximo": 2246.0
        }
      }
    },
    ...
  ]
}
```

---

## Correções Implementadas

### 1. Problema de Encoding UTF-8 no Windows

**Problema:** Caracteres especiais (`✓`, `⚠️`, etc.) causavam erro `'charmap' codec can't encode character` no Windows.

**Solução:** Substituição de todos os caracteres especiais por equivalentes ASCII no arquivo `src/collectors/db_storage.py`:

```bash
sed -i 's/✓/OK/g' src/collectors/db_storage.py
```

**Arquivos Modificados:**
- `src/collectors/db_storage.py`: Caracteres `✓` substituídos por `OK`

### 2. Lazy Initialization do Banco de Dados

**Problema:** Conexão com banco DuckDB era criada no import do módulo, causando conflitos quando múltiplos processos tentavam acessar o banco.

**Solução:** Implementação de lazy initialization com função `get_db()`:

**Antes:**
```python
db = GA4DatabaseStorage()  # Instância criada no import
```

**Depois:**
```python
db = None

def get_db():
    """Lazy initialization do banco de dados."""
    global db
    if db is None:
        db = GA4DatabaseStorage()
    return db
```

**Arquivos Modificados:**
- `app/main.py`: Todas as referências `db.query_df()` foram substituídas por `get_db().query_df()`

### 3. Correção de IDs Primários no DuckDB

**Problema:** DuckDB criou tabelas com `INTEGER PRIMARY KEY` mas sem `AUTOINCREMENT`, causando falha silenciosa nas inserções (`NOT NULL constraint failed: *.id`).

**Solução:** Adição de geração manual de IDs em todos os 8 métodos de inserção em `src/collectors/db_storage.py`:

```python
# Padrão aplicado a todos os métodos:
max_id_result = self.conn.execute("SELECT COALESCE(MAX(id), 0) FROM tabela").fetchone()
next_id = max_id_result[0] + 1 if max_id_result else 1

for row in rows:
    self.conn.execute("INSERT INTO tabela (id, col1, col2, ...) VALUES (?, ?, ...)", [next_id, ...])
    next_id += 1
```

**Métodos Corrigidos:**
1. `insert_traffic_data()`
2. `insert_conversions_data()`
3. `insert_engagement_data()`
4. `insert_gsc_query_data()`
5. `insert_gsc_page_data()`
6. `insert_gsc_country_data()`
7. `insert_gsc_device_data()`
8. `insert_gsc_date_data()`

---

## Testes de Validação

### 1. Verificar API Ativa
```bash
curl http://localhost:8000/health
# Resposta esperada: {"status":"ok"}
```

### 2. Testar Resumo Estatístico
```bash
curl "http://localhost:8000/api/v1/data/summary" | python -m json.tool
```

### 3. Testar Visualização Completa (3 registros)
```bash
curl "http://localhost:8000/api/v1/data/all?limit=3" | python -m json.tool
```

### 4. Testar Visualização Completa (máximo de registros)
```bash
curl "http://localhost:8000/api/v1/data/all?limit=100" | python -m json.tool
```

---

## Iniciar a API

### Método 1: Execução Direta
```bash
cd "c:/Users/guguo/OneDrive/Área de Trabalho/trabalho_A2"
python app/main.py
```

### Método 2: Via Uvicorn
```bash
python -m uvicorn app.main:app --reload --port 8000
```

---

## Documentação Interativa

Com a API rodando, acesse a documentação Swagger:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## Estrutura Completa dos Endpoints

```
GET  /health                              # Health check
GET  /api/v1/overview/kpis               # KPIs principais
GET  /api/v1/analysis/correlation_matrix # Matriz de correlação
GET  /api/v1/analysis/page_clusters      # Clusters de páginas
GET  /api/v1/page_analysis               # Análise de página específica
POST /api/v1/predict/simulator           # Simulador preditivo
GET  /api/v1/data/all                    # ✨ NOVO: Todos os dados
GET  /api/v1/data/summary                # ✨ NOVO: Resumo estatístico
```

---

## Dados Disponíveis

O banco de dados contém **1.864 registros** distribuídos em:

| Tabela | Registros | Período |
|--------|-----------|---------|
| **GA4 Traffic** | 240 | 30 dias |
| **GA4 Conversions** | 750 | 30 dias |
| **GA4 Engagement** | 810 | 30 dias |
| **GSC Queries** | 15 | 1 dia |
| **GSC Pages** | 9 | 1 dia |
| **GSC Countries** | 7 | 1 dia |
| **GSC Devices** | 3 | 1 dia |
| **GSC Date Series** | 30 | 30 dias |

---

## Próximos Passos

1. ✅ Endpoints de visualização implementados
2. ✅ Correções de encoding UTF-8 aplicadas
3. ✅ Lazy initialization do banco implementada
4. ✅ Correção de IDs primários concluída
5. ⏳ Integrar frontend React com novos endpoints
6. ⏳ Adicionar autenticação JWT (se necessário)
7. ⏳ Implementar cache Redis para queries pesadas
8. ⏳ Criar testes automatizados para os endpoints

---

**Data da Última Atualização:** 26 de outubro de 2025  
**Versão da API:** 1.0.0
