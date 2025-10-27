# Sistema de Coleta e Análise de Dados - Google Analytics 4 & Search Console

Sistema completo para coleta, armazenamento e análise de dados do **Google Analytics 4 (GA4)** e **Google Search Console (GSC)** usando as APIs oficiais.

## 📋 Funcionalidades

✅ **Coleta de Dados GA4**
- Tráfego (sessões, usuários, pageviews, fontes)
- Conversões (eventos-chave, receita, transações)
- Engajamento (taxa de engajamento, duração, eventos)
- Dados em tempo real (usuários ativos, páginas visualizadas)

✅ **Coleta de Dados GSC**
- Performance de palavras-chave (queries, cliques, impressões, CTR)
- Performance de páginas/URLs
- Análise por país (geolocalização)
- Análise por dispositivo (desktop, mobile, tablet)
- Séries temporais (evolução diária)

✅ **Limpeza e Validação de Dados**
- Tratamento automático de valores nulos (zero-fill, forward-fill)
- Recálculo de CTR para dados GSC
- Remoção de duplicatas
- Validação de integridade (ranges, consistência)
- Relatórios de qualidade de dados

✅ **Armazenamento**
- Formato JSON local (`data/raw/`)
- Banco de dados DuckDB unificado (`data/processed/`)
- Schema otimizado para análise combinada GA4 + GSC
- Limpeza automática antes de inserção no banco

✅ **Infraestrutura**
- API FastAPI para endpoints customizados
- Docker/Docker Compose (em desenvolvimento)
- Scripts de automação

## 🚀 Instalação

### 1. Criar ambiente virtual

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows
```

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Configurar credenciais do Google Analytics e Search Console

#### 3.1. Obter credenciais
1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie/selecione um projeto
3. Ative as APIs:
   - **Google Analytics Data API** (para GA4)
   - **Google Search Console API** (para GSC)
4. Crie uma **Service Account**
5. Baixe o arquivo JSON de credenciais
6. **Importante**: Adicione a Service Account como usuário em:
   - GA4: Admin → Property Access Management → Add user (role: Viewer)
   - GSC: Settings → Users and permissions → Add user (role: Full)

#### 3.2. Configurar variáveis de ambiente

```bash
export GA4_PROPERTY_ID="123456789"  # Seu Property ID do GA4
export GSC_SITE_URL="https://www.seusite.com/"  # URL verificada no GSC
export GOOGLE_APPLICATION_CREDENTIALS="/caminho/para/credentials.json"
```

Ou crie um arquivo `.env`:

```env
GA4_PROPERTY_ID=123456789
GSC_SITE_URL=https://www.seusite.com/
GOOGLE_APPLICATION_CREDENTIALS=/caminho/para/credentials.json
```

### 4. Configurar settings (opcional)

Copie e edite o arquivo de configuração:

```bash
cp config/settings.example.yaml config/settings.yaml
# Edite config/settings.yaml com suas configurações
```

## 📖 Uso

### Coleta Completa GA4 (Exemplo Básico)

```bash
python scripts/exemplo_coleta_ga4.py
```

Este script executa:
1. Coleta dados dos últimos 7 dias do GA4
2. Salva JSONs em `data/raw/`
3. Insere dados no banco DuckDB
4. Exibe estatísticas resumidas

### Coleta Completa GSC (Exemplo Básico)

```bash
python scripts/exemplo_coleta_gsc.py
```

Este script executa:
1. Coleta dados de busca orgânica dos últimos 7 dias
2. Salva JSONs em `data/raw/`
3. Insere dados no mesmo banco DuckDB
4. Exibe top queries, páginas e estatísticas

### Uso Programático - GA4

```python
from src.collectors.ga_orchestrator import GA4Orchestrator
from src.collectors.db_storage import GA4DatabaseStorage

# 1. Inicializar orchestrator
orchestrator = GA4Orchestrator(
    property_id="123456789",
    credentials_path="credentials.json"
)

