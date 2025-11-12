# 📘 Documentação Completa da API - Para Desenvolvimento Frontend

## 🎯 Visão Geral da API

Esta é uma **API REST de Analytics** construída com FastAPI que fornece dados de marketing digital, análises de Machine Learning e relatórios narrativos gerados por IA (GPT-4o-mini via Agno).

**Base URL (Produção):** `https://siteup.onrender.com`  
**Swagger Docs:** `https://siteup.onrender.com/docs`

---

## 📊 Estrutura de Dados

### Dados Disponíveis

A API trabalha com dados de:
- **Google Analytics 4 (GA4)**: Tráfego, engagement, conversões
- **Google Search Console (GSC)**: Keywords, impressões, cliques, CTR, posições
- **Machine Learning**: Clusters de canais, keywords e páginas (K-Means)

### Período de Dados

- Dados históricos configuráveis (1 a 365 dias)
- Gerados sob demanda via endpoint administrativo
- Dados agregados por data para análise temporal

---

## 🔗 Lista Completa de Endpoints

### 1. KPIs Principais
### 2. Matriz de Correlação
### 3. Análise de Canais (ML)
### 4. Análise de Keywords (ML)
### 5. Análise de Páginas (ML)
### 6. Análise de Página Específica
### 7. Simulador de Performance
### 8. Dados Brutos Completos
### 9. Resumo de Dados
### 10. Relatórios Narrativos com IA ⭐

---

## 📍 ENDPOINT 1: KPIs Principais

**Propósito:** Obter métricas principais de performance do site (sessões, conversões, bounce rate, etc).

**Método:** `GET`  
**URL:** `/api/v1/overview/kpis`  
**Autenticação:** Não requerida

### Request
```http
GET https://siteup.onrender.com/api/v1/overview/kpis HTTP/1.1
```

### Response (200 OK)
```json
{
  "totalPaginas": 9,
  "sessoesTotais": 31099,
  "conversoesTotais": 94652,
  "mediaBounceRate": 27.0,
  "mediaSessionDuration": 108.9
}
```

### Campos Explicados

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `totalPaginas` | number | Total de páginas únicas visitadas |
| `sessoesTotais` | number | Total de sessões no período |
| `conversoesTotais` | number | Total de conversões no período |
| `mediaBounceRate` | number | Taxa média de rejeição (0-1, multiplicar por 100 para %) |
| `mediaSessionDuration` | number | Duração média de sessão em segundos |

### Quando Usar no Frontend
- **Dashboard principal** (cards com KPIs)
- Resumo executivo no topo
- Comparação entre períodos

### Exemplo React
```jsx
function DashboardKPIs() {
  const [kpis, setKpis] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('https://siteup.onrender.com/api/v1/overview/kpis')
      .then(res => res.json())
      .then(data => {
        setKpis(data);
        setLoading(false);
      });
  }, []);

  if (loading) return <Spinner />;

  return (
    <div className="kpi-grid">
      <KPICard 
        title="Páginas" 
        value={kpis.totalPaginas} 
        icon="📄"
      />
      <KPICard 
        title="Sessões" 
        value={kpis.sessoesTotais.toLocaleString()} 
        icon="👥"
      />
      <KPICard 
        title="Conversões" 
        value={kpis.conversoesTotais.toLocaleString()} 
        icon="🎯"
      />
      <KPICard 
        title="Bounce Rate" 
        value={`${(kpis.mediaBounceRate * 100).toFixed(1)}%`} 
        icon="⚡"
      />
      <KPICard 
        title="Duração Média" 
        value={`${Math.round(kpis.mediaSessionDuration)}s`} 
        icon="⏱️"
      />
    </div>
  );
}
```

---

## 📍 ENDPOINT 2: Matriz de Correlação

**Propósito:** Obter correlações estatísticas entre métricas agregadas por data.

**Método:** `GET`  
**URL:** `/api/v1/analysis/correlation_matrix`  
**Autenticação:** Não requerida

### Request
```http
GET https://siteup.onrender.com/api/v1/analysis/correlation_matrix HTTP/1.1
```

### Response (200 OK)
```json
{
  "conversions": {
    "sessions": 0.87,
    "pageViews": 0.92,
    "avgSessionDuration": 0.45
  },
  "engagementRate": {
    "sessions": 0.34,
    "pageViews": 0.56,
    "avgSessionDuration": 0.68
  },
  "averageSessionDuration": {
    "sessions": 0.23,
    "pageViews": 0.41,
    "conversions": 0.45
  }
}
```

