
Crie um dashboard completo de analytics em Next.js 14 (App Router) + TypeScript + Tailwind CSS + shadcn/ui + Recharts.

## 🔗 API

**Base URL:** https://siteup.onrender.com
**Swagger Docs:** https://siteup.onrender.com/docs
**CORS:** Habilitado para todas as origens
**Autenticação:** Não requerida

## 📊 ENDPOINTS (10 no total)

### 1. KPIs Principais
- **GET** `/api/v1/overview/kpis`
- Retorna: `{ totalPaginas, sessoesTotais, conversoesTotais, mediaBounceRate, mediaSessionDuration }`
- Uso: Cards do dashboard principal

### 2. Matriz de Correlação
- **GET** `/api/v1/analysis/correlation_matrix`
- Retorna: Correlações entre conversões, engagementRate e averageSessionDuration
- Uso: Heatmap de correlações estatísticas

### 3. Clusters de Canais (Machine Learning)
- **GET** `/api/v1/ml/channel_clusters?n_clusters=3`
- Query params: `n_clusters` (2-10, padrão: 3)
- Retorna: `{ algoritmo, canais[], cluster_centers[], segment_summary[] }`
- Uso: Análise de canais de tráfego agrupados por ML

### 4. Clusters de Keywords (Machine Learning)
- **GET** `/api/v1/ml/keyword_clusters?n_clusters=3`
- Query params: `n_clusters` (2-10, padrão: 3)
- Retorna: `{ algoritmo, queries[], cluster_centers[], segment_summary[] }`
- Uso: Análise de SEO e keywords do Google Search Console

### 5. Clusters de Páginas (Machine Learning)
- **GET** `/api/v1/ml/page_clusters?n_clusters=5`
- Query params: `n_clusters` (2-10, padrão: 5)
- Retorna: `{ algoritmo, paginas[], cluster_centers[], segment_summary[] }`
- Uso: Segmentação de páginas por performance

### 6. Análise de Página Específica
- **GET** `/api/v1/page_analysis?path=/landing/promo`
- Query params: `path` (obrigatório)
- Retorna: `{ page_path, engagement_metrics, traffic_sources, performance_classification, recommendations }`
- Uso: Drill-down em página específica

### 7. Simulador de Performance
- **POST** `/api/v1/predict/simulator`
- Body: `{ contagemDePalavras, numeroDeImagens, precoDoProduto }`
- Retorna: `{ inputFeatures, predictedPerformance, recommendations }`
- Uso: Prever performance de nova página baseado em características

### 8. Dados Brutos Completos
- **GET** `/api/v1/data/all`
- Retorna: `{ traffic[], engagement[], conversions[], gsc_query_performance[] }`
- Uso: Exportação de dados brutos, tabelas completas

### 9. Resumo de Dados
- **GET** `/api/v1/data/summary`
- Retorna: Estatísticas de cada tabela (total_records, médias, date_range)
- Uso: Status do banco de dados

### 10. Relatórios Narrativos com IA ⭐ (PRINCIPAL)
- **POST** `/api/v1/reports/generate`
- Body: `{ period_days: 7, detail_level: "executive", focus_areas?: [], language?: "pt-br" }`
- Retorna: `{ report_id, executive_summary, sections[], recommendations[], metadata }`
- **ATENÇÃO:** Este endpoint demora 10-30 segundos (gera relatório com GPT-5-mini)
- Uso: Relatório executivo completo com análise narrativa em markdown

## 🎨 ESTRUTURA DO PROJETO

```
app/
├── layout.tsx                 → Layout principal com sidebar
├── page.tsx                   → Redirect para /dashboard
├── dashboard/
│   └── page.tsx              → KPIs em cards (Endpoint 1)
├── channels/
│   └── page.tsx              → Clusters de canais com gráficos (Endpoint 3)
├── keywords/
│   └── page.tsx              → Clusters de keywords + tabela (Endpoint 4)
├── pages/
│   └── page.tsx              → Clusters de páginas + ranking (Endpoint 5)
├── correlations/
│   └── page.tsx              → Heatmap de correlações (Endpoint 2)
├── simulator/
│   └── page.tsx              → Formulário + predição (Endpoint 7)
├── reports/
│   └── page.tsx              → Gerador de relatórios IA (Endpoint 10) ⭐
└── data/
    └── page.tsx              → Tabelas de dados brutos (Endpoint 8)

components/
├── ui/                        → shadcn/ui components
├── dashboard/
│   ├── KPICard.tsx           → Card para métricas (valor + ícone)
│   ├── MetricCard.tsx        → Card genérico
│   └── StatsGrid.tsx         → Grid de cards
├── charts/
│   ├── BarChart.tsx          → Gráfico de barras (Recharts)
│   ├── LineChart.tsx         → Gráfico de linhas (Recharts)
│   ├── ScatterPlot.tsx       → Scatter plot para clusters
│   └── Heatmap.tsx           → Heatmap para correlações
├── clusters/
│   ├── ClusterCard.tsx       → Card para exibir cluster
│   ├── ClusterTable.tsx      → Tabela de elementos do cluster
│   └── ClusterSelector.tsx   → Slider/Select para n_clusters
├── reports/
│   ├── ReportView.tsx        → Visualizador de relatório
│   ├── ReportSection.tsx     → Seção de relatório (markdown)
│   ├── ReportHeader.tsx      → Header com metadata
│   ├── RecommendationCard.tsx → Card de recomendação
│   └── ExecutiveSummary.tsx  → Resumo executivo
└── layout/
    ├── Sidebar.tsx           → Navegação lateral
    ├── Header.tsx            → Header com título
    └── Loading.tsx           → Loading states

lib/
├── api.ts                     → Service layer para API
└── utils.ts                   → Funções auxiliares

hooks/
├── useKPIs.ts                → React Query hook para KPIs
├── useClusters.ts            → React Query hook para clusters
└── useReports.ts             → React Query hook para relatórios
```