# 2. Coletar dados
saved_files = orchestrator.collect_and_save(
    report_types=["traffic", "conversions", "engagement"],
    start_date="30daysAgo",
    end_date="today"
)

# 3. Armazenar no banco
db = GA4DatabaseStorage()
for filepath in saved_files.values():
    db.insert_from_json(filepath)

# 4. Executar queries
stats = db.get_summary_stats()
print(stats)

db.close()
```

### Uso Programático - GSC

```python
from src.collectors.gsc_orchestrator import GSCOrchestrator
from src.collectors.db_storage import GA4DatabaseStorage

# 1. Inicializar orchestrator
orchestrator = GSCOrchestrator(
    site_url="https://www.seusite.com/",
    credentials_path="credentials.json"
)

# 2. Coletar dados
saved_files = orchestrator.collect_and_save(
    report_types=[
        "query_performance",
        "page_performance",
        "country_performance",
        "device_performance",
        "date_performance",
    ],
    start_date="2024-01-01",
    end_date="2024-01-31",
    max_rows_queries=5000,
    max_rows_pages=1000,
)

# 3. Armazenar no banco (mesmo banco do GA4!)
db = GA4DatabaseStorage()
for filepath in saved_files.values():
    db.insert_from_json(filepath)

db.close()
```

### Coleta Incremental (Atualização Diária)

```python
from src.collectors.ga_orchestrator import GA4Orchestrator

orchestrator = GA4Orchestrator(property_id="123456789")

# Coleta apenas dados de ontem
filepath = orchestrator.collect_incremental(
    report_type="traffic",
    start_date="yesterday",
    end_date="yesterday"
)
```

## 📊 Estrutura de Dados

### GA4 - Tipos de Reports

#### 1. Traffic (Tráfego)
- **Dimensões**: date, sessionSource, sessionMedium, sessionCampaignName
- **Métricas**: sessions, activeUsers, newUsers, screenPageViews, averageSessionDuration

#### 2. Conversions (Conversões)
- **Dimensões**: date, eventName, sessionSource, sessionMedium
- **Métricas**: keyEvents, eventCount, totalRevenue, transactions, purchaseRevenue

#### 3. Engagement (Engajamento)
- **Dimensões**: date, pagePath, unifiedScreenName, deviceCategory
- **Métricas**: engagementRate, engagedSessions, averageSessionDuration, eventCount, userEngagementDuration

#### 4. Realtime Traffic (Tempo Real)
- **Dimensões**: unifiedScreenName, country, city
- **Métricas**: activeUsers, screenPageViews

### GSC - Tipos de Reports

#### 1. Query Performance (Palavras-chave)
- **Dimensões**: query (palavra-chave)
- **Métricas**: clicks, impressions, ctr, position
- **Uso**: Identificar queries que trazem tráfego orgânico

#### 2. Page Performance (Páginas/URLs)
- **Dimensões**: page (URL)
- **Métricas**: clicks, impressions, ctr, position
- **Uso**: Analisar performance de páginas específicas

#### 3. Country Performance (Países)
- **Dimensões**: country (código ISO)
- **Métricas**: clicks, impressions, ctr, position
- **Uso**: Análise geográfica do tráfego orgânico

#### 4. Device Performance (Dispositivos)
- **Dimensões**: device (DESKTOP, MOBILE, TABLET)
- **Métricas**: clicks, impressions, ctr, position
- **Uso**: Otimização por tipo de dispositivo

#### 5. Date Performance (Série Temporal)
- **Dimensões**: date
- **Métricas**: clicks, impressions, ctr, position
- **Uso**: Análise de tendências ao longo do tempo

#### 6. Query + Page Performance (Combinado)
- **Dimensões**: query, page
- **Métricas**: clicks, impressions, ctr, position
- **Uso**: Análise detalhada query → landing page

## 🧹 Limpeza e Validação de Dados

### Funcionalidades de Limpeza

O sistema inclui módulo completo de limpeza automática (`src/cleaning/`):

**Tratamento de Valores Nulos:**
- Métricas numéricas → `0.0` (zero-fill)
- Dimensões texto → valores padrão: `"(not set)"`, `"(direct)"`, `"(none)"`
- CTR nulo → recalculado automaticamente: `clicks / impressions`

**Remoção de Duplicatas:**
- Identifica registros duplicados por chaves únicas
- Mantém versão mais recente (`collected_at`)
- Gera relatórios de duplicatas removidas

**Validação de Integridade:**
- Formatos de data (YYYY-MM-DD)
- Ranges válidos (CTR: 0-1, position: >=1)
- Consistência lógica (ex: `new_users <= active_users`)
- CTR vs clicks/impressions (tolerância 1%)

### Uso Automático

```python
from src.collectors.db_storage import GA4DatabaseStorage

