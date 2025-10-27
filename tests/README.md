# 🧪 Testes - Dashboard Analytics API

## 📊 Status dos Testes

✅ **10/10 testes passando**

```bash
================================= test session starts ==================================
platform win32 -- Python 3.12.10, pytest-8.3.3, pluggy-1.5.0
collected 10 items

tests/test_api.py::test_health_check PASSED                                       [ 10%]
tests/test_api.py::test_get_kpis PASSED                                           [ 20%]
tests/test_api.py::test_get_correlation_matrix PASSED                             [ 30%]
tests/test_api.py::test_get_page_clusters PASSED                                  [ 40%]
tests/test_api.py::test_get_page_analysis_not_found PASSED                        [ 50%]
tests/test_api.py::test_get_page_analysis_valid PASSED                            [ 60%]
tests/test_api.py::test_predict_simulator_valid PASSED                            [ 70%]
tests/test_api.py::test_predict_simulator_edge_cases PASSED                       [ 80%]
tests/test_api.py::test_predict_simulator_invalid_input PASSED                    [ 90%]
tests/test_api.py::test_openapi_docs PASSED                                       [100%]

============================== 10 passed, 2 warnings in 2.43s ==============================
```

---

## 📁 Arquivos de Teste

### 1. `test_api.py`
Suite completa de testes para a API FastAPI.

**Cobertura:**
- ✅ Health check
- ✅ Endpoints de KPIs
- ✅ Análises estáticas (correlações e clusters)
- ✅ Análises preditivas (análise de página e simulador)
- ✅ Validação de erros
- ✅ Documentação OpenAPI

### 2. `create_test_data.py`
Script para popular o banco DuckDB com dados de teste realistas.

**Gera:**
- 63 registros de tráfego (GA4)
- 210 registros de engajamento (GA4)
- 112 registros de conversões (GA4)
- 24 registros de queries GSC
- 40 registros de páginas GSC

**Total: 449 registros**

### 3. `cleanup_test_data.py`
Script para limpar todos os dados de teste do banco.

**Remove dados das tabelas:**
- `traffic`
- `engagement`
- `conversions`
- `gsc_query_performance`
- `gsc_page_performance`

---

## 🚀 Como Executar os Testes

### Pré-requisitos

```bash
# Instalar dependências
pip install -r requirements.txt

# Verificar que o banco existe
ls -la data/processed/ga4_data.duckdb
```

### Executar Todos os Testes

```bash
# Modo verbose (recomendado)
python -m pytest tests/test_api.py -v

# Modo quiet
python -m pytest tests/test_api.py

# Com coverage
python -m pytest tests/test_api.py --cov=app --cov-report=html
```

### Executar Teste Específico

```bash
# Um teste específico
python -m pytest tests/test_api.py::test_get_kpis -v

# Testes de um endpoint
python -m pytest tests/test_api.py -k "simulator" -v

# Parar no primeiro erro
python -m pytest tests/test_api.py -x
```

### Executar com Saída Detalhada

```bash
# Mostrar prints e logs
python -m pytest tests/test_api.py -v -s

# Mostrar apenas erros
python -m pytest tests/test_api.py --tb=short

# Mostrar traceback completo
python -m pytest tests/test_api.py --tb=long
```

---

## 🗃️ Gerenciar Dados de Teste

### Criar Dados de Teste

```bash
# Executar script
python tests/create_test_data.py
```

**Saída esperada:**
```
✓ Tabelas criadas/verificadas no banco de dados (GA4 + GSC)
🔄 Gerando dados de teste...
  → Inserindo dados de tráfego...
  ✓ 63 registros de tráfego inseridos
  → Inserindo dados de engajamento...
  ✓ 210 registros de engajamento inseridos
  → Inserindo dados de conversões...
  ✓ 112 registros de conversões inseridos
  → Inserindo dados de Search Console (queries)...
  ✓ 24 registros de GSC (queries) inseridos
  → Inserindo dados de Search Console (páginas)...
  ✓ 40 registros de GSC (páginas) inseridos

📊 Resumo dos dados inseridos:
  • Traffic: 63 registros
  • Engagement: 210 registros
  • Conversions: 112 registros
  • GSC Query Performance: 24 registros
  • GSC Page Performance: 40 registros

✅ Dados de teste criados com sucesso!
⚠️  LEMBRE-SE: Execute 'python tests/cleanup_test_data.py' para limpar depois!
```

### Limpar Dados de Teste