## 🎯 FEATURES OBRIGATÓRIAS

### 1. Dashboard (/dashboard)
- 5 cards KPI: Páginas, Sessões, Conversões, Bounce Rate, Duração Média
- Ícones para cada métrica
- Números formatados (locale pt-BR)
- Loading skeleton

### 2. Análise de Canais (/channels)
- Selector para n_clusters (2-10)
- Cards para cada cluster com:
  - Nome do cluster e performance_level (badge)
  - Métricas agregadas
  - Lista de canais (source/medium)
- Gráfico de barras comparando clusters
- Scatter plot de canais coloridos por cluster

### 3. Análise de Keywords (/keywords)
- Selector para n_clusters (2-10)
- Tabs/filtros por intent_category
- Tabela de keywords com:
  - Query, Cliques, Impressões, CTR, Posição
  - Ordenação por coluna
  - Badge de cluster
- Gráfico CTR vs Posição

### 4. Análise de Páginas (/pages)
- Selector para n_clusters (2-10)
- Tabela de páginas com:
  - Page path, Cluster, Engagement Rate, Eventos, Duração
  - Badges de performance_level
  - Click para drill-down (usar Endpoint 6)
- Ranking das top 10 páginas

### 5. Correlações (/correlations)
- Heatmap de correlações entre métricas
- Escala de cores (verde = positivo, vermelho = negativo)
- Tooltip com valor exato
- Cards explicativos para principais correlações

### 6. Simulador (/simulator)
- Formulário com 3 inputs:
  - Contagem de Palavras (number)
  - Número de Imagens (number)
  - Preço do Produto (number, R$)
- Botão "Simular Performance"
- Card de resultado com:
  - 4 métricas preditas (Engagement, Bounce, Duração, Conversões/1K)
  - Lista de recomendações

### 7. Relatórios IA (/reports) ⭐ PRINCIPAL
- Form com:
  - Select: Período (7, 30, 90 dias)
  - Select: Nível de detalhe (executive, technical, detailed)
  - Botão "Gerar Relatório com IA"
- Loading state customizado (10-30s):
  - Spinner + mensagem "Analisando dados e gerando insights..."
  - Progress bar animado
- Visualização do relatório:
  - Header com metadata (período, data, confidence score)
  - Resumo executivo (markdown)
  - Seções expansíveis (título + content em markdown + key_insights)
  - Recomendações agrupadas por prioridade (high/medium/low)
  - Botão "Exportar PDF" (opcional)
- Suporte a markdown (react-markdown)

### 8. Dados (/data)
- Tabs para cada tabela (Traffic, Engagement, Conversions, GSC)
- Tabela com paginação (TanStack Table)
- Filtros por coluna
- Botão "Exportar CSV"
- Card de resumo estatístico (Endpoint 9)

## 🔧 TECNOLOGIAS OBRIGATÓRIAS

- **Framework:** Next.js 14 (App Router)
- **Linguagem:** TypeScript
- **Estilização:** Tailwind CSS
- **Componentes:** shadcn/ui (Button, Card, Badge, Select, Input, Table, Tabs, Dialog)
- **Gráficos:** Recharts (BarChart, LineChart, ScatterChart)
- **Data Fetching:** React Query (TanStack Query)
- **Markdown:** react-markdown
- **Ícones:** lucide-react
- **Formatação:** date-fns, numeral


## 📦 SERVICE LAYER (lib/api.ts)