# Limpeza acontece automaticamente antes de inserir no banco
db = GA4DatabaseStorage(
    auto_clean=True,         # Trata nulos e recalcula métricas
    auto_deduplicate=True    # Remove duplicatas
)

count = db.insert_from_json("data/raw/ga4_traffic.json")
# Dados já foram limpos e validados!
```

### Uso Manual

```python
from src.cleaning import JSONCleaner, DeduplicateData, ValidationReport

# Limpar arquivo JSON
cleaned = JSONCleaner.clean_json_file(
    input_path="data/raw/gsc_queries.json",
    output_path="data/processed/cleaned_queries.json",
    source="gsc"
)

# Remover duplicatas
unique = DeduplicateData.deduplicate_gsc_query(cleaned['rows'])

# Validar qualidade
report = ValidationReport.validate_dataset(unique, GSCValidator.validate_performance_row)
print(f"Taxa de validação: {report['validation_rate']*100:.1f}%")
```

**Documentação completa:** Ver `src/cleaning/README.md`

## 🗄️ Banco de Dados

### Schema DuckDB

O banco unificado possui **10 tabelas**:

**GA4 (4 tabelas):**
- `traffic`: Dados de tráfego histórico
- `conversions`: Dados de conversões e receita
- `engagement`: Dados de engajamento
- `realtime_traffic`: Snapshots de dados em tempo real

**GSC (6 tabelas):**
- `gsc_query_performance`: Performance por palavra-chave
- `gsc_page_performance`: Performance por URL
- `gsc_country_performance`: Performance por país
- `gsc_device_performance`: Performance por dispositivo
- `gsc_date_performance`: Série temporal diária
- `gsc_query_page_performance`: Combinação query + page

### Queries de Exemplo

#### GA4: Top páginas mais visitadas

```python
from src.collectors.db_storage import GA4DatabaseStorage

db = GA4DatabaseStorage()

