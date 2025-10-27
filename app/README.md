# 🚀 API de Analytics Dashboard

API REST desenvolvida em **FastAPI** para análise de dados do Google Analytics 4 (GA4) e Google Search Console (GSC) com predições baseadas em Machine Learning.

## 📋 Endpoints Disponíveis

### 🏥 Health Check

**GET** `/health`
- Verifica se a API está online
- Resposta: `{"status": "ok"}`

---

### 📊 Dashboard Overview

#### **GET** `/api/v1/overview/kpis`

Retorna os principais KPIs do site para cards do dashboard.

**Resposta:**
```json
{
  "totalPaginas": 1000,
  "sessoesTotais": 5480230,
  "conversoesTotais": 120500,
  "mediaBounceRate": 0.58,
  "mediaSessionDuration": 215.4
}
```

---

### 🔬 Análises Estáticas

#### **GET** `/api/v1/analysis/correlation_matrix`

Retorna matriz de correlação entre features e métricas principais.

**Finalidade:** Mostrar em heatmap o que influencia cada métrica.

**Resposta:**
```json
{
  "conversions": {
    "sessions": 0.55,
    "pageViews": 0.42,
    "avgSessionDuration": 0.30
  },
  "engagementRate": {
    "sessions": 0.38,
    "pageViews": 0.45,
    "avgSessionDuration": 0.75
  },
  "averageSessionDuration": {
    "sessions": 0.22,
    "pageViews": 0.18,
    "conversions": 0.30
  }
}
```

#### **GET** `/api/v1/analysis/page_clusters`

Retorna clusters (arquétipos) de páginas do site.

**Finalidade:** Identificar grupos de páginas similares (ex: "Artigos Longos", "Produtos de Sucesso", "Páginas Problemáticas").

**Resposta:**
```json
{
  "clusters": [
    {
      "clusterId": 0,
      "clusterName": "Páginas de Alto Engajamento e Conversão",
      "avgEngagementRate": 0.75,
      "avgSessionDuration": 420.5,
      "avgConversions": 210,
      "totalPaginas": 300
    },
    {
      "clusterId": 1,
      "clusterName": "Produtos de Sucesso (Boa Conversão)",
      "avgEngagementRate": 0.55,
      "avgSessionDuration": 180.0,
      "avgConversions": 150,
      "totalPaginas": 450
    }
  ]
}
```

---

### 🔍 Análise de Página Específica

#### **GET** `/api/v1/page_analysis?path=/pagina/exemplo`

Retorna análise completa de uma página específica com dados reais + predições.

**Parâmetros:**
- `path` (query): Caminho da página (ex: `/produtos/item-1`)

**Resposta:**
```json
{
  "pagePath": "/produtos/item-1",
  "dadosReais": {
    "sessions": 885,
    "pageViews": 1024,
    "averageSessionDuration": 390.10,
    "engagementRate": 0.68,
    "conversions": 42
  },
  "analisePreditiva": {
    "clusterName": "Produto de Sucesso",
    "riscoDeRejeicao": "Baixo"
  }
}
```

---

### 🤖 Simulador Preditivo (ML)

#### **POST** `/api/v1/predict/simulator`

**⭐ Endpoint mais importante:** Simula a performance esperada de uma nova página antes de publicá-la.

**Finalidade:** Ferramenta de otimização SEO/CRO. Permite testar diferentes cenários de conteúdo.

**Request Body:**
```json
{
  "contagemDePalavras": 1200,
  "numeroDeImagens": 5,
  "precoDoProduto": 79.90
}
```

**Resposta:**
```json
{
  "inputFeatures": {
    "contagemDePalavras": 1200,
    "numeroDeImagens": 5,
    "precoDoProduto": 79.90
  },
  "predictedPerformance": {
    "estimativaEngagementRate": 0.72,
    "estimativaBounceRate": 0.28,
    "estimativaSessionDuration": 310.5,
    "estimativaConversoesPorMilSessoes": 45.2
  },
  "recommendations": [
    "✅ Excelente contagem de palavras para engajamento.",
    "✅ Número adequado de imagens.",
    "💰 Produto de valor médio. Destaque benefícios e diferenciais."
  ]
}
```

---

## 🚀 Como Executar

### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

### 2. Ativar ambiente virtual

```bash
# Windows (bash)
source .venv/Scripts/activate

# Linux/Mac
source .venv/bin/activate
```

### 3. Iniciar servidor

```bash
# Desenvolvimento (com auto-reload)
uvicorn app.main:app --reload

# Produção
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. Acessar documentação interativa

Abra no navegador:
- **Swagger UI:** http://127.0.0.1:8000/docs
- **ReDoc:** http://127.0.0.1:8000/redoc

---

## 🧪 Testes

### Executar suite completa de testes

```bash
pytest tests/test_api.py -v
```

### Executar teste específico

```bash
pytest tests/test_api.py::test_predict_simulator_valid -v
```

### Executar com print outputs

```bash
python tests/test_api.py
```

---

## 📦 Dependências Principais

- **FastAPI:** Framework web assíncrono
- **Pydantic:** Validação de dados
- **DuckDB:** Banco de dados analítico
- **Pandas:** Manipulação de dados
- **Uvicorn:** ASGI server

---

## 🏗️ Arquitetura

```
app/
├── main.py              # Endpoints da API (FastAPI)
├── __init__.py