```bash
# Modo interativo (pede confirmação)
python tests/cleanup_test_data.py

# Modo automático (sem confirmação)
echo "sim" | python tests/cleanup_test_data.py
```

**Saída esperada:**
```
✓ Tabelas criadas/verificadas no banco de dados (GA4 + GSC)
⚠️  Tem certeza que deseja APAGAR TODOS os dados? (sim/não): sim
🗑️  Limpando dados de teste...
  ✓ traffic: 63 registros removidos
  ✓ engagement: 210 registros removidos
  ✓ conversions: 112 registros removidos
  ✓ gsc_query_performance: 24 registros removidos
  ✓ gsc_page_performance: 40 registros removidos

📊 Verificação pós-limpeza:
  • traffic: 0 registros restantes
  • engagement: 0 registros restantes
  • conversions: 0 registros restantes
  • gsc_query_performance: 0 registros restantes
  • gsc_page_performance: 0 registros restantes

✅ Limpeza concluída!
```

---

## 📝 Descrição Detalhada dos Testes

### 1. `test_health_check`
**Objetivo:** Verificar se a API está respondendo.

**Endpoint:** `GET /health`

**Validações:**
- Status code 200
- Resposta JSON com `{"status": "ok"}`

---

### 2. `test_get_kpis`
**Objetivo:** Validar KPIs principais do dashboard.

**Endpoint:** `GET /api/v1/overview/kpis`

**Validações:**
- Status code 200
- Presença de todos os campos obrigatórios:
  - `totalPaginas`
  - `sessoesTotais`
  - `conversoesTotais`
  - `mediaBounceRate`
  - `mediaSessionDuration`
- Tipos corretos (int para contadores, float para médias)
- Valores não negativos

**Exemplo de resposta:**
```json
{
  "totalPaginas": 10,
  "sessoesTotais": 5670,
  "conversoesTotais": 448,
  "mediaBounceRate": 0.55,
  "mediaSessionDuration": 142.35
}
```

---

### 3. `test_get_correlation_matrix`
**Objetivo:** Validar matriz de correlação entre métricas.

**Endpoint:** `GET /api/v1/analysis/correlation_matrix`

**Validações:**
- Status code 200
- Estrutura hierárquica correta
- Valores de correlação entre -1 e 1
- Sem valores NaN ou Infinity

**Exemplo de resposta:**
```json
{
  "conversions": {
    "sessions": 0.42,
    "pageViews": 0.38,
    "avgSessionDuration": -0.05
  },
  "engagementRate": {
    "sessions": 0.25,
    "pageViews": 0.22,
    "avgSessionDuration": 0.68
  },
  "averageSessionDuration": {
    "sessions": 0.35,
    "pageViews": 0.30,
    "conversions": -0.05
  }
}
```

---

### 4. `test_get_page_clusters`
**Objetivo:** Validar segmentação de páginas em clusters.

**Endpoint:** `GET /api/v1/analysis/page_clusters`

**Validações:**
- Status code 200
- Array de clusters não vazio
- Cada cluster contém:
  - `clusterId` (int)
  - `clusterName` (string)
  - `avgEngagementRate` (float)
  - `avgSessionDuration` (float)
  - `avgConversions` (int)
  - `totalPaginas` (int)

**Exemplo de resposta:**
```json
{
  "clusters": [
    {
      "clusterId": 0,
      "clusterName": "Páginas de Alto Engajamento e Conversão",
      "avgEngagementRate": 0.68,
      "avgSessionDuration": 285.5,
      "avgConversions": 25,
      "totalPaginas": 15
    },
    {
      "clusterId": 3,
      "clusterName": "Páginas Intermediárias",
      "avgEngagementRate": 0.48,
      "avgSessionDuration": 180.2,
      "avgConversions": 12,
      "totalPaginas": 195
    }
  ]
}
```

---

### 5. `test_get_page_analysis_not_found`
**Objetivo:** Validar erro quando página não existe.

**Endpoint:** `GET /api/v1/page_analysis?path=/pagina-inexistente`

**Validações:**
- Status code 404
- Mensagem de erro clara

---

### 6. `test_get_page_analysis_valid`
**Objetivo:** Validar análise de página existente.

**Endpoint:** `GET /api/v1/page_analysis?path=/produtos/notebook-dell`

**Validações:**
- Status code 200
- Estrutura com `dadosReais` e `analisePreditiva`
- Dados reais contêm métricas observadas
- Análise preditiva contém cluster e risco