### Campos Explicados

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `conversions` | object | Correlações de conversões com outras métricas |
| `engagementRate` | object | Correlações de engagement com outras métricas |
| `averageSessionDuration` | object | Correlações de duração com outras métricas |
| Valores | number | -1 a 1 (negativo = inverso, positivo = direto, 0 = sem correlação) |

**Interpretação:**
- `> 0.7`: Correlação forte
- `0.3 a 0.7`: Correlação moderada
- `< 0.3`: Correlação fraca
- Valor negativo: relação inversa (uma aumenta, outra diminui)

### Quando Usar no Frontend
- **Página de Insights Estatísticos**
- Heatmap de correlações
- Identificação de relações entre métricas

### Exemplo React
```jsx
function CorrelationMatrix() {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetch('https://siteup.onrender.com/api/v1/analysis/correlation_matrix')
      .then(res => res.json())
      .then(setData);
  }, []);

  if (!data) return <Loading />;

  const getStrength = (value) => {
    const abs = Math.abs(value);
    if (abs > 0.7) return { text: 'Forte', color: 'green' };
    if (abs > 0.3) return { text: 'Moderada', color: 'yellow' };
    return { text: 'Fraca', color: 'red' };
  };

  return (
    <div>
      <h1>🔗 Matriz de Correlação</h1>
      
      <section>
        <h2>Conversões</h2>
        <CorrelationCard>
          <Metric 
            label="vs Sessões" 
            value={data.conversions.sessions.toFixed(2)}
            strength={getStrength(data.conversions.sessions)}
          />
          <Metric 
            label="vs Page Views" 
            value={data.conversions.pageViews.toFixed(2)}
            strength={getStrength(data.conversions.pageViews)}
          />
          <Metric 
            label="vs Duração" 
            value={data.conversions.avgSessionDuration.toFixed(2)}
            strength={getStrength(data.conversions.avgSessionDuration)}
          />
        </CorrelationCard>
      </section>
      
      <section>
        <h2>Engagement Rate</h2>
        <CorrelationCard>
          <Metric 
            label="vs Sessões" 
            value={data.engagementRate.sessions.toFixed(2)}
            strength={getStrength(data.engagementRate.sessions)}
          />
          <Metric 
            label="vs Page Views" 
            value={data.engagementRate.pageViews.toFixed(2)}
            strength={getStrength(data.engagementRate.pageViews)}
          />
          <Metric 
            label="vs Duração" 
            value={data.engagementRate.avgSessionDuration.toFixed(2)}
            strength={getStrength(data.engagementRate.avgSessionDuration)}
          />
        </CorrelationCard>
      </section>
    </div>
  );
}
```

---

## 📍 ENDPOINT 3: Análise de Canais (Machine Learning)

**Propósito:** Obter clusters de canais de tráfego agrupados por Machine Learning (K-Means).

**Método:** `GET`  
**URL:** `/api/v1/ml/channel_clusters`  
**Autenticação:** Não requerida

### Query Parameters

| Parâmetro | Tipo | Obrigatório | Padrão | Descrição |
|-----------|------|-------------|--------|-----------|
| `n_clusters` | number | Não | 3 | Número de clusters (2-10) |

### Request
```http
GET https://siteup.onrender.com/api/v1/ml/channel_clusters?n_clusters=3 HTTP/1.1
```

### Response (200 OK)
```json
{
  "algoritmo": "K-Means Clustering",
  "n_clusters": 3,
  "total_canais": 25,
  "canais": [
    {
      "source": "google",
      "medium": "organic",
      "sessions": 15234,
      "cluster": 0
    },
    {
      "source": "facebook",
      "medium": "social",
      "sessions": 8901,
      "cluster": 1
    }
  ],
  "cluster_centers": [
    {
      "cluster": 0,
      "sessions_mean": 12500.5,
      "activeUsers_mean": 10234.2,
      "newUsers_mean": 8901.3
    }
  ],
  "segment_summary": [
    {
      "cluster": 0,
      "count": 8,
      "sessions_sum": 100004,
      "activeUsers_sum": 81873,
      "performance_level": "high"
    }
  ]
}
```

### Campos Explicados

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `canais` | array | Lista de canais com cluster_id atribuído |
| `cluster_centers` | array | Centros dos clusters (médias das features) |
| `segment_summary` | array | Resumo estatístico por cluster |
| `performance_level` | string | high, medium, low (baseado em métricas) |

