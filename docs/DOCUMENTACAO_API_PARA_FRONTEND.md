# 📘 Documentação Completa da API - Para Desenvolvimento Frontend

## 🎯 Visão Geral da API

Esta é uma **API REST de Analytics** construída com FastAPI que fornece dados de marketing digital, análises de Machine Learning e relatórios narrativos gerados por IA (GPT-4o-mini via Agno).

**Base URL (Local):** `http://localhost:8000`  
**Base URL (Produção):** `https://seu-app.onrender.com`

---

## 📊 Estrutura de Dados

### Dados Disponíveis

A API trabalha com dados simulados de:
- **Google Analytics 4 (GA4)**: Tráfego, engagement, conversões
- **Google Search Console (GSC)**: Keywords, impressões, cliques, CTR, posições
- **Machine Learning**: Clusters de canais, keywords e páginas (K-Means)

### Período de Dados

- Dados históricos configuráveis (7 a 365 dias)
- Gerados sob demanda via endpoint administrativo
- Atualmente com ~31.099 sessões e ~94.652 conversões no banco

---

## 🔗 Lista Completa de Endpoints

### 1. Health Check
### 2. KPIs Principais
### 3. Análise de Canais (ML)
### 4. Análise de Keywords (ML)
### 5. Análise de Páginas (ML)
### 6. Matriz de Correlação
### 7. Simulador de Performance de Página
### 8. Relatórios Narrativos com IA ⭐
### 9. Endpoints Administrativos 🔒

---

## 📍 ENDPOINT 1: Health Check

**Propósito:** Verificar se a API está online e operacional.

**Método:** `GET`  
**URL:** `/api/v1/health`  
**Autenticação:** Não requerida

### Request
```http
GET /api/v1/health HTTP/1.1
Host: localhost:8000
```

### Response (200 OK)
```json
{
  "status": "healthy",
  "message": "API is running"
}
```

### Quando Usar no Frontend
- Página de loading inicial
- Status indicator no header
- Healthcheck periódico (setInterval a cada 30s)

### Exemplo React
```jsx
const [apiStatus, setApiStatus] = useState('checking');

useEffect(() => {
  fetch('/api/v1/health')
    .then(res => res.json())
    .then(data => setApiStatus(data.status))
    .catch(() => setApiStatus('offline'));
}, []);
```

---

## 📍 ENDPOINT 2: KPIs Principais

**Propósito:** Obter métricas principais de performance do site (sessões, conversões, bounce rate, etc).

**Método:** `GET`  
**URL:** `/api/v1/kpis`  
**Autenticação:** Não requerida

### Request
```http
GET /api/v1/kpis HTTP/1.1
Host: localhost:8000
```

### Response (200 OK)
```json
{
  "sessoesTotais": 31099,
  "conversoesTotais": 94652,
  "taxaConversao": 304.36,
  "mediaBounceRate": 27.0,
  "duracaoMediaSessao": 108.9,
  "totalPaginas": 9
}
```