**Exemplo de resposta:**
```json
{
  "pagePath": "/produtos/notebook-dell",
  "dadosReais": {
    "sessions": 450,
    "averageSessionDuration": 220.5,
    "engagementRate": 0.62,
    "pageViews": 680,
    "conversions": 28
  },
  "analisePreditiva": {
    "clusterName": "Produtos de Sucesso (Boa Conversão)",
    "riscoDeRejeicao": "Baixo"
  }
}
```

---

### 7. `test_predict_simulator_valid`
**Objetivo:** Validar simulador com dados válidos.

**Endpoint:** `POST /api/v1/predict/simulator`

**Payload:**
```json
{
  "contagemDePalavras": 1200,
  "numeroDeImagens": 5,
  "precoDoProduto": 79.90
}
```

**Validações:**
- Status code 200
- Echo dos inputs fornecidos
- Predições de performance:
  - `estimativaConversoesPorMilSessoes`
  - `estimativaBounceRate`
  - `estimativaSessionDuration`
- Array de recomendações

---

### 8. `test_predict_simulator_edge_cases`
**Objetivo:** Validar simulador com casos extremos.

**Casos testados:**
1. **Conteúdo mínimo:** 50 palavras, 0 imagens, R$0
2. **Conteúdo extenso:** 5000 palavras, 15 imagens, R$0
3. **Produto caro:** 800 palavras, 8 imagens, R$2500
4. **Produto barato:** 400 palavras, 3 imagens, R$9.99

**Validações:**
- Todos os casos retornam 200
- Predições são números válidos
- Recomendações são geradas

---

### 9. `test_predict_simulator_invalid_input`
**Objetivo:** Validar validação de entrada do simulador.

**Casos testados:**
- Valores negativos
- Campos faltando
- Tipos errados

**Validações:**
- Status code 422 (Unprocessable Entity)
- Mensagem de erro descritiva do Pydantic

---

### 10. `test_openapi_docs`
**Objetivo:** Validar que documentação OpenAPI está acessível.

**Endpoints:**
- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc
- `GET /openapi.json` - Schema OpenAPI

**Validações:**
- Todos retornam 200
- OpenAPI JSON é válido

---

## 🔧 Configuração de Testes

### pytest.ini ou pyproject.toml

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --tb=short"
```

### Fixtures Disponíveis

```python
@pytest.fixture
def client():
    """Cliente de teste FastAPI."""
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)
```

---

## 🐛 Troubleshooting

### Erro: "Tabela não encontrada"
**Solução:** Criar dados de teste
```bash
python tests/create_test_data.py
```

### Erro: "Módulo não encontrado"
**Solução:** Instalar dependências
```bash
pip install -r requirements.txt
```

### Erro: "Porta 8000 em uso"
**Solução:** A API não precisa estar rodando para testes (TestClient)

### Erro: "NaN/Inf values"
**Solução:** Já tratado no código com `fillna(0)` e `safe_float()`

### Testes lentos
**Solução:** Usar pytest-xdist para paralelização
```bash
pip install pytest-xdist
python -m pytest tests/test_api.py -n auto
```

---

## 📊 Coverage Report

### Gerar Coverage

```bash
# Instalar coverage
pip install pytest-cov

# Executar com coverage
python -m pytest tests/test_api.py --cov=app --cov-report=html

# Abrir relatório
# Windows
start htmlcov/index.html

# Linux/Mac
xdg-open htmlcov/index.html
```

### Coverage Esperado
- `app/main.py`: ~95% (todas as rotas testadas)
- `src/collectors/db_storage.py`: ~75% (query_df testado indiretamente)

---

## 🚀 Integração Contínua (CI)

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.12'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Create test data
      run: python tests/create_test_data.py
    
    - name: Run tests
      run: python -m pytest tests/test_api.py -v
    
    - name: Cleanup
      run: echo "sim" | python tests/cleanup_test_data.py
```

---

## ✅ Checklist de Testes

Antes de fazer commit/deploy:

- [ ] Todos os 10 testes passando
- [ ] Dados de teste limpos (`cleanup_test_data.py`)
- [ ] Sem warnings críticos
- [ ] Coverage > 80%
- [ ] Documentação OpenAPI acessível
- [ ] README atualizado

---

## 📚 Recursos Adicionais

- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [pytest Documentation](https://docs.pytest.org/)
- [TestClient API](https://www.starlette.io/testclient/)
- [Pydantic Validation](https://docs.pydantic.dev/latest/concepts/validation/)

---

**Desenvolvido com 🧪 usando pytest + FastAPI TestClient**