result = db.query("""
    SELECT 
        page_path,
        SUM(screen_page_views) as total_views,
        SUM(engaged_sessions) as engaged
    FROM engagement
    GROUP BY page_path
    ORDER BY total_views DESC
    LIMIT 10
""")
```

#### GA4: Receita por fonte/mídia

```python
result = db.query("""
    SELECT 
        session_source,
        session_medium,
        SUM(total_revenue) as revenue,
        SUM(transactions) as txns
    FROM conversions
    GROUP BY session_source, session_medium
    ORDER BY revenue DESC
""")
```

#### GSC: Top queries por cliques

```python
result = db.query("""
    SELECT 
        query,
        SUM(clicks) as total_clicks,
        SUM(impressions) as total_impressions,
        AVG(ctr) as avg_ctr,
        AVG(position) as avg_position
    FROM gsc_query_performance
    GROUP BY query
    ORDER BY total_clicks DESC
    LIMIT 20
""")
```

#### GSC: Performance de páginas

```python
result = db.query("""
    SELECT 
        page,
        SUM(clicks) as clicks,
        AVG(position) as avg_position
    FROM gsc_page_performance
    WHERE clicks > 10
    GROUP BY page
    ORDER BY clicks DESC
""")
```

#### Análise Combinada GA4 + GSC

```python
# Correlação: Tráfego orgânico (GA4) vs Cliques (GSC)
result = db.query("""
    SELECT 
        g.date,
        SUM(t.sessions) as ga4_sessions,
        SUM(g.clicks) as gsc_clicks,
        AVG(g.position) as avg_position
    FROM gsc_date_performance g
    LEFT JOIN traffic t 
        ON g.date = t.date 
        AND t.session_medium = 'organic'
    GROUP BY g.date
    ORDER BY g.date DESC
    LIMIT 30
""")
```

```python
db.close()
```

## 🏗️ Estrutura do Projeto

```
trabalho_A2/
├── app/
│   ├── __init__.py
│   └── main.py              # FastAPI endpoints (exemplo mínimo)
├── src/
│   ├── ga/                  # Módulo Google Analytics 4
│   │   ├── __init__.py
│   │   ├── ga_client.py     # Cliente GA4 Data API
│   │   └── collectors.py    # Coletores especializados GA4
│   ├── gsc/                 # Módulo Google Search Console
│   │   ├── __init__.py
│   │   ├── gsc_client.py    # Cliente GSC API
│   │   └── collectors.py    # Coletores especializados GSC
│   ├── collectors/          # Orchestrators e storage
│   │   ├── __init__.py
│   │   ├── ga_orchestrator.py   # Coordena coleta GA4
│   │   ├── gsc_orchestrator.py  # Coordena coleta GSC
│   │   └── db_storage.py        # Armazenamento DuckDB unificado (com limpeza)
│   ├── cleaning/            # **NOVO** Limpeza e validação
│   │   ├── __init__.py
│   │   ├── data_cleaner.py      # Tratamento de nulos, recálculo CTR
│   │   ├── deduplicator.py      # Remoção de duplicatas
│   │   ├── validators.py        # Validação de integridade
│   │   └── README.md            # Documentação detalhada
│   └── ml/                  # Machine Learning (placeholder)
├── data/
│   ├── raw/                 # JSONs coletados (GA4 + GSC)
│   └── processed/           # Banco DuckDB + JSONs limpos
├── config/
│   ├── settings.example.yaml
│   └── settings.yaml        # (crie este arquivo)
├── scripts/
│   ├── exemplo_coleta_ga4.py     # Script demonstrativo GA4
│   ├── exemplo_coleta_gsc.py     # Script demonstrativo GSC
│   ├── exemplo_limpeza_dados.py  # **NOVO** Demonstra limpeza/validação
│   └── run.sh
├── docker/
│   ├── docker-compose.yml
│   └── Dockerfile
├── requirements.txt
└── README.md
```

## 🔧 API FastAPI (em desenvolvimento)

Inicie o servidor FastAPI:

```bash
uvicorn app.main:app --reload
```

Acesse:
- Docs: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health

## � API FastAPI - Endpoints Disponíveis

### Iniciar a API

```bash
# Método 1: Execução direta
python app/main.py

# Método 2: Via Uvicorn
python -m uvicorn app.main:app --reload --port 8000
```

### Documentação Interativa

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Endpoints Implementados

#### 🏥 Health Check
```bash
GET /health                                  # Status da API
```

#### 📊 Dashboard & Análises
```bash
GET /api/v1/overview/kpis                    # KPIs principais (sessões, conversões, bounce rate)
GET /api/v1/analysis/correlation_matrix      # Matriz de correlação entre métricas
GET /api/v1/analysis/page_clusters           # Clusters de páginas por performance
GET /api/v1/page_analysis?path=/produtos     # Análise detalhada de página específica
POST /api/v1/predict/simulator               # Simulador preditivo de performance
```

#### ✨ Visualização de Dados (NOVO)
```bash
GET /api/v1/data/all?limit=10                # Ver todos os dados (8 tabelas: GA4 + GSC)
GET /api/v1/data/summary                     # Resumo estatístico completo
```

### Exemplo de Uso

```bash
# Ver primeiros 5 registros de cada tabela
curl "http://localhost:8000/api/v1/data/all?limit=5" | python -m json.tool