### Campos Explicados

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `sessoesTotais` | number | Total de sessões no período |
| `conversoesTotais` | number | Total de conversões no período |
| `taxaConversao` | number | (conversões / sessões) * 100 |
| `mediaBounceRate` | number | Taxa média de rejeição (%) |
| `duracaoMediaSessao` | number | Tempo médio de sessão em segundos |
| `totalPaginas` | number | Número de páginas únicas visitadas |

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
    fetch('/api/v1/kpis')
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
        title="Taxa de Conversão" 
        value={`${kpis.taxaConversao.toFixed(2)}%`} 
        icon="📈"
      />
      <KPICard 
        title="Bounce Rate" 
        value={`${kpis.mediaBounceRate.toFixed(1)}%`} 
        icon="⚡"
      />
    </div>
  );
}
```

---

## 📍 ENDPOINT 3: Análise de Canais (Machine Learning)

**Propósito:** Obter clusters de canais de tráfego agrupados por Machine Learning (K-Means) com métricas de performance.

**Método:** `GET`  
**URL:** `/api/v1/channel-clusters`  
**Autenticação:** Não requerida

### Request
```http
GET /api/v1/channel-clusters HTTP/1.1
Host: localhost:8000
```

### Response (200 OK)
```json
{
  "clusters": [
    {
      "cluster_id": 0,
      "cluster_name": "High Engagement Channels",
      "channels": ["google/organic", "facebook/social"],
      "total_sessions": 15234,
      "total_conversions": 4567,
      "avg_bounce_rate": 23.5,
      "conversion_rate": 29.97,
      "characteristics": {
        "engagement_level": "high",
        "conversion_performance": "excellent"
      }
    },
    {
      "cluster_id": 1,
      "cluster_name": "Low Performing Channels",
      "channels": ["referral/referral", "email/email"],
      "total_sessions": 8901,
      "total_conversions": 1234,
      "avg_bounce_rate": 45.2,
      "conversion_rate": 13.86,
      "characteristics": {
        "engagement_level": "low",
        "conversion_performance": "needs_improvement"
      }
    }
  ],
  "summary": {
    "total_clusters": 2,
    "best_performing_cluster": "High Engagement Channels",
    "recommendation": "Focus budget on Cluster 0 channels"
  }
}
```

### Campos Explicados

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `cluster_id` | number | ID único do cluster (0, 1, 2...) |
| `cluster_name` | string | Nome descritivo do cluster |
| `channels` | string[] | Lista de canais (formato: source/medium) |
| `total_sessions` | number | Total de sessões deste cluster |
| `total_conversions` | number | Total de conversões deste cluster |
| `avg_bounce_rate` | number | Bounce rate médio do cluster (%) |
| `conversion_rate` | number | Taxa de conversão do cluster (%) |
| `characteristics` | object | Características qualitativas |

### Quando Usar no Frontend
- **Página de Análise de Canais**
- Visualização de clusters em gráfico (scatter plot, bar chart)
- Tabela comparativa de canais
- Recomendações de budget allocation

### Exemplo React
```jsx
function ChannelClustersPage() {
  const [clusters, setClusters] = useState([]);

  useEffect(() => {
    fetch('/api/v1/channel-clusters')
      .then(res => res.json())
      .then(data => setClusters(data.clusters));
  }, []);

  return (
    <div>
      <h1>📊 Análise de Canais (Machine Learning)</h1>
      
      {clusters.map(cluster => (
        <ClusterCard key={cluster.cluster_id}>
          <h3>{cluster.cluster_name}</h3>
          <div className="metrics">
            <Metric label="Sessões" value={cluster.total_sessions} />
            <Metric label="Conversões" value={cluster.total_conversions} />
            <Metric label="CVR" value={`${cluster.conversion_rate.toFixed(2)}%`} />
            <Metric label="Bounce" value={`${cluster.avg_bounce_rate.toFixed(1)}%`} />
          </div>
          
          <h4>Canais neste cluster:</h4>
          <ul>
            {cluster.channels.map(ch => (
              <li key={ch}>{ch}</li>
            ))}
          </ul>
          
          <Badge color={cluster.characteristics.engagement_level}>
            {cluster.characteristics.engagement_level}
          </Badge>
        </ClusterCard>
      ))}
    </div>
  );
}
```

---

## 📍 ENDPOINT 4: Análise de Keywords (Machine Learning)

**Propósito:** Obter clusters de keywords agrupadas por intenção de busca e performance (dados do Google Search Console).

**Método:** `GET`  
**URL:** `/api/v1/keyword-clusters`  
**Autenticação:** Não requerida

### Request
```http
GET /api/v1/keyword-clusters HTTP/1.1
Host: localhost:8000
```

### Response (200 OK)
```json
{
  "clusters": [
    {
      "cluster_id": 0,
      "cluster_name": "Branded Queries",
      "keywords": [
        {
          "query": "nome da marca",
          "impressions": 12500,
          "clicks": 8900,
          "ctr": 71.2,
          "position": 1.2
        }
      ],
      "total_impressions": 12500,
      "total_clicks": 8900,
      "avg_ctr": 71.2,
      "avg_position": 1.2,
      "search_intent": "branded"
    },
    {
      "cluster_id": 1,
      "cluster_name": "Informational Queries",
      "keywords": [
        {
          "query": "como fazer analytics",
          "impressions": 45000,
          "clicks": 3200,
          "ctr": 7.11,
          "position": 8.5
        }
      ],
      "total_impressions": 45000,
      "total_clicks": 3200,
      "avg_ctr": 7.11,
      "avg_position": 8.5,
      "search_intent": "informational"
    }
  ],
  "summary": {
    "total_clusters": 2,
    "total_keywords": 150,
    "best_ctr_cluster": "Branded Queries"
  }
}
```

### Campos Explicados

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `query` | string | Termo de busca (keyword) |
| `impressions` | number | Número de vezes que apareceu no Google |
| `clicks` | number | Número de cliques recebidos |
| `ctr` | number | Click-Through Rate (%) |
| `position` | number | Posição média no Google (1 = primeiro) |
| `search_intent` | string | Intenção: branded, informational, transactional |

### Quando Usar no Frontend
- **Página de SEO / Keywords**
- Tabela de keywords com filtros
- Gráfico de CTR vs Posição
- Oportunidades de otimização

### Exemplo React
```jsx
function KeywordClustersPage() {
  const [clusters, setClusters] = useState([]);
  const [selectedIntent, setSelectedIntent] = useState('all');

  useEffect(() => {
    fetch('/api/v1/keyword-clusters')
      .then(res => res.json())
      .then(data => setClusters(data.clusters));
  }, []);

  const filteredClusters = selectedIntent === 'all' 
    ? clusters 
    : clusters.filter(c => c.search_intent === selectedIntent);

  return (
    <div>
      <h1>🔍 Análise de Keywords (GSC + ML)</h1>
      
      <Filter 
        options={['all', 'branded', 'informational', 'transactional']}
        value={selectedIntent}
        onChange={setSelectedIntent}
      />

      {filteredClusters.map(cluster => (
        <ClusterCard key={cluster.cluster_id}>
          <h3>{cluster.cluster_name}</h3>
          <Badge>{cluster.search_intent}</Badge>
          
          <MetricsRow>
            <Metric label="Impressões" value={cluster.total_impressions.toLocaleString()} />
            <Metric label="Cliques" value={cluster.total_clicks.toLocaleString()} />
            <Metric label="CTR" value={`${cluster.avg_ctr.toFixed(2)}%`} />
            <Metric label="Posição" value={cluster.avg_position.toFixed(1)} />
          </MetricsRow>

          <KeywordsTable keywords={cluster.keywords} />
        </ClusterCard>
      ))}
    </div>
  );
}
```

---

## 📍 ENDPOINT 5: Análise de Páginas (Machine Learning)

**Propósito:** Obter clusters de páginas agrupadas por performance de engagement (tempo, bounce, conversões).

**Método:** `GET`  
**URL:** `/api/v1/page-clusters`  
**Autenticação:** Não requerida

### Request
```http
GET /api/v1/page-clusters HTTP/1.1
Host: localhost:8000
```

### Response (200 OK)
```json
{
  "clusters": [
    {
      "cluster_id": 0,
      "cluster_name": "High Converting Pages",
      "pages": [
        {
          "page": "/landing/promo",
          "sessions": 5234,
          "conversions": 2100,
          "bounce_rate": 18.5,
          "avg_time_on_page": 245.3,
          "conversion_rate": 40.13
        }
      ],
      "total_sessions": 5234,
      "total_conversions": 2100,
      "avg_bounce_rate": 18.5,
      "avg_time_on_page": 245.3,
      "performance_level": "excellent"
    }
  ],
  "summary": {
    "total_clusters": 3,
    "total_pages": 9
  }
}
```

### Campos Explicados

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `page` | string | URL/path da página |
| `sessions` | number | Sessões que visitaram esta página |
| `conversions` | number | Conversões originadas desta página |
| `bounce_rate` | number | Taxa de rejeição da página (%) |
| `avg_time_on_page` | number | Tempo médio na página (segundos) |
| `conversion_rate` | number | Taxa de conversão da página (%) |
| `performance_level` | string | excellent, good, needs_improvement |

### Quando Usar no Frontend
- **Página de Análise de Conteúdo**
- Ranking de páginas por performance
- Heatmap de conversões por página
- Identificação de páginas problemáticas

### Exemplo React
```jsx
function PageClustersPage() {
  const [clusters, setClusters] = useState([]);
  const [sortBy, setSortBy] = useState('conversion_rate');

  useEffect(() => {
    fetch('/api/v1/page-clusters')
      .then(res => res.json())
      .then(data => setClusters(data.clusters));
  }, []);

  // Flatten all pages from all clusters
  const allPages = clusters.flatMap(c => 
    c.pages.map(p => ({ ...p, cluster_name: c.cluster_name }))
  );

  // Sort pages
  const sortedPages = [...allPages].sort((a, b) => 
    b[sortBy] - a[sortBy]
  );

  return (
    <div>
      <h1>📄 Análise de Páginas (ML)</h1>
      
      <SortSelector 
        options={['conversion_rate', 'sessions', 'bounce_rate']}
        value={sortBy}
        onChange={setSortBy}
      />

      <Table>
        <thead>
          <tr>
            <th>Página</th>
            <th>Cluster</th>
            <th>Sessões</th>
            <th>Conversões</th>
            <th>CVR</th>
            <th>Bounce</th>
            <th>Tempo Médio</th>
          </tr>
        </thead>
        <tbody>
          {sortedPages.map(page => (
            <tr key={page.page}>
              <td>{page.page}</td>
              <td><Badge>{page.cluster_name}</Badge></td>
              <td>{page.sessions.toLocaleString()}</td>
              <td>{page.conversions.toLocaleString()}</td>
              <td>{page.conversion_rate.toFixed(2)}%</td>
              <td>{page.bounce_rate.toFixed(1)}%</td>
              <td>{Math.round(page.avg_time_on_page)}s</td>
            </tr>
          ))}
        </tbody>
      </Table>
    </div>
  );
}
```

---

## 📍 ENDPOINT 6: Matriz de Correlação

**Propósito:** Obter correlações estatísticas entre métricas (ex: sessões vs conversões, bounce vs tempo).

**Método:** `GET`  
**URL:** `/api/v1/correlation-matrix`  
**Autenticação:** Não requerida

### Request
```http
GET /api/v1/correlation-matrix HTTP/1.1
Host: localhost:8000
```

### Response (200 OK)
```json
{
  "correlation_matrix": {
    "sessions_vs_conversions": 0.87,
    "sessions_vs_bounce_rate": -0.34,
    "bounce_rate_vs_time_on_page": -0.62,
    "time_on_page_vs_conversions": 0.45
  },
  "insights": [
    {
      "pair": "sessions_vs_conversions",
      "correlation": 0.87,
      "strength": "strong_positive",
      "interpretation": "Aumento de sessões está fortemente correlacionado com aumento de conversões"
    }
  ],
  "significant_correlations": [
    {
      "pair": "sessions_vs_conversions",
      "value": 0.87,
      "p_value": 0.001
    }
  ]
}
```

### Campos Explicados

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `correlation` | number | Valor de -1 a 1 (negativo = inverso, positivo = direto) |
| `strength` | string | strong_positive, weak_negative, etc |
| `interpretation` | string | Texto explicativo da correlação |
| `p_value` | number | Significância estatística (< 0.05 = significante) |

### Quando Usar no Frontend
- **Página de Insights Estatísticos**
- Heatmap de correlações
- Gráficos de dispersão (scatter plots)
- Identificação de relações causais

### Exemplo React
```jsx
function CorrelationMatrixPage() {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetch('/api/v1/correlation-matrix')
      .then(res => res.json())
      .then(setData);
  }, []);

  if (!data) return <Loading />;

  return (
    <div>
      <h1>🔗 Matriz de Correlação</h1>
      
      <Heatmap data={data.correlation_matrix} />

      <section>
        <h2>Insights Principais</h2>
        {data.insights.map((insight, i) => (
          <InsightCard key={i}>
            <h3>{insight.pair.replace(/_/g, ' vs ')}</h3>
            <CorrelationBadge value={insight.correlation} strength={insight.strength} />
            <p>{insight.interpretation}</p>
          </InsightCard>
        ))}
      </section>

      <section>
        <h2>Correlações Significativas</h2>
        <Table>
          <thead>
            <tr>
              <th>Variáveis</th>
              <th>Correlação</th>
              <th>P-value</th>
              <th>Significância</th>
            </tr>
          </thead>
          <tbody>
            {data.significant_correlations.map(corr => (
              <tr key={corr.pair}>
                <td>{corr.pair}</td>
                <td>{corr.value.toFixed(3)}</td>
                <td>{corr.p_value.toFixed(4)}</td>
                <td>{corr.p_value < 0.05 ? '✅ Sim' : '❌ Não'}</td>
              </tr>
            ))}
          </tbody>
        </Table>
      </section>
    </div>
  );
}
```

---

## 📍 ENDPOINT 7: Simulador de Performance de Página

**Propósito:** Prever métricas de performance (conversões, bounce, tempo) baseado em características da página usando Machine Learning.

**Método:** `POST`  
**URL:** `/api/v1/simulate-page-performance`  
**Autenticação:** Não requerida

### Request
```http
POST /api/v1/simulate-page-performance HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "contagemDePalavras": 1200,
  "numeroDeImagens": 5,
  "tempoCarregamento": 2.3,
  "numeroDeLinks": 15,
  "temVideo": true,
  "temFormulario": true
}
```

### Request Body Explicado

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `contagemDePalavras` | number | ✅ Sim | Número de palavras no conteúdo (ex: 1200) |
| `numeroDeImagens` | number | ✅ Sim | Quantidade de imagens na página (ex: 5) |
| `tempoCarregamento` | number | ❌ Não | Tempo de carregamento em segundos (padrão: 3.0) |
| `numeroDeLinks` | number | ❌ Não | Quantidade de links internos (padrão: 10) |
| `temVideo` | boolean | ❌ Não | Se a página tem vídeo (padrão: false) |
| `temFormulario` | boolean | ❌ Não | Se a página tem formulário (padrão: false) |

### Response (200 OK)
```json
{
  "predicao": {
    "sessoes": 5234,
    "conversoes": 892,
    "taxaConversao": 17.04,
    "bounceRate": 32.5,
    "tempoMedioPagina": 185.6
  },
  "confianca": 0.82,
  "recomendacoes": [
    "Página com bom potencial de conversão (17.04%)",
    "Tempo de carregamento adequado (2.3s)",
    "Considere aumentar número de palavras para 1500+ para melhor SEO"
  ],
  "input_recebido": {
    "contagemDePalavras": 1200,
    "numeroDeImagens": 5,
    "tempoCarregamento": 2.3,
    "numeroDeLinks": 15,
    "temVideo": true,
    "temFormulario": true
  }
}
```

### Quando Usar no Frontend
- **Página de Otimização de Conteúdo**
- Ferramenta "Preditor de Performance"
- Planejamento de novas landing pages
- A/B testing calculator

### Exemplo React
```jsx
function PagePerformanceSimulator() {
  const [input, setInput] = useState({
    contagemDePalavras: 1000,
    numeroDeImagens: 3,
    tempoCarregamento: 3.0,
    numeroDeLinks: 10,
    temVideo: false,
    temFormulario: false
  });
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSimulate = async () => {
    setLoading(true);
    
    const response = await fetch('/api/v1/simulate-page-performance', {
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
          label="Tempo de Carregamento (segundos)"
          type="number"
          step="0.1"
          value={input.tempoCarregamento}
          onChange={v => setInput({...input, tempoCarregamento: v})}
        />
        
        <Checkbox 
          label="Tem Vídeo?"
          checked={input.temVideo}
          onChange={v => setInput({...input, temVideo: v})}
        />
        
        <Checkbox 
          label="Tem Formulário?"
          checked={input.temFormulario}
          onChange={v => setInput({...input, temFormulario: v})}
        />
        
        <Button onClick={handleSimulate} disabled={loading}>
          {loading ? 'Simulando...' : '🚀 Simular Performance'}
        </Button>
      </form>

      {prediction && (
        <ResultCard>
          <h2>📊 Predição</h2>
          <MetricsGrid>
            <Metric label="Sessões Estimadas" value={prediction.predicao.sessoes.toLocaleString()} />
            <Metric label="Conversões Estimadas" value={prediction.predicao.conversoes.toLocaleString()} />
            <Metric label="Taxa de Conversão" value={`${prediction.predicao.taxaConversao.toFixed(2)}%`} />
            <Metric label="Bounce Rate" value={`${prediction.predicao.bounceRate.toFixed(1)}%`} />
            <Metric label="Tempo Médio" value={`${Math.round(prediction.predicao.tempoMedioPagina)}s`} />
          </MetricsGrid>
          
          <ConfidenceBar value={prediction.confianca} />
          
          <h3>💡 Recomendações</h3>
          <ul>
            {prediction.recomendacoes.map((rec, i) => (
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

## 📍 ENDPOINT 8: Relatórios Narrativos com IA ⭐ (PRINCIPAL)

**Propósito:** Gerar relatório executivo completo com análise narrativa gerada por GPT-4o-mini, insights estratégicos e recomendações priorizadas.

**Método:** `POST`  
**URL:** `/api/v1/reports/generate`  
**Autenticação:** Não requerida (requer `OPENAI_API_KEY` configurada)

### Request
```http
POST /api/v1/reports/generate HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "period_days": 7,
  "detail_level": "executive",
  "focus_areas": ["conversions", "traffic"],
  "language": "pt-br"
}
```

### Request Body Explicado

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `period_days` | number | ✅ Sim | Período de análise em dias (7, 30, 90) |
| `detail_level` | string | ✅ Sim | executive, technical, detailed |
| `focus_areas` | string[] | ❌ Não | conversions, traffic, engagement, keywords, seo |
| `language` | string | ❌ Não | pt-br, en-us (padrão: pt-br) |

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
  "executive_summary": "Visão executiva — Período 2025-11-04 a 2025-11-11 (7 dias): O conjunto de KPIs apresenta **31.099 sessões**, **94.652 conversões** e uma **taxa de conversão de 304,36%**... [texto completo gerado pela IA]",
  "sections": [
    {
      "title": "Seção 1 — Visão Geral de Performance 🎯",
      "content": "Interpretação dos KPIs principais: [análise detalhada gerada pela IA]",
      "key_insights": [
        "94.652 conversões > 31.099 sessões sugere conversões múltiplas por sessão",
        "Taxa de rejeição baixa (27%) indica bom engajamento"
      ]
    }
  ],
  "recommendations": [
    {
      "priority": "high",
      "category": "conversions",
      "action": "Executar auditoria completa de tracking (GA4): verificar eventos/objetivos duplicados",
      "rationale": "Taxa de conversão de **304,36%** indica alto risco de dados inválidos"
    }
  ],
  "metadata": {
    "data_sources": ["kpis", "channel_clusters", "keyword_clusters"],
    "ml_models_used": ["channel_profiling", "keyword_clustering"],
    "agent_model": "gpt-4o-mini",
    "confidence_score": 0.55,
    "generation_timestamp": "2025-11-11T22:00:47.749622"
  }
}
```

### Response Explicado

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `report_id` | string (UUID) | ID único do relatório |
| `generated_at` | string (ISO 8601) | Data/hora de geração |
| `executive_summary` | string | Resumo executivo narrativo (100-300 palavras) |
| `sections` | array | 5-6 seções detalhadas de análise |
| `sections[].title` | string | Título da seção com emoji |
| `sections[].content` | string | Análise narrativa da seção |
| `sections[].key_insights` | string[] | 3-5 insights principais |
| `recommendations` | array | 5-8 recomendações priorizadas |
| `recommendations[].priority` | string | high, medium, low |
| `recommendations[].category` | string | conversions, traffic, engagement, keywords, seo |
| `recommendations[].action` | string | Ação específica a tomar |
| `recommendations[].rationale` | string | Justificativa da recomendação |
| `metadata.confidence_score` | number | 0.0 a 1.0 (confiabilidade da análise) |

### Estrutura das Seções

Sempre retorna 5-6 seções:
1. **Visão Geral de Performance** - KPIs principais
2. **Análise de Canais de Tráfego** - Clusters de canais
3. **Performance de Keywords (GSC)** - SEO e busca orgânica
4. **Segmentação de Páginas** - Performance de conteúdo
5. **Correlações e Padrões** - Insights estatísticos
6. **Metadata & Confidence** - Dados técnicos

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
    
    const response = await fetch('/api/v1/reports/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
    
    const data = await response.json();
    setReport(data);
    setLoading(false);
  };

  return (
    <div className="reports-page">
      <header>
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
          
          <Select 
            label="Nível de Detalhe"
            options={[
              { value: 'executive', label: 'Executivo' },
              { value: 'technical', label: 'Técnico' },
              { value: 'detailed', label: 'Detalhado' }
            ]}
            value={config.detail_level}
            onChange={v => setConfig({...config, detail_level: v})}
          />
          
          <Button onClick={generateReport} disabled={loading}>
            {loading ? '⏳ Gerando...' : '🚀 Gerar Relatório com IA'}
          </Button>
        </ConfigPanel>
      </header>

      {loading && (
        <LoadingState>
          <Spinner />
          <p>Analisando dados e gerando insights com GPT-4o-mini...</p>
          <ProgressBar />
        </LoadingState>
      )}

      {report && (
        <ReportView>
          {/* Header do Relatório */}
          <ReportHeader>
            <div>
              <h2>Relatório Executivo</h2>
              <p>Período: {report.period.start_date} a {report.period.end_date}</p>
              <p>Gerado em: {new Date(report.generated_at).toLocaleString('pt-BR')}</p>
            </div>
            <div>
              <ConfidenceBadge score={report.metadata.confidence_score} />
              <Button onClick={() => exportToPDF(report)}>📄 Exportar PDF</Button>
            </div>
          </ReportHeader>

          {/* Resumo Executivo */}
          <ExecutiveSummary>
            <h3>📋 Resumo Executivo</h3>
            <Markdown>{report.executive_summary}</Markdown>
          </ExecutiveSummary>

          {/* Seções Detalhadas */}
          {report.sections.map((section, index) => (
            <Section key={index}>
              <h3>{section.title}</h3>
              <Markdown>{section.content}</Markdown>
              
              {section.key_insights && section.key_insights.length > 0 && (
                <InsightsBox>
                  <h4>💡 Insights Principais</h4>
                  <ul>
                    {section.key_insights.map((insight, i) => (
                      <li key={i}>{insight}</li>
                    ))}
                  </ul>
                </InsightsBox>
              )}
            </Section>
          ))}

          {/* Recomendações */}
          <RecommendationsSection>
            <h3>🎯 Recomendações Priorizadas</h3>
            
            {/* Agrupar por prioridade */}
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
                    <RecommendationCard key={i} priority={priority}>
                      <CategoryBadge>{rec.category}</CategoryBadge>
                      <h5>{rec.action}</h5>
                      <p><strong>Por quê:</strong> {rec.rationale}</p>
                    </RecommendationCard>
                  ))}
                </PriorityGroup>
              );
            })}
          </RecommendationsSection>

          {/* Metadata (Footer) */}
          <ReportFooter>
            <small>
              Fontes de dados: {report.metadata.data_sources.join(', ')} |  
              Modelos ML: {report.metadata.ml_models_used.join(', ')} | 
              IA: {report.metadata.agent_model}
            </small>
          </ReportFooter>
        </ReportView>
      )}
    </div>
  );
}
```

---

## 📍 ENDPOINT 9: Popular Banco de Dados (ADMIN) 🔒

**Propósito:** Gerar dados simulados no banco de dados para testes e desenvolvimento.

**Método:** `POST`  
**URL:** `/api/v1/admin/populate-database`  
**Autenticação:** `ADMIN_KEY` (se configurada no .env)

### Request
```http
POST /api/v1/admin/populate-database HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "days": 30,
  "overwrite": false,
  "admin_key": "sua_chave_secreta"
}
```

### Request Body

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `days` | number | ✅ Sim | Dias de dados (1-365) |
| `overwrite` | boolean | ❌ Não | Se True, limpa antes (padrão: false) |
| `admin_key` | string | ⚠️ Condicional | Obrigatório se `ADMIN_KEY` configurada no .env |

### Response (200 OK)
```json
{
  "status": "success",
  "message": "Banco de dados populado com 30 dias de dados",
  "statistics": {
    "days_generated": 30,
    "traffic_records": 1864,
    "engagement_records": 1864,
    "conversion_records": 1864,
    "gsc_records": 1864,
    "overwrite_mode": false
  },
  "next_steps": [
    "Use GET /api/v1/kpis para visualizar KPIs",
    "Use POST /api/v1/reports/generate para gerar relatórios"
  ]
}
```

### Quando Usar no Frontend
- **Página de Admin** (protegida por senha)
- Setup inicial da aplicação
- Reset de dados de teste

### Exemplo React
```jsx
function AdminPage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [adminKey, setAdminKey] = useState('');
  const [days, setDays] = useState(30);

  const populateDatabase = async () => {
    setLoading(true);
    
    try {
      const response = await fetch('/api/v1/admin/populate-database', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          days,
          overwrite: false,
          admin_key: adminKey || undefined
        })
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setResult({ success: true, data });
      } else {
        setResult({ success: false, error: data.detail });
      }
    } catch (error) {
      setResult({ success: false, error: error.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="admin-page">
      <h1>🔒 Painel Administrativo</h1>
      
      <Card>
        <h2>Popular Banco de Dados</h2>
        
        <Input 
          label="Dias de dados"
          type="number"
          min="1"
          max="365"
          value={days}
          onChange={setDays}
        />
        
        <Input 
          label="Admin Key (se configurada)"
          type="password"
          value={adminKey}
          onChange={setAdminKey}
          placeholder="Deixe vazio se não configurou ADMIN_KEY"
        />
        
        <Button 
          onClick={populateDatabase} 
          disabled={loading}
        >
          {loading ? '⏳ Populando...' : '🚀 Popular Banco'}
        </Button>
      </Card>

      {result && (
        <ResultCard success={result.success}>
          {result.success ? (
            <>
              <h3>✅ Sucesso!</h3>
              <p>{result.data.message}</p>
              <ul>
                <li>Tráfego: {result.data.statistics.traffic_records} registros</li>
                <li>Engagement: {result.data.statistics.engagement_records} registros</li>
                <li>Conversões: {result.data.statistics.conversion_records} registros</li>
                <li>GSC: {result.data.statistics.gsc_records} registros</li>
              </ul>
            </>
          ) : (
            <>
              <h3>❌ Erro</h3>
              <p>{result.error}</p>
            </>
          )}
        </ResultCard>
      )}
    </div>
  );
}
```

---

## 📍 ENDPOINT 10: Estatísticas do Banco (ADMIN)

**Propósito:** Ver quantos dados existem no banco e período disponível.

**Método:** `GET`  
**URL:** `/api/v1/admin/database-stats`  
**Autenticação:** Não requerida

### Request
```http
GET /api/v1/admin/database-stats HTTP/1.1
Host: localhost:8000
```

### Response (200 OK)
```json
{
  "database_file": "data/processed/ga4_data.duckdb",
  "record_counts": {
    "ga4_traffic": 1864,
    "ga4_engagement": 1864,
    "ga4_conversions": 1864,
    "gsc_performance": 1864,
    "total": 7456
  },
  "date_range": {
    "start": "2024-10-13",
    "end": "2024-11-11"
  },
  "status": "operational"
}
```

### Quando Usar no Frontend
- **Dashboard de Admin**
- Status indicator (header/footer)
- Verificação antes de popular

### Exemplo React
```jsx
function DatabaseStats() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetch('/api/v1/admin/database-stats')
      .then(res => res.json())
      .then(setStats);
  }, []);

  if (!stats) return <Loading />;

  return (
    <StatsCard>
      <h3>📊 Estatísticas do Banco</h3>
      <p><strong>Total:</strong> {stats.record_counts.total.toLocaleString()} registros</p>
      <p><strong>Período:</strong> {stats.date_range.start} a {stats.date_range.end}</p>
      <StatusBadge status={stats.status} />
    </StatsCard>
  );
}
```

---

## 🎨 Arquitetura Frontend Sugerida

### Páginas Recomendadas

```
/
├── /dashboard              → KPIs principais (GET /kpis)
├── /channels               → Análise de canais (GET /channel-clusters)
├── /keywords               → Análise de keywords (GET /keyword-clusters)
├── /pages                  → Análise de páginas (GET /page-clusters)
├── /correlations           → Matriz de correlação (GET /correlation-matrix)
├── /simulator              → Simulador de página (POST /simulate-page-performance)
├── /reports                → Relatórios IA (POST /reports/generate) ⭐
└── /admin                  → Popular dados (POST /admin/populate-database) 🔒
```

### Estrutura de Componentes

```
src/
├── components/
│   ├── common/
│   │   ├── KPICard.jsx
│   │   ├── MetricCard.jsx
│   │   ├── Badge.jsx
│   │   ├── Loading.jsx
│   │   └── ErrorBoundary.jsx
│   ├── charts/
│   │   ├── BarChart.jsx
│   │   ├── LineChart.jsx
│   │   ├── ScatterPlot.jsx
│   │   └── Heatmap.jsx
│   ├── clusters/
│   │   ├── ClusterCard.jsx
│   │   └── ClusterTable.jsx
│   ├── reports/
│   │   ├── ReportView.jsx
│   │   ├── ReportSection.jsx
│   │   ├── RecommendationCard.jsx
│   │   └── ExecutiveSummary.jsx
│   └── admin/
│       ├── PopulateForm.jsx
│       └── DatabaseStats.jsx
├── pages/
│   ├── Dashboard.jsx
│   ├── Channels.jsx
│   ├── Keywords.jsx
│   ├── Pages.jsx
│   ├── Correlations.jsx
│   ├── Simulator.jsx
│   ├── Reports.jsx
│   └── Admin.jsx
├── services/
│   └── api.js
└── hooks/
    ├── useKPIs.js
    ├── useClusters.js
    └── useReports.js
```

### Service API (api.js)

```javascript
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = {
  // Health
  health: () => fetch(`${API_BASE_URL}/api/v1/health`).then(r => r.json()),
  
  // KPIs
  getKPIs: () => fetch(`${API_BASE_URL}/api/v1/kpis`).then(r => r.json()),
  
  // Clusters
  getChannelClusters: () => fetch(`${API_BASE_URL}/api/v1/channel-clusters`).then(r => r.json()),
  getKeywordClusters: () => fetch(`${API_BASE_URL}/api/v1/keyword-clusters`).then(r => r.json()),
  getPageClusters: () => fetch(`${API_BASE_URL}/api/v1/page-clusters`).then(r => r.json()),
  
  // Correlations
  getCorrelationMatrix: () => fetch(`${API_BASE_URL}/api/v1/correlation-matrix`).then(r => r.json()),
  
  // Simulator
  simulatePagePerformance: (data) => 
    fetch(`${API_BASE_URL}/api/v1/simulate-page-performance`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json()),
  
  // Reports (IA)
  generateReport: (config) =>
    fetch(`${API_BASE_URL}/api/v1/reports/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    }).then(r => r.json()),
  
  // Admin
  populateDatabase: (data) =>
    fetch(`${API_BASE_URL}/api/v1/admin/populate-database`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json()),
  
  getDatabaseStats: () => 
    fetch(`${API_BASE_URL}/api/v1/admin/database-stats`).then(r => r.json())
};
```

---

## 🔐 Segurança e CORS

### CORS Configurado

A API aceita requisições de **qualquer origem** (útil para desenvolvimento):

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique domínios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Headers Requeridos

Todas requisições POST/PUT devem incluir:
```
Content-Type: application/json
```

### Autenticação

- **Maioria dos endpoints**: Não requer autenticação
- **Endpoint `/admin/populate-database`**: Requer `admin_key` se `ADMIN_KEY` configurada no `.env`

---

## ⚡ Performance e Limites

### Timeouts
- Endpoints rápidos (KPIs, clusters): < 1 segundo
- Relatórios com IA: 10-30 segundos (depende da OpenAI API)
- Popular banco: 5-15 segundos (depende de `days`)

### Rate Limiting
Não implementado (adicione se necessário em produção)

### Caching
Não implementado (considere cachear KPIs e clusters)

---

## 🐛 Tratamento de Erros

### Códigos de Status

| Código | Significado | Quando Acontece |
|--------|-------------|-----------------|
| 200 | Success | Requisição bem-sucedida |
| 400 | Bad Request | Dados inválidos no body |
| 403 | Forbidden | ADMIN_KEY inválida |
| 404 | Not Found | Endpoint não existe |
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

## 📦 Deploy e Configuração

### Variáveis de Ambiente (Render)

```bash
# Obrigatório
OPENAI_API_KEY=sk-proj-sua-chave

# Recomendado
ADMIN_KEY=sua_chave_secreta_forte

# Opcional
DATABASE_URL=postgresql://... (para PostgreSQL)
```

### Build e Start (Render)

```bash
# Build Command
pip install -r requirements.txt

# Start Command
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

---

## 🎯 Prompt para IA Gerar Frontend

Use o prompt abaixo para gerar o frontend:

---

**PROMPT PARA IA:**

```
Crie um dashboard completo de analytics em React/Next.js que consome uma API REST.

CONTEXTO:
- A API fornece dados de marketing digital (GA4 + Google Search Console)
- Possui análises de Machine Learning (clusters de canais, keywords, páginas)
- Gera relatórios narrativos com IA (GPT-4o-mini)

ENDPOINTS DISPONÍVEIS:

1. GET /api/v1/health - Health check
2. GET /api/v1/kpis - KPIs principais (sessões, conversões, bounce, etc)
3. GET /api/v1/channel-clusters - Clusters de canais de tráfego (ML)
4. GET /api/v1/keyword-clusters - Clusters de keywords (GSC + ML)
5. GET /api/v1/page-clusters - Clusters de páginas por performance (ML)
6. GET /api/v1/correlation-matrix - Matriz de correlação entre métricas
7. POST /api/v1/simulate-page-performance - Simular performance de página
8. POST /api/v1/reports/generate - Gerar relatório narrativo com IA ⭐
9. POST /api/v1/admin/populate-database - Popular dados (admin)
10. GET /api/v1/admin/database-stats - Estatísticas do banco

REQUISITOS DO FRONTEND:

PÁGINAS:
1. Dashboard - Cards com KPIs principais (GET /kpis)
2. Canais - Tabela/gráficos de clusters de canais (GET /channel-clusters)
3. Keywords - Análise de SEO com keywords (GET /keyword-clusters)
4. Páginas - Performance de páginas (GET /page-clusters)
5. Insights - Matriz de correlação e insights estatísticos (GET /correlation-matrix)
6. Simulador - Ferramenta para prever performance de páginas (POST /simulate-page-performance)
7. Relatórios - Gerador de relatórios com IA ⭐ (POST /reports/generate)
8. Admin - Painel para popular dados (POST /admin/populate-database)

COMPONENTES PRINCIPAIS:
- KPICard - Card para exibir métricas
- ClusterCard - Card para exibir clusters
- ReportView - Visualizador de relatórios com seções e recomendações
- Charts - BarChart, LineChart, ScatterPlot, Heatmap
- Forms - Formulários para simulador e geração de relatórios

TECNOLOGIAS:
- React 18+ ou Next.js 14+
- TypeScript
- Tailwind CSS ou styled-components
- Recharts ou Chart.js para gráficos
- React Query para data fetching
- React Markdown para renderizar relatórios

FEATURES IMPORTANTES:
- Loading states para todas requisições
- Error handling com mensagens amigáveis
- Responsive design (mobile-first)
- Dark mode (opcional)
- Exportar relatórios para PDF (opcional)

DETALHES DA API:
- Base URL: http://localhost:8000 (dev) ou https://seu-app.onrender.com (prod)
- CORS habilitado
- Sem autenticação (exceto admin/populate-database que pode requerer admin_key)
- Responses em JSON
- Relatórios com IA levam 10-30s (mostrar loading)

PRIORIDADE:
1. Dashboard com KPIs
2. Página de Relatórios com IA (principal feature)
3. Análise de Canais
4. Simulador de Performance
5. Páginas restantes

Gere o código completo com:
- Estrutura de pastas
- Componentes reutilizáveis
- Service layer (api.js)
- Hooks customizados (useKPIs, useReports)
- Exemplos de uso de cada endpoint
- Estilos modernos e profissionais
```

---

## 🎉 Conclusão

Você agora tem:
✅ Documentação completa de 10 endpoints  
✅ Exemplos de código React para cada endpoint  
✅ Arquitetura sugerida para o frontend  
✅ Service layer completo (api.js)  
✅ Prompt otimizado para gerar frontend com IA  

**Próximo passo:** Use o prompt acima com ChatGPT, Claude, ou outra IA para gerar o código do frontend completo! 🚀