### Quando Usar no Frontend
- **Página de Análise de Canais**
- Visualização de clusters em gráfico (scatter plot, bar chart)
- Tabela comparativa de canais
- Recomendações de budget allocation

### Exemplo React
```jsx
function ChannelClusters() {
  const [data, setData] = useState(null);
  const [nClusters, setNClusters] = useState(3);

  const fetchData = () => {
    fetch(`https://siteup.onrender.com/api/v1/ml/channel_clusters?n_clusters=${nClusters}`)
      .then(res => res.json())
      .then(setData);
  };

  useEffect(() => {
    fetchData();
  }, [nClusters]);

  if (!data) return <Loading />;

  return (
    <div>
      <h1>📊 Análise de Canais (Machine Learning)</h1>
      
      <ClusterSelector 
        value={nClusters}
        onChange={setNClusters}
        min={2}
        max={10}
      />

      <p>Algoritmo: {data.algoritmo} | Total de canais: {data.total_canais}</p>

      {data.segment_summary.map(segment => (
        <ClusterCard key={segment.cluster}>
          <h3>Cluster {segment.cluster}</h3>
          <Badge level={segment.performance_level}>{segment.performance_level}</Badge>
          <p><strong>Canais:</strong> {segment.count}</p>
          <p><strong>Sessões:</strong> {segment.sessions_sum.toLocaleString()}</p>
          
          <h4>Canais neste cluster:</h4>
          <ul>
            {data.canais
              .filter(c => c.cluster === segment.cluster)
              .map(c => (
                <li key={`${c.source}/${c.medium}`}>
                  {c.source}/{c.medium} ({c.sessions.toLocaleString()} sessões)
                </li>
              ))}
          </ul>
        </ClusterCard>
      ))}
    </div>
  );
}
```

---

## 📍 ENDPOINT 4: Análise de Keywords (Machine Learning)

**Propósito:** Obter clusters de keywords agrupadas por performance (dados do Google Search Console).

**Método:** `GET`  
**URL:** `/api/v1/ml/keyword_clusters`  
**Autenticação:** Não requerida

### Query Parameters

| Parâmetro | Tipo | Obrigatório | Padrão | Descrição |
|-----------|------|-------------|--------|-----------|
| `n_clusters` | number | Não | 3 | Número de clusters (2-10) |

### Request
```http
GET https://siteup.onrender.com/api/v1/ml/keyword_clusters?n_clusters=3 HTTP/1.1
```

### Response (200 OK)
```json
{
  "algoritmo": "K-Means Clustering",
  "n_clusters": 3,
  "total_queries": 150,
  "queries": [
    {
      "query": "analytics dashboard",
      "clicks": 1250,
      "impressions": 15000,
      "ctr": 8.33,
      "position": 3.2,
      "cluster": 0
    }
  ],
  "cluster_centers": [
    {
      "cluster": 0,
      "clicks_mean": 1100.5,
      "impressions_mean": 12500.3,
      "ctr_mean": 8.8,
      "position_mean": 3.5
    }
  ],
  "segment_summary": [
    {
      "cluster": 0,
      "count": 45,
      "clicks_sum": 49522,
      "impressions_sum": 562635,
      "intent_category": "transactional"
    }
  ]
}
```

### Campos Explicados

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `query` | string | Termo de busca (keyword) |
| `clicks` | number | Número de cliques recebidos |
| `impressions` | number | Número de vezes que apareceu no Google |
| `ctr` | number | Click-Through Rate (%) |
| `position` | number | Posição média no Google (1 = primeiro) |
| `intent_category` | string | transactional, informational, navigational |

### Quando Usar no Frontend
- **Página de SEO / Keywords**
- Tabela de keywords com filtros
- Gráfico de CTR vs Posição
- Oportunidades de otimização

### Exemplo React
```jsx
function KeywordClusters() {
  const [data, setData] = useState(null);
  const [nClusters, setNClusters] = useState(3);

  useEffect(() => {
    fetch(`https://siteup.onrender.com/api/v1/ml/keyword_clusters?n_clusters=${nClusters}`)
      .then(res => res.json())
      .then(setData);
  }, [nClusters]);

  if (!data) return <Loading />;

  return (
    <div>
      <h1>🔍 Análise de Keywords (GSC + ML)</h1>
      
      <ClusterSelector 
        value={nClusters}
        onChange={setNClusters}
        min={2}
        max={10}
      />

      <p>Total de queries: {data.total_queries}</p>

      {data.segment_summary.map(segment => (
        <ClusterCard key={segment.cluster}>
          <h3>Cluster {segment.cluster}</h3>
          <Badge>{segment.intent_category}</Badge>
          <p><strong>Keywords:</strong> {segment.count}</p>
          <p><strong>Cliques:</strong> {segment.clicks_sum.toLocaleString()}</p>
          <p><strong>Impressões:</strong> {segment.impressions_sum.toLocaleString()}</p>
          
          <KeywordsTable>
            <thead>
              <tr>
                <th>Query</th>
                <th>Cliques</th>
                <th>CTR</th>
                <th>Posição</th>
              </tr>
            </thead>
            <tbody>
              {data.queries
                .filter(q => q.cluster === segment.cluster)
                .slice(0, 10)
                .map(q => (
                  <tr key={q.query}>
                    <td>{q.query}</td>
                    <td>{q.clicks.toLocaleString()}</td>
                    <td>{q.ctr.toFixed(2)}%</td>
                    <td>{q.position.toFixed(1)}</td>
                  </tr>
                ))}
            </tbody>
          </KeywordsTable>
        </ClusterCard>
      ))}
    </div>
  );
}
```

---

## 📍 ENDPOINT 5: Análise de Páginas (Machine Learning)

**Propósito:** Obter clusters de páginas agrupadas por performance de engagement.

**Método:** `GET`  
**URL:** `/api/v1/ml/page_clusters`  
**Autenticação:** Não requerida

### Query Parameters

| Parâmetro | Tipo | Obrigatório | Padrão | Descrição |
|-----------|------|-------------|--------|-----------|
| `n_clusters` | number | Não | 5 | Número de clusters (2-10) |

### Request
```http
GET https://siteup.onrender.com/api/v1/ml/page_clusters?n_clusters=5 HTTP/1.1
```

### Response (200 OK)
```json
{
  "algoritmo": "K-Means Clustering",
  "n_clusters": 5,
  "total_paginas": 9,
  "paginas": [
    {
      "page_path": "/landing/promo",
      "engagement_rate": 0.85,
      "event_count": 2500,
      "average_session_duration": 245.3,
      "cluster": 0
    }
  ],
  "cluster_centers": [
    {
      "cluster": 0,
      "engagement_rate_mean": 0.82,
      "event_count_mean": 2200.5,
      "average_session_duration_mean": 230.1
    }
  ],
  "segment_summary": [
    {
      "cluster": 0,
      "count": 2,
      "engagement_rate_mean": 0.82,
      "event_count_sum": 4401,
      "performance_level": "excellent"
    }
  ]
}
```

### Campos Explicados

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `page_path` | string | URL/path da página |
| `engagement_rate` | number | Taxa de engajamento (0-1) |
| `event_count` | number | Total de eventos na página |
| `average_session_duration` | number | Duração média na página (segundos) |
| `performance_level` | string | excellent, good, needs_improvement |

### Quando Usar no Frontend
- **Página de Análise de Conteúdo**
- Ranking de páginas por performance
- Identificação de páginas problemáticas

### Exemplo React
```jsx
function PageClusters() {
  const [data, setData] = useState(null);
  const [nClusters, setNClusters] = useState(5);

  useEffect(() => {
    fetch(`https://siteup.onrender.com/api/v1/ml/page_clusters?n_clusters=${nClusters}`)
      .then(res => res.json())
      .then(setData);
  }, [nClusters]);

  if (!data) return <Loading />;

  // Flatten e ordenar páginas
  const allPages = data.paginas
    .map(p => ({
      ...p,
      cluster_level: data.segment_summary.find(s => s.cluster === p.cluster)?.performance_level
    }))
    .sort((a, b) => b.engagement_rate - a.engagement_rate);

  return (
    <div>
      <h1>📄 Análise de Páginas (ML)</h1>
      
      <ClusterSelector 
        value={nClusters}
        onChange={setNClusters}
        min={2}
        max={10}
      />

      <p>Total de páginas: {data.total_paginas}</p>

      <Table>
        <thead>
          <tr>
            <th>Página</th>
            <th>Cluster</th>
            <th>Engagement</th>
            <th>Eventos</th>
            <th>Duração</th>
          </tr>
        </thead>
        <tbody>
          {allPages.map(page => (
            <tr key={page.page_path}>
              <td>{page.page_path}</td>
              <td>
                <Badge level={page.cluster_level}>
                  Cluster {page.cluster}
                </Badge>
              </td>
              <td>{(page.engagement_rate * 100).toFixed(1)}%</td>
              <td>{page.event_count.toLocaleString()}</td>
              <td>{Math.round(page.average_session_duration)}s</td>
            </tr>
          ))}
        </tbody>
      </Table>
    </div>
  );
}
```

---

## 📍 ENDPOINT 6: Análise de Página Específica

**Propósito:** Obter análise detalhada de uma página específica.

**Método:** `GET`  
**URL:** `/api/v1/page_analysis`  
**Autenticação:** Não requerida

### Query Parameters

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|------------|-----------|
| `path` | string | Sim | Caminho da página (ex: `/produtos/item-1`) |

### Request
```http
GET https://siteup.onrender.com/api/v1/page_analysis?path=/landing/promo HTTP/1.1
```

### Response (200 OK)
```json
{
  "page_path": "/landing/promo",
  "engagement_metrics": {
    "engagement_rate": 0.85,
    "event_count": 2500,
    "average_session_duration": 245.3,
    "engaged_sessions": 2125
  },
  "traffic_sources": [
    {
      "source": "google",
      "medium": "organic",
      "sessions": 1234
    }
  ],
  "performance_classification": "high_performer",
  "recommendations": [
    "✅ Excelente engagement rate (85%)",
    "💡 Replicar elementos desta página em outras landing pages"
  ]
}
```

### Quando Usar no Frontend
- **Página de detalhes de uma página**
- Drill-down após clicar em uma página na tabela
- Análise detalhada de performance

---

## 📍 ENDPOINT 7: Simulador de Performance

**Propósito:** Prever performance de uma página baseado em características de conteúdo.

**Método:** `POST`  
**URL:** `/api/v1/predict/simulator`  
**Autenticação:** Não requerida

### Request Body

```json
{
  "contagemDePalavras": 1200,
  "numeroDeImagens": 5,
  "precoDoProduto": 299.90
}
```

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `contagemDePalavras` | number | Sim | Número de palavras no conteúdo |
| `numeroDeImagens` | number | Sim | Quantidade de imagens na página |
| `precoDoProduto` | number | Sim | Preço do produto (0 se não aplicável) |

### Request
```http
POST https://siteup.onrender.com/api/v1/predict/simulator HTTP/1.1
Content-Type: application/json