src/
├── collectors/
│   └── db_storage.py    # Conexão com DuckDB (backend)

tests/
├── test_api.py          # Testes automatizados

data/
└── processed/
    └── ga4_data.duckdb  # Banco de dados
```

### Fluxo de Dados

1. **Frontend (React)** → Faz requisição HTTP para API
2. **FastAPI** → Processa request e valida input
3. **db_storage.py** → Executa queries SQL no DuckDB
4. **DuckDB** → Retorna dados agregados
5. **FastAPI** → Aplica lógica ML/heurísticas
6. **FastAPI** → Retorna JSON formatado para frontend

---

## 🔧 Configuração

### CORS

Por padrão, a API aceita requisições de qualquer origem (`allow_origins=["*"]`).

Para produção, configure origens específicas em `app/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://seudominio.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Banco de Dados

O caminho padrão do banco é `data/processed/ga4_data.duckdb`.

Para alterar, modifique em `app/main.py`:

```python
db = GA4DatabaseStorage(db_path="outro/caminho/banco.duckdb")
```

---

## 📈 Uso no Frontend

### Exemplo: Buscar KPIs (React)

```javascript
// App.jsx
import { useEffect, useState } from 'react';

function Dashboard() {
  const [kpis, setKpis] = useState(null);

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/overview/kpis')
      .then(res => res.json())
      .then(data => setKpis(data))
      .catch(err => console.error(err));
  }, []);

  if (!kpis) return <div>Loading...</div>;

  return (
    <div>
      <h1>Dashboard</h1>
      <div className="kpi-cards">
        <Card title="Páginas" value={kpis.totalPaginas} />
        <Card title="Sessões" value={kpis.sessoesTotais} />
        <Card title="Conversões" value={kpis.conversoesTotais} />
        <Card title="Bounce Rate" value={`${(kpis.mediaBounceRate * 100).toFixed(1)}%`} />
      </div>
    </div>
  );
}
```

### Exemplo: Simulador (React)

```javascript
function Simulator() {
  const [result, setResult] = useState(null);

  const handleSimulate = async (e) => {
    e.preventDefault();
    
    const payload = {
      contagemDePalavras: parseInt(e.target.palavras.value),
      numeroDeImagens: parseInt(e.target.imagens.value),
      precoDoProduto: parseFloat(e.target.preco.value)
    };

    const response = await fetch('http://localhost:8000/api/v1/predict/simulator', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await response.json();
    setResult(data);
  };

  return (
    <form onSubmit={handleSimulate}>
      <input type="number" name="palavras" placeholder="Palavras" />
      <input type="number" name="imagens" placeholder="Imagens" />
      <input type="number" step="0.01" name="preco" placeholder="Preço" />
      <button type="submit">Simular</button>

      {result && (
        <div>
          <h3>Resultado:</h3>
          <p>Engagement: {(result.predictedPerformance.estimativaEngagementRate * 100).toFixed(1)}%</p>
          <p>Bounce: {(result.predictedPerformance.estimativaBounceRate * 100).toFixed(1)}%</p>
          <ul>
            {result.recommendations.map((rec, i) => <li key={i}>{rec}</li>)}
          </ul>
        </div>
      )}
    </form>
  );
}
```

---

## 🐛 Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'src'"

**Solução:** Certifique-se de estar executando do diretório raiz do projeto.

```bash
cd "/c/Users/guguo/OneDrive/Área de Trabalho/trabalho_A2"
uvicorn app.main:app --reload
```

### Erro: "DuckDB não instalado"

**Solução:**
```bash
pip install duckdb
```

### Erro: "Table 'traffic' does not exist"

**Solução:** Execute scripts de coleta para popular o banco:

```bash
python scripts/exemplo_coleta_ga4.py
```

### API retorna todos os valores zerados

**Causa:** Banco de dados vazio (sem coletas).

**Solução:** Gerar dados de teste ou executar coleta real:

```bash
# Dados simulados
python scripts/gerar_dados_teste.py

# Coleta real (requer configuração)
python scripts/exemplo_coleta_ga4.py
```

---

## 📝 Próximos Passos

- [ ] Implementar cache (Redis) para queries pesadas
- [ ] Adicionar autenticação JWT
- [ ] Criar endpoint para análise combinada GA4 + GSC
- [ ] Implementar rate limiting
- [ ] Deploy em Docker/Cloud
- [ ] Integrar modelos ML reais (scikit-learn)

---

## 📄 Licença

MIT License