```typescript
const API_BASE_URL = 'https://siteup.onrender.com';

export const api = {
  // KPIs
  getKPIs: async () => {
    const res = await fetch(`${API_BASE_URL}/api/v1/overview/kpis`);
    if (!res.ok) throw new Error('Failed to fetch KPIs');
    return res.json();
  },
  
  // Correlations
  getCorrelationMatrix: async () => {
    const res = await fetch(`${API_BASE_URL}/api/v1/analysis/correlation_matrix`);
    if (!res.ok) throw new Error('Failed to fetch correlations');
    return res.json();
  },
  
  // ML Clusters
  getChannelClusters: async (nClusters = 3) => {
    const res = await fetch(`${API_BASE_URL}/api/v1/ml/channel_clusters?n_clusters=${nClusters}`);
    if (!res.ok) throw new Error('Failed to fetch channel clusters');
    return res.json();
  },
  
  getKeywordClusters: async (nClusters = 3) => {
    const res = await fetch(`${API_BASE_URL}/api/v1/ml/keyword_clusters?n_clusters=${nClusters}`);
    if (!res.ok) throw new Error('Failed to fetch keyword clusters');
    return res.json();
  },
  
  getPageClusters: async (nClusters = 5) => {
    const res = await fetch(`${API_BASE_URL}/api/v1/ml/page_clusters?n_clusters=${nClusters}`);
    if (!res.ok) throw new Error('Failed to fetch page clusters');
    return res.json();
  },
  
  // Page Analysis
  getPageAnalysis: async (path: string) => {
    const res = await fetch(`${API_BASE_URL}/api/v1/page_analysis?path=${encodeURIComponent(path)}`);
    if (!res.ok) throw new Error('Failed to fetch page analysis');
    return res.json();
  },
  
  // Simulator
  simulatePagePerformance: async (data: {
    contagemDePalavras: number;
    numeroDeImagens: number;
    precoDoProduto: number;
  }) => {
    const res = await fetch(`${API_BASE_URL}/api/v1/predict/simulator`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error('Failed to simulate performance');
    return res.json();
  },
  
  // Data
  getAllData: async () => {
    const res = await fetch(`${API_BASE_URL}/api/v1/data/all`);
    if (!res.ok) throw new Error('Failed to fetch all data');
    return res.json();
  },
  
  getDataSummary: async () => {
    const res = await fetch(`${API_BASE_URL}/api/v1/data/summary`);
    if (!res.ok) throw new Error('Failed to fetch data summary');
    return res.json();
  },
  
  // Reports (IA)
  generateReport: async (config: {
    period_days: number;
    detail_level: 'executive' | 'technical' | 'detailed';
    focus_areas?: string[];
    language?: string;
  }) => {
    const res = await fetch(`${API_BASE_URL}/api/v1/reports/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
    if (!res.ok) throw new Error('Failed to generate report');
    return res.json();
  }
};
```

## 🚀 REACT QUERY SETUP (app/providers.tsx)

```typescript
'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { useState } from 'react';

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60 * 1000, // 1 minuto
        refetchOnWindowFocus: false,
      },
    },
  }));

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
```

## 🎯 PRIORIDADES DE IMPLEMENTAÇÃO

### Fase 1 (MVP - Essencial)
1. ✅ Setup do projeto (Next.js + TypeScript + Tailwind + shadcn/ui)
2. ✅ Layout com Sidebar
3. ✅ Service layer (lib/api.ts)
4. ✅ Dashboard (/dashboard) - Endpoint 1
5. ✅ Relatórios IA (/reports) - Endpoint 10 ⭐ (FEATURE PRINCIPAL)

### Fase 2 (Análises ML)
6. ✅ Análise de Canais (/channels) - Endpoint 3
7. ✅ Análise de Keywords (/keywords) - Endpoint 4
8. ✅ Análise de Páginas (/pages) - Endpoint 5

### Fase 3 (Complementos)
9. ✅ Correlações (/correlations) - Endpoint 2
10. ✅ Simulador (/simulator) - Endpoint 7
11. ✅ Dados (/data) - Endpoints 8 e 9

## 📝 OBSERVAÇÕES IMPORTANTES

1. **Relatórios IA (Endpoint 10):**
   - É a FEATURE PRINCIPAL do projeto
   - Demora 10-30 segundos para responder
   - Implementar loading state robusto com feedback visual
   - Usar react-markdown para renderizar conteúdo
   - Suportar markdown formatting (títulos, listas, negrito, etc)

2. **Clusters ML (Endpoints 3, 4, 5):**
   - Permitir ajustar n_clusters dinamicamente
   - Mostrar visualizações gráficas (scatter plots, bar charts)
   - Performance level/intent_category devem ter badges coloridos

3. **Formatação de Dados:**
   - Números: use `toLocaleString('pt-BR')`
   - Percentuais: multiplicar por 100 se valor entre 0-1
   - Datas: formato DD/MM/YYYY
   - Duração: converter segundos para formato legível

4. **Error Handling:**
   - Toast notifications para erros
   - Mensagens amigáveis para usuário
   - Retry automático em erros de rede (React Query)

5. **Performance:**
   - React Query cache para evitar requests desnecessários
   - Lazy loading de componentes pesados
   - Virtualization em tabelas grandes (react-virtual)

## 🎬 RESULTADO ESPERADO

Um dashboard profissional e moderno que:
- ✅ Consuma todos os 10 endpoints
- ✅ Tenha navegação fluida entre páginas
- ✅ Exiba dados de forma visual e compreensível
- ✅ Destaque a funcionalidade de relatórios IA
- ✅ Seja responsivo (mobile, tablet, desktop)
- ✅ Tenha loading states e error handling
- ✅ Use TypeScript para type safety
- ✅ Siga boas práticas de React/Next.js

---

**IMPORTANTE:** Comece pela Fase 1 (Dashboard + Relatórios IA) e depois expanda para as outras páginas. A página de relatórios é a mais crítica e deve ter atenção especial no loading state e renderização de markdown.