{
  "contagemDePalavras": 1200,
  "numeroDeImagens": 5,
  "precoDoProduto": 299.90
}
```

### Response (200 OK)
```json
{
  "inputFeatures": {
    "contagemDePalavras": 1200,
    "numeroDeImagens": 5,
    "precoDoProduto": 299.90
  },
  "predictedPerformance": {
    "estimativaEngagementRate": 0.75,
    "estimativaBounceRate": 0.25,
    "estimativaSessionDuration": 216.0,
    "estimativaConversoesPorMilSessoes": 18.5
  },
  "recommendations": [
    "✅ Excelente contagem de palavras para engajamento.",
    "✅ Número adequado de imagens.",
    "💰 Produto de valor médio. Destaque benefícios e diferenciais."
  ]
}
```

### Quando Usar no Frontend
- **Página de Otimização de Conteúdo**
- Ferramenta "Preditor de Performance"
- Planejamento de novas landing pages

### Exemplo React
```jsx
function PageSimulator() {
  const [input, setInput] = useState({
    contagemDePalavras: 1000,
    numeroDeImagens: 3,
    precoDoProduto: 0
  });
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSimulate = async () => {
    setLoading(true);
    
    const response = await fetch('https://siteup.onrender.com/api/v1/predict/simulator', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input)
    });
    
    const data = await response.json();
    setPrediction(data);
    setLoading(false);
  };

  return (
    <div>
      <h1>🎯 Simulador de Performance de Página</h1>
      
      <form>
        <Input 
          label="Contagem de Palavras"
          type="number"
          value={input.contagemDePalavras}
          onChange={v => setInput({...input, contagemDePalavras: v})}
        />
        
        <Input 
          label="Número de Imagens"
          type="number"
          value={input.numeroDeImagens}
          onChange={v => setInput({...input, numeroDeImagens: v})}
        />
        
        <Input 
          label="Preço do Produto (R$)"
          type="number"
          step="0.01"
          value={input.precoDoProduto}
          onChange={v => setInput({...input, precoDoProduto: v})}
        />
        
        <Button onClick={handleSimulate} disabled={loading}>
          {loading ? 'Simulando...' : '🚀 Simular Performance'}
        </Button>
      </form>

      {prediction && (
        <ResultCard>
          <h2>📊 Predição</h2>
          <MetricsGrid>
            <Metric 
              label="Engagement Rate" 
              value={`${(prediction.predictedPerformance.estimativaEngagementRate * 100).toFixed(1)}%`} 
            />
            <Metric 
              label="Bounce Rate" 
              value={`${(prediction.predictedPerformance.estimativaBounceRate * 100).toFixed(1)}%`} 
            />
            <Metric 
              label="Duração" 
              value={`${Math.round(prediction.predictedPerformance.estimativaSessionDuration)}s`} 
            />
            <Metric 
              label="Conversões/1K" 
              value={prediction.predictedPerformance.estimativaConversoesPorMilSessoes.toFixed(1)} 
            />
          </MetricsGrid>
          
          <h3>💡 Recomendações</h3>
          <ul>
            {prediction.recommendations.map((rec, i) => (
              <li key={i}>{rec}</li>
            ))}
          </ul>
        </ResultCard>
      )}
    </div>
  );
}
```

---

## 📍 ENDPOINT 8: Dados Brutos Completos

**Propósito:** Obter todos os dados brutos das 4 tabelas (tráfego, engagement, conversões, GSC).

**Método:** `GET`  
**URL:** `/api/v1/data/all`  
**Autenticação:** Não requerida

### Request
```http
GET https://siteup.onrender.com/api/v1/data/all HTTP/1.1
```

### Response (200 OK)
```json
{
  "traffic": [...],
  "engagement": [...],
  "conversions": [...],
  "gsc_query_performance": [...]
}
```

### Quando Usar no Frontend
- **Página de exploração de dados**
- Exportação de dados brutos
- Tabelas com paginação e filtros
- Download CSV/Excel

---

## 📍 ENDPOINT 9: Resumo de Dados

**Propósito:** Obter resumo estatístico de cada tabela (contagens, médias, min/max).

**Método:** `GET`  
**URL:** `/api/v1/data/summary`  
**Autenticação:** Não requerida

### Request
```http
GET https://siteup.onrender.com/api/v1/data/summary HTTP/1.1
```

### Response (200 OK)
```json
{
  "traffic": {
    "total_records": 1864,
    "total_sessions": 31099,
    "avg_session_duration": 108.9,
    "date_range": {
      "min": "2024-09-23",
      "max": "2024-11-11"
    }
  },
  "engagement": {...},
  "conversions": {...},
  "gsc_query_performance": {...}
}
```

### Quando Usar no Frontend
- **Dashboard de Admin**
- Status do banco de dados
- Verificação de dados antes de análises

---

## 📍 ENDPOINT 10: Relatórios Narrativos com IA ⭐ (PRINCIPAL)

**Propósito:** Gerar relatório executivo completo com análise narrativa gerada por GPT-4o-mini.

**Método:** `POST`  
**URL:** `/api/v1/reports/generate`  
**Autenticação:** Não requerida (requer `OPENAI_API_KEY` configurada no servidor)

### Request Body

```json
{
  "period_days": 7,
  "detail_level": "executive",
  "focus_areas": ["conversions", "traffic"],
  "language": "pt-br"
}
```

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `period_days` | number | Sim | Período de análise em dias (1-365) |
| `detail_level` | string | Sim | executive, technical, detailed |
| `focus_areas` | string[] | Não | conversions, traffic, engagement, keywords, seo |
| `language` | string | Não | pt-br, en-us (padrão: pt-br) |

### Request
```http
POST https://siteup.onrender.com/api/v1/reports/generate HTTP/1.1
Content-Type: application/json