# Ver apenas resumo estatístico
curl "http://localhost:8000/api/v1/data/summary" | python -m json.tool

# Obter KPIs do dashboard
curl "http://localhost:8000/api/v1/overview/kpis" | python -m json.tool
```

**Documentação detalhada dos endpoints:** Ver [`ENDPOINTS_VISUALIZACAO.md`](ENDPOINTS_VISUALIZACAO.md)

## 🧪 Simulador de Dados

Para testar a API sem dados reais do Google Analytics/Search Console:

```bash
# Gerar 30 dias de dados simulados (1.864 registros)
python tests/simulador_dados.py --days 30

# Limpar banco e gerar novos dados
python tests/simulador_dados.py --clear --days 30

# Visualizar dados gerados no terminal
python tests/visualizar_dados.py
```

O simulador gera dados realistas com:
- ✅ Distribuições estatísticas (Poisson, Normal, Beta)
- ✅ Padrões de comportamento de usuários reais
- ✅ Variação temporal (fins de semana vs dias úteis)
- ✅ 8 tabelas completas (GA4: traffic, conversions, engagement | GSC: queries, pages, countries, devices, dates)

## �📝 Próximos Passos

1. **Limpeza de Dados** (`src/cleaning/`) ✅ **CONCLUÍDO**
   - ✅ Normalização automática de dados GA4 + GSC
   - ✅ Remoção de duplicatas (por chave única)
   - ✅ Tratamento de valores nulos (zero-fill, CTR recálculo)
   - ✅ Validação de integridade (ranges, consistência)
   - ✅ Integração automática com db_storage.py

2. **Machine Learning** (`src/ml/`)
   - Previsão de conversões usando dados de tráfego orgânico
   - Segmentação de palavras-chave (high/medium/low intent)
   - Análise de churn
   - Correlação GA4 sessions x GSC clicks

3. **Endpoints FastAPI** (`app/main.py`)
   - GET /ga4/collect - Trigger coleta manual GA4
   - GET /gsc/collect - Trigger coleta manual GSC
   - GET /reports/{type} - Retorna dados JSON
   - GET /stats - Estatísticas agregadas (GA4 + GSC)
   - GET /keywords/top - Top queries do GSC
   - POST /analysis/combined - Análise combinada

4. **Docker & Automação**
   - Containerizar aplicação
   - Agendamento de coletas (cron: GA4 diário, GSC a cada 3 dias)
   - CI/CD pipeline
   - Dashboards com Streamlit/Plotly

## 💡 Casos de Uso

### 1. Análise SEO Completa
Combine dados do GSC (queries, posições) com dados do GA4 (sessões, conversões) para:
- Identificar queries com alto CTR mas baixa conversão
- Otimizar páginas com boa posição mas baixo engajamento
- Correlacionar mudanças em position com variação de tráfego

### 2. Atribuição de Valor a Queries
```python
# Atribui receita do GA4 a queries do GSC
db.query("""
    SELECT 
        g.query,
        SUM(g.clicks) as clicks,
        AVG(c.total_revenue) / AVG(t.sessions) as revenue_per_session
    FROM gsc_query_performance g
    JOIN gsc_page_performance p ON g.page = p.page
    JOIN traffic t ON p.page LIKE '%' || t.page_path || '%'
    JOIN conversions c ON t.date = c.date
    GROUP BY g.query
    ORDER BY revenue_per_session DESC
""")
```

### 3. Monitoramento de Performance
- Alertas quando queries importantes caem de posição
- Tracking de organic sessions (GA4) vs clicks (GSC)
- Detecção de anomalias em CTR

## 🤝 Contribuição

Este é um projeto de exemplo/scaffold. Adapte conforme suas necessidades.

## 📄 Licença

MIT License