{
  "period_days": 7,
  "detail_level": "executive"
}
```

### Response (200 OK)
```json
{
  "report_id": "0dacc08d-f248-49e9-a9fc-6c019a2e759f",
  "generated_at": "2025-11-11T22:00:47.749622",
  "period": {
    "start_date": "2025-11-04",
    "end_date": "2025-11-11",
    "days": 7
  },
  "executive_summary": "Análise do período de 7 dias... [texto gerado pela IA]",
  "sections": [
    {
      "title": "Visão Geral de Performance 🎯",
      "content": "Durante o período analisado... [análise detalhada]",
      "key_insights": [
        "94.652 conversões com 31.099 sessões indica múltiplas conversões por sessão",
        "Taxa de rejeição de 27% está abaixo da média do setor"
      ]
    }
  ],
  "recommendations": [
    {
      "priority": "high",
      "category": "conversions",
      "action": "Executar auditoria completa de tracking de conversões",
      "rationale": "Taxa de conversão anormalmente alta indica possível erro de implementação"
    }
  ],
  "metadata": {
    "data_sources": ["kpis", "channel_clusters", "keyword_clusters"],
    "ml_models_used": ["channel_profiling", "keyword_clustering"],
    "agent_model": "gpt-4o-mini",
    "confidence_score": 0.75,
    "generation_timestamp": "2025-11-11T22:00:47.749622"
  }
}
```

### Response Explicado

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `report_id` | string (UUID) | ID único do relatório |
| `generated_at` | string (ISO 8601) | Data/hora de geração |
| `executive_summary` | string | Resumo executivo narrativo |
| `sections` | array | 5-6 seções detalhadas de análise |
| `sections[].title` | string | Título da seção com emoji |
| `sections[].content` | string | Análise narrativa (markdown) |
| `sections[].key_insights` | string[] | 2-4 insights principais |
| `recommendations` | array | 5-8 recomendações priorizadas |
| `recommendations[].priority` | string | high, medium, low |
| `recommendations[].category` | string | conversions, traffic, engagement, keywords, seo |
| `recommendations[].action` | string | Ação específica a tomar |
| `recommendations[].rationale` | string | Justificativa da recomendação |
| `metadata.confidence_score` | number | 0.0 a 1.0 (confiabilidade da análise) |

### Quando Usar no Frontend
- **Página de Relatórios** (principal)
- Dashboard executivo
- Email reports automáticos
- Export PDF

### Exemplo React
```jsx
function ReportsPage() {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [config, setConfig] = useState({
    period_days: 7,
    detail_level: 'executive'
  });

  const generateReport = async () => {
    setLoading(true);
    
    const response = await fetch('https://siteup.onrender.com/api/v1/reports/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
    
    const data = await response.json();
    setReport(data);
    setLoading(false);
  };

  return (
    <div>
      <h1>📊 Relatórios com IA</h1>
      
      <ConfigPanel>
        <Select 
          label="Período"
          options={[
            { value: 7, label: 'Últimos 7 dias' },
            { value: 30, label: 'Últimos 30 dias' },
            { value: 90, label: 'Últimos 90 dias' }
          ]}
          value={config.period_days}
          onChange={v => setConfig({...config, period_days: v})}
        />
        
        <Button onClick={generateReport} disabled={loading}>
          {loading ? '⏳ Gerando... (10-30s)' : '🚀 Gerar Relatório'}
        </Button>
      </ConfigPanel>

      {loading && (
        <LoadingState>
          <Spinner />
          <p>Analisando dados e gerando insights com GPT-4o-mini...</p>
          <p>Isso pode levar 10-30 segundos...</p>
        </LoadingState>
      )}

      {report && (
        <ReportView>
          <ReportHeader>
            <h2>Relatório Executivo</h2>
            <p>Período: {report.period.start_date} a {report.period.end_date}</p>
            <ConfidenceBadge score={report.metadata.confidence_score} />
          </ReportHeader>

          <ExecutiveSummary>
            <h3>📋 Resumo Executivo</h3>
            <ReactMarkdown>{report.executive_summary}</ReactMarkdown>
          </ExecutiveSummary>

          {report.sections.map((section, i) => (
            <Section key={i}>
              <h3>{section.title}</h3>
              <ReactMarkdown>{section.content}</ReactMarkdown>
              
              {section.key_insights && (
                <InsightsBox>
                  <h4>💡 Insights Principais</h4>
                  <ul>
                    {section.key_insights.map((insight, j) => (
                      <li key={j}>{insight}</li>
                    ))}
                  </ul>
                </InsightsBox>
              )}
            </Section>
          ))}

          <RecommendationsSection>
            <h3>🎯 Recomendações</h3>
            
            {['high', 'medium', 'low'].map(priority => {
              const recs = report.recommendations.filter(r => r.priority === priority);
              if (recs.length === 0) return null;
              
              return (
                <PriorityGroup key={priority}>
                  <h4>
                    <PriorityBadge priority={priority} />
                    {priority === 'high' ? 'Alta Prioridade' : 
                     priority === 'medium' ? 'Média Prioridade' : 
                     'Baixa Prioridade'}
                  </h4>
                  
                  {recs.map((rec, i) => (
                    <RecommendationCard key={i}>
                      <Badge>{rec.category}</Badge>
                      <h5>{rec.action}</h5>
                      <p><strong>Justificativa:</strong> {rec.rationale}</p>
                    </RecommendationCard>
                  ))}
                </PriorityGroup>
              );
            })}
          </RecommendationsSection>
        </ReportView>
      )}
    </div>
  );
}
```

---

## 🎨 Arquitetura Frontend Sugerida

### Páginas Recomendadas

```
/
├── /dashboard              → KPIs (GET /api/v1/overview/kpis)
├── /channels               → Canais (GET /api/v1/ml/channel_clusters)
├── /keywords               → Keywords (GET /api/v1/ml/keyword_clusters)
├── /pages                  → Páginas (GET /api/v1/ml/page_clusters)
├── /correlations           → Correlações (GET /api/v1/analysis/correlation_matrix)
├── /simulator              → Simulador (POST /api/v1/predict/simulator)
├── /reports                → Relatórios IA (POST /api/v1/reports/generate) ⭐
└── /data                   → Dados brutos (GET /api/v1/data/all)
```

### Service API (api.js)

```javascript
const API_BASE_URL = 'https://siteup.onrender.com';

export const api = {
  // KPIs
  getKPIs: () => 
    fetch(`${API_BASE_URL}/api/v1/overview/kpis`).then(r => r.json()),
  
  // Correlations
  getCorrelationMatrix: () => 
    fetch(`${API_BASE_URL}/api/v1/analysis/correlation_matrix`).then(r => r.json()),
  
  // ML Clusters
  getChannelClusters: (nClusters = 3) => 
    fetch(`${API_BASE_URL}/api/v1/ml/channel_clusters?n_clusters=${nClusters}`).then(r => r.json()),
  
  getKeywordClusters: (nClusters = 3) => 
    fetch(`${API_BASE_URL}/api/v1/ml/keyword_clusters?n_clusters=${nClusters}`).then(r => r.json()),
  
  getPageClusters: (nClusters = 5) => 
    fetch(`${API_BASE_URL}/api/v1/ml/page_clusters?n_clusters=${nClusters}`).then(r => r.json()),
  
  // Page Analysis
  getPageAnalysis: (path) => 
    fetch(`${API_BASE_URL}/api/v1/page_analysis?path=${encodeURIComponent(path)}`).then(r => r.json()),
  
  // Simulator
  simulatePagePerformance: (data) => 
    fetch(`${API_BASE_URL}/api/v1/predict/simulator`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json()),
  
  // Data
  getAllData: () => 
    fetch(`${API_BASE_URL}/api/v1/data/all`).then(r => r.json()),
  
  getDataSummary: () => 
    fetch(`${API_BASE_URL}/api/v1/data/summary`).then(r => r.json()),
  
  // Reports (IA)
  generateReport: (config) =>
    fetch(`${API_BASE_URL}/api/v1/reports/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    }).then(r => r.json())
};
```

---

## 🔐 Segurança e CORS

### CORS Configurado

A API aceita requisições de **qualquer origem**:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Autenticação

Todos os endpoints disponíveis para o frontend **não requerem autenticação**.

---

## ⚡ Performance e Limites

### Timeouts
- Endpoints rápidos (KPIs, clusters): < 1 segundo
- **Relatórios com IA**: 10-30 segundos (API OpenAI)
- Popular banco: 5-15 segundos

### Rate Limiting
Não implementado

---

## 🐛 Tratamento de Erros

### Códigos de Status

| Código | Significado | Quando Acontece |
|--------|-------------|-----------------|
| 200 | Success | Requisição bem-sucedida |
| 400 | Bad Request | Dados inválidos ou insuficientes |
| 403 | Forbidden | ADMIN_KEY inválida |
| 500 | Internal Server Error | Erro no servidor/banco |

### Formato de Erro
```json
{
  "detail": "Mensagem de erro descritiva"
}
```

### Tratamento no Frontend
```javascript
async function fetchWithErrorHandling(url, options) {
  try {
    const response = await fetch(url, options);
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Erro desconhecido');
    }
    
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    toast.error(error.message);
    throw error;
  }
}
```

---

## 🎉 Conclusão

Você agora tem:
✅ Documentação completa de **10 endpoints** para o frontend  
✅ URLs de produção (`https://siteup.onrender.com`)  
✅ Exemplos de código React para cada endpoint  
✅ Service layer completo (api.js)  
✅ Tratamento de erros e CORS configurado  

**Próximo passo:** Use esta documentação para desenvolver o frontend! 🚀
