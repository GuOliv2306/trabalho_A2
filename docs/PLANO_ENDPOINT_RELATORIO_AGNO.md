# 📊 PLANO: Endpoint de Relatório Inteligente com Agno

## 1. VISÃO GERAL

### Objetivo
Criar um endpoint que agregue todas as análises existentes e utilize a biblioteca **Agno** (multi-agent AI framework) para gerar relatórios narrativos compreensíveis para usuários finais.

### Proposta de Valor
- **Atual**: Usuário recebe apenas dados brutos (JSON com números)
- **Novo**: Usuário recebe análise narrativa completa com insights acionáveis
- **Diferencial**: Transformação de dados técnicos em linguagem de negócio

---

## 2. ESPECIFICAÇÃO DO ENDPOINT

### Rota
```
POST /api/v1/reports/generate
```

### Parâmetros de Entrada
```json
{
  "period_days": 30,           // Período de análise (padrão: 30)
  "focus_areas": [              // Áreas de foco (opcional)
    "traffic",
    "conversions", 
    "engagement",
    "keywords"
  ],
  "detail_level": "executive",  // "executive" | "detailed" | "technical"
  "language": "pt-br"           // Idioma do relatório
}
```

### Resposta
```json
{
  "report_id": "uuid",
  "generated_at": "2024-01-22T10:30:00Z",
  "period": {
    "start_date": "2023-12-23",
    "end_date": "2024-01-22",
    "days": 30
  },
  "executive_summary": "Texto narrativo com resumo executivo...",
  "sections": [
    {
      "title": "Visão Geral de Performance",
      "content": "Narrativa sobre KPIs...",
      "key_insights": ["Insight 1", "Insight 2"],
      "data_references": {
        "total_sessions": 1500,
        "conversion_rate": 2.5
      }
    },
    {
      "title": "Análise de Canais",
      "content": "Narrativa sobre clusters de canais...",
      "clusters_identified": 3,
      "recommendations": ["Recomendação 1"]
    }
  ],
  "recommendations": [
    {
      "priority": "high",
      "category": "traffic",
      "action": "Aumentar investimento em google/organic",
      "rationale": "Este canal apresentou 45% de conversões..."
    }
  ],
  "metadata": {
    "data_sources": ["traffic", "conversions", "engagement", "gsc"],
    "ml_models_used": ["channel_profiling", "keyword_clustering", "page_segmentation"],
    "confidence_score": 0.87
  }
}
```

---

## 3. ARQUITETURA DO AGENTE AGNO

### Biblioteca Agno - Características
- **Framework**: Multi-agent AI system (AGI)
- **Integração**: OpenAI GPT models (gpt-5-mini recomendado)
- **Capacidades**: 
  - Synthesize de múltiplas fontes de dados
  - Geração de narrativas estruturadas
  - Formatação em Markdown
  - Sistema de instruções customizáveis
  - Output schemas (Pydantic)

### Design do Agente: "Analytics Report Generator"

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from pydantic import BaseModel
from typing import List, Dict, Any

class ReportSection(BaseModel):
    title: str
    content: str
    key_insights: List[str]
    data_references: Dict[str, Any]

class Recommendation(BaseModel):
    priority: str  # high, medium, low
    category: str
    action: str
    rationale: str

class AnalyticsReport(BaseModel):
    executive_summary: str
    sections: List[ReportSection]
    recommendations: List[Recommendation]
    metadata: Dict[str, Any]

report_generator_agent = Agent(
    name="Analytics Report Generator",
    model=OpenAIChat(id="gpt-5-mini"),
    description="""
    Você é um Analista de Negócios Sênior especializado em transformar dados 
    analíticos complexos em relatórios executivos compreensíveis. Suas expertises:
    
    - Análise de métricas de marketing digital
    - Interpretação de padrões de tráfego web
    - Avaliação de performance de conversão
    - Síntese de dados de múltiplas fontes
    - Recomendações estratégicas baseadas em dados
    - Comunicação clara para stakeholders não-técnicos
    """,
    instructions=[
        # Instruções detalhadas aqui (ver seção 4)
    ],
    output_schema=AnalyticsReport,
    add_datetime_to_context=True,
    markdown=True,
    debug_mode=False  # True apenas em desenvolvimento
)
```

---

## 4. INSTRUÇÕES DO AGENTE (Prompt Engineering)

### Estrutura das Instruções

```python
instructions = [
    # 1. ANÁLISE DE CONTEXTO
    """
    1. Contexto de Dados 📊
       - Você receberá dados agregados de 4 fontes principais:
         * KPIs gerais (páginas, sessões, conversões, bounce rate)
         * Clusters de canais (K-Means com 3 grupos)
         * Clusters de keywords (K-Means com 3 grupos)
         * Clusters de páginas (K-Means com 3 grupos)
         * Matriz de correlação (métricas temporais)
       - Todos os dados cobrem o mesmo período temporal
       - Clusters são resultado de Machine Learning (K-Means)
    """,
    
    # 2. ESTRUTURA DO RELATÓRIO
    """
    2. Estrutura do Relatório 📝
       - Executive Summary (3-5 parágrafos):
         * Resumo dos principais achados
         * Performance geral do período
         * Destaques positivos e pontos de atenção
         
       - Seção 1: Visão Geral de Performance
         * Interpretar KPIs principais
         * Comparar com benchmarks (se disponível)
         * Identificar tendências
         
       - Seção 2: Análise de Canais de Tráfego
         * Descrever os 3 clusters identificados
         * Dar nomes significativos aos clusters (ex: "Canais de Alta Conversão")
         * Identificar características de cada grupo
         * Destacar canais top performers
         
       - Seção 3: Performance de Keywords (GSC)
         * Descrever os 3 clusters de palavras-chave
         * Categorizar (ex: "Keywords de Alto Volume", "Keywords de Alta Taxa de Conversão")
         * Identificar oportunidades de otimização
         
       - Seção 4: Segmentação de Páginas
         * Descrever os 3 clusters de páginas
         * Identificar páginas de alta performance
         * Detectar páginas com problemas
         
       - Seção 5: Correlações e Padrões
         * Explicar correlações significativas
         * Identificar relações causa-efeito
         * Destacar anomalias ou padrões inesperados
    """,
    
    # 3. INTERPRETAÇÃO DE CLUSTERS
    """
    3. Interpretação de Clusters ML 🎯
       Para cada cluster identificado:
       - Analisar as médias das features
       - Comparar com os outros clusters
       - Dar um nome descritivo e significativo
       - Explicar o que caracteriza o grupo
       - Indicar o tamanho do cluster (número de elementos)
       
       Exemplo de nomenclatura:
       - Cluster 0 → "Canais de Alto Engajamento"
       - Cluster 1 → "Canais de Alto Volume, Baixa Conversão"
       - Cluster 2 → "Canais Emergentes"
    """,
    
    # 4. RECOMENDAÇÕES
    """
    4. Recomendações Estratégicas 💡
       Gerar 5-8 recomendações priorizadas:
       
       Para cada recomendação:
       - Prioridade: high/medium/low
       - Categoria: traffic/conversions/engagement/keywords
       - Ação específica e acionável
       - Rationale baseado nos dados
       
       Critérios de priorização:
       - High: Impacto grande + Esforço baixo
       - Medium: Impacto médio ou esforço médio
       - Low: Melhorias incrementais
       
       Exemplos:
       - "Aumentar investimento em google/organic (45% de conversões)"
       - "Otimizar páginas do Cluster 2 (alta rejeição)"
       - "Focar em keywords do Cluster 0 (alto ROI)"
    """,
    
    # 5. ESTILO E TOM
    """
    5. Estilo e Tom de Comunicação ✍️
       - Linguagem clara e objetiva
       - Evitar jargões técnicos excessivos
       - Usar analogias quando apropriado
       - Priorizar insights acionáveis
       - Ser conciso mas completo
       - Usar emojis moderadamente para ênfase
       - Traduzir termos técnicos (ex: "bounce rate" → "taxa de rejeição")
       
       Público-alvo:
       - Gestores de marketing
       - Analistas de negócios
       - Stakeholders não-técnicos
    """,
    
    # 6. TRATAMENTO DE DADOS
    """
    6. Tratamento de Dados 🔍
       - Se um cluster tem poucos elementos (< 5), mencionar limitação
       - Se correlações são zero/muito baixas, explicar possíveis causas
       - Se faltam dados, indicar claramente
       - Sempre citar números específicos para embasar afirmações
       - Incluir data_references para rastreabilidade
    """,
    
    # 7. KEY INSIGHTS
    """
    7. Key Insights por Seção 🎯
       Cada seção deve ter 2-4 key insights:
       - Frases curtas e impactantes
       - Baseadas em dados concretos
       - Destacar descobertas não-óbvias
       - Focar em actionable insights
       
       Exemplo:
       - "Google Organic representa 35% do tráfego mas 60% das conversões"
       - "Páginas de produto têm 2x mais engajamento que blog"
       - "Keywords de cauda longa trazem 40% menos volume mas 3x mais conversão"
    """,
    
    # 8. METADATA
    """
    8. Metadata e Confiabilidade 📋
       Sempre incluir no metadata:
       - data_sources: Lista de fontes usadas
       - ml_models_used: Modelos ML aplicados
       - confidence_score: 0-1 baseado em:
         * Volume de dados (mais dados = mais confiança)
         * Qualidade dos clusters (silhouette score se disponível)
         * Completude dos dados
       
       Fórmula sugerida:
       confidence = (data_completeness * 0.4) + (cluster_quality * 0.3) + (data_volume * 0.3)
    """
]
```

---

## 5. FLUXO DE EXECUÇÃO DO ENDPOINT

### Passo a Passo

```python
@app.post("/api/v1/reports/generate")
async def generate_report(request: ReportRequest):
    """
    Endpoint que gera relatório narrativo com Agno
    """
    
    # ETAPA 1: Coletar dados de todos os endpoints existentes
    data_collection = {
        "kpis": await collect_kpis(),
        "channel_clusters": await collect_channel_clusters(),
        "keyword_clusters": await collect_keyword_clusters(), 
        "page_clusters": await collect_page_clusters(),
        "correlations": await collect_correlations(),
        "period": {
            "start_date": calculate_start_date(request.period_days),
            "end_date": datetime.now().date(),
            "days": request.period_days
        }
    }
    
    # ETAPA 2: Preparar contexto para o agente
    context_prompt = f"""
    Gere um relatório analítico completo baseado nos seguintes dados:
    
    ## Período de Análise
    - Início: {data_collection['period']['start_date']}
    - Fim: {data_collection['period']['end_date']}
    - Dias: {data_collection['period']['days']}
    
    ## KPIs Gerais
    {format_kpis(data_collection['kpis'])}
    
    ## Clusters de Canais de Tráfego
    {format_channel_clusters(data_collection['channel_clusters'])}
    
    ## Clusters de Keywords (GSC)
    {format_keyword_clusters(data_collection['keyword_clusters'])}
    
    ## Clusters de Páginas
    {format_page_clusters(data_collection['page_clusters'])}
    
    ## Matriz de Correlação
    {format_correlations(data_collection['correlations'])}
    
    ## Instruções Específicas
    - Nível de detalhe: {request.detail_level}
    - Focar em: {', '.join(request.focus_areas) if request.focus_areas else 'todas as áreas'}
    - Idioma: {request.language}
    """
    
    # ETAPA 3: Invocar o agente Agno
    try:
        response = report_generator_agent.run(context_prompt)
        
        # ETAPA 4: Estruturar resposta
        report = {
            "report_id": str(uuid.uuid4()),
            "generated_at": datetime.now().isoformat(),
            "period": data_collection['period'],
            "executive_summary": response.executive_summary,
            "sections": response.sections,
            "recommendations": response.recommendations,
            "metadata": {
                **response.metadata,
                "data_sources": list(data_collection.keys()),
                "ml_models_used": ["channel_profiling", "keyword_clustering", "page_segmentation"],
                "agent_model": "gpt-5-mini",
                "generation_timestamp": datetime.now().isoformat()
            }
        }
        
        return JSONResponse(content=report)
        
    except Exception as e:
        logger.error(f"Erro ao gerar relatório: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao gerar relatório: {str(e)}")
```

---

## 6. FUNÇÕES AUXILIARES

### Formatação de Dados para o Agente

```python
def format_kpis(kpis: dict) -> str:
    """Formata KPIs em texto legível"""
    return f"""
- Total de Páginas: {kpis['total_pages']}
- Total de Sessões: {kpis['total_sessions']}
- Total de Conversões: {kpis['total_conversions']}
- Taxa de Conversão: {kpis['conversion_rate']:.2f}%
- Taxa de Rejeição: {kpis['bounce_rate']:.2f}%
- Duração Média da Sessão: {kpis['avg_session_duration']:.2f}s
    """

def format_channel_clusters(clusters: dict) -> str:
    """Formata clusters de canais em texto estruturado"""
    output = []
    for cluster_id, cluster_data in clusters['clusters'].items():
        output.append(f"""
### Cluster {cluster_id}
- Elementos: {cluster_data['count']}
- Canais: {', '.join(cluster_data['channels'][:5])}...
- Características médias:
  * Sessões: {cluster_data['avg_metrics']['sessions']:.0f}
  * Usuários Ativos: {cluster_data['avg_metrics']['active_users']:.0f}
  * Duração Média: {cluster_data['avg_metrics']['avg_duration']:.0f}s
        """)
    return "\n".join(output)

def format_keyword_clusters(clusters: dict) -> str:
    """Formata clusters de keywords"""
    # Similar ao format_channel_clusters
    pass

def format_page_clusters(clusters: dict) -> str:
    """Formata clusters de páginas"""
    # Similar ao format_channel_clusters
    pass

def format_correlations(correlations: dict) -> str:
    """Formata matriz de correlação"""
    output = ["Correlações significativas (|r| > 0.3):"]
    for metric1, correlations in correlations.items():
        for metric2, value in correlations.items():
            if abs(value) > 0.3 and metric1 != metric2:
                direction = "positiva" if value > 0 else "negativa"
                output.append(f"- {metric1} ↔ {metric2}: {value:.2f} ({direction})")
    return "\n".join(output)
```

---

## 7. DEPENDÊNCIAS E INSTALAÇÃO

### requirements.txt
```txt
# Adicionar à seção existente
# AI/ML Generation
agno>=0.3.0
openai>=1.0.0
```

### Variáveis de Ambiente
```bash
# .env ou settings
OPENAI_API_KEY=sk-...
AGNO_DEBUG_MODE=False
REPORT_CACHE_TTL=3600  # Cache de relatórios (1h)
```

---

## 8. TRATAMENTO DE ERROS E FALLBACKS

### Estratégias

```python
class ReportGenerationError(Exception):
    """Erro customizado para geração de relatórios"""
    pass

# Fallback 1: Se Agno falhar, gerar relatório simples
def generate_simple_report(data: dict) -> dict:
    """Relatório básico sem IA quando Agno falha"""
    return {
        "executive_summary": "Relatório gerado em modo simplificado.",
        "sections": [
            {
                "title": "KPIs",
                "content": format_kpis(data['kpis']),
                "key_insights": [],
                "data_references": data['kpis']
            }
        ],
        "recommendations": [],
        "metadata": {"generation_mode": "fallback"}
    }

# Fallback 2: Cache de relatórios recentes
@lru_cache(maxsize=10)
def get_cached_report(period_hash: str):
    """Cache de relatórios já gerados"""
    pass

# Retry com backoff exponencial
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def call_agno_agent(prompt: str):
    """Invoca agente com retry"""
    return report_generator_agent.run(prompt)
```

---

## 9. TESTES E VALIDAÇÃO

### Casos de Teste

```python
# test_report_generation.py

async def test_report_generation_success():
    """Testa geração completa de relatório"""
    response = await client.post("/api/v1/reports/generate", json={
        "period_days": 7,
        "detail_level": "executive",
        "language": "pt-br"
    })
    assert response.status_code == 200
    data = response.json()
    assert "executive_summary" in data
    assert len(data["sections"]) >= 4
    assert len(data["recommendations"]) > 0

async def test_report_with_focus_areas():
    """Testa relatório focado em áreas específicas"""
    response = await client.post("/api/v1/reports/generate", json={
        "period_days": 30,
        "focus_areas": ["traffic", "conversions"],
        "detail_level": "detailed"
    })
    assert response.status_code == 200

async def test_report_fallback_mode():
    """Testa modo fallback quando Agno falha"""
    # Simular falha do Agno
    with patch('agno.agent.Agent.run', side_effect=Exception("API Error")):
        response = await client.post("/api/v1/reports/generate", json={
            "period_days": 7
        })
        assert response.status_code == 200
        assert response.json()["metadata"]["generation_mode"] == "fallback"
```

---

## 10. PERFORMANCE E OTIMIZAÇÕES

### Considerações

1. **Tempo de Resposta**
   - Coleta de dados: ~2-3s (4 endpoints paralelos)
   - Processamento Agno: ~5-10s (depende do modelo)
   - Total estimado: **7-13 segundos**

2. **Otimizações Recomendadas**
      
   - **Paralelização**: Coletar dados de endpoints em paralelo (asyncio.gather)
   - **Cache**: Cachear relatórios por 1h (período + parâmetros como chave)
   - **Streaming**: Retornar relatório em chunks (SSE - Server-Sent Events)
   - **Background Jobs**: Para relatórios complexos, processar em background (Celery)

3. **Custos de API (OpenAI)**
   - Modelo: gpt-5-mini (~$0.15/1M tokens de entrada, $0.60/1M tokens de saída)
   - Estimativa por relatório: ~2000 tokens entrada + 1500 tokens saída
   - Custo por relatório: **~$0.0012** (menos de 1 centavo)
   - 1000 relatórios/mês: **~$1.20**

4. **Rate Limits**
   - Implementar rate limiting (ex: 5 relatórios/usuário/hora)
   - Queue para requisições concorrentes

---

## 11. MONITORAMENTO E MÉTRICAS

### KPIs do Endpoint

```python
# Métricas a coletar (Prometheus/logging)
- report_generation_duration_seconds
- report_generation_success_total
- report_generation_failure_total
- agno_api_calls_total
- agno_token_usage_total
- cache_hit_rate
- average_report_quality_score (feedback dos usuários)
```

### Logging

```python
import structlog

logger = structlog.get_logger()

logger.info(
    "report_generated",
    report_id=report_id,
    period_days=request.period_days,
    detail_level=request.detail_level,
    generation_time=elapsed_time,
    token_usage=response.usage,
    cache_hit=cache_hit
)
```

---

## 12. ROADMAP E EVOLUÇÕES FUTURAS

### Fase 1 (MVP) - Semana 1-2
- ✅ Implementar endpoint básico
- ✅ Integração com Agno (modelo único)
- ✅ Formatação de dados
- ✅ Testes unitários

### Fase 2 (Enhancements) - Semana 3-4
- 📊 Adicionar gráficos/visualizações inline (base64)
- 💾 Salvar relatórios em banco de dados
- 📧 Envio de relatórios por email
- 📅 Agendamento de relatórios recorrentes

### Fase 3 (Advanced) - Mês 2
- 🤖 Multi-agent system:
  * Agent 1: Data Analyst (interpreta números)
  * Agent 2: Business Strategist (gera recomendações)
  * Agent 3: Editor (sintetiza e formata)
- 🎨 Templates customizáveis por tipo de relatório
- 📱 Exportação para PDF/PowerPoint
- 🔮 Previsões e forecasting com séries temporais

### Fase 4 (AI-Powered) - Mês 3+
- 🧠 Fine-tuning de modelo específico para relatórios de marketing
- 🗣️ Relatórios em áudio (text-to-speech)
- 🎥 Vídeo-relatórios com narração IA
- 💬 Chatbot interativo sobre o relatório

---

## 13. ALTERNATIVAS E COMPARAÇÕES

### Por que Agno?

| Aspecto | Agno | LangChain | CrewAI | Custom GPT |
|---------|------|-----------|---------|------------|
| Setup | ⭐⭐⭐⭐⭐ Simples | ⭐⭐⭐ Médio | ⭐⭐⭐⭐ Fácil | ⭐⭐ Limitado |
| Multi-agent | ✅ Nativo | ✅ Possível | ✅ Nativo | ❌ Não |
| Output Schema | ✅ Pydantic | ✅ Pydantic | ✅ Pydantic | ❌ Texto |
| Markdown | ✅ Nativo | ⚠️ Manual | ✅ Sim | ⚠️ Manual |
| Context Control | ✅ Excelente | ✅ Bom | ✅ Bom | ⚠️ Limitado |
| Documentação | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| Comunidade | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

**Decisão**: Agno é ideal para este caso porque:
- Setup rápido e direto
- Output schema nativo (Pydantic)
- Instruções claras e estruturadas
- Markdown nativo
- Documentação focada em agentes de relatório

---

## 14. RISCOS E MITIGAÇÕES

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| API OpenAI indisponível | Alto | Baixa | Fallback para relatório simples |
| Custos excederem orçamento | Médio | Média | Rate limiting + cache agressivo |
| Qualidade dos relatórios baixa | Alto | Média | Validação de output + feedback loop |
| Tempo de resposta lento | Médio | Alta | Cache + processamento assíncrono |
| Dados insuficientes | Médio | Baixa | Validação antes de enviar para Agno |
| Hallucinations da IA | Alto | Média | Sempre citar dados de origem |

---

## 15. CHECKLIST DE IMPLEMENTAÇÃO

### Preparação
- [ ] Instalar biblioteca Agno (`pip install agno`)
- [ ] Obter API key OpenAI
- [ ] Adicionar variáveis de ambiente
- [ ] Estudar exemplos de Agno (Report Generator)

### Desenvolvimento
- [ ] Criar modelos Pydantic (ReportRequest, AnalyticsReport)
- [ ] Implementar funções auxiliares de formatação
- [ ] Criar agente Agno com instruções
- [ ] Implementar endpoint POST /api/v1/reports/generate
- [ ] Adicionar coleta paralela de dados (asyncio)
- [ ] Implementar sistema de cache
- [ ] Adicionar tratamento de erros e fallbacks

### Testes
- [ ] Teste unitário de cada função auxiliar
- [ ] Teste de integração do endpoint completo
- [ ] Teste de fallback (simular falha do Agno)
- [ ] Teste de performance (tempo de resposta)
- [ ] Teste de qualidade (validar output schema)
- [ ] Teste com diferentes volumes de dados

### Documentação
- [ ] Documentar endpoint na API (OpenAPI/Swagger)
- [ ] Criar exemplos de requisição/resposta
- [ ] Documentar variáveis de ambiente
- [ ] Adicionar guia de troubleshooting
- [ ] Atualizar README principal

### Deploy
- [ ] Configurar rate limiting
- [ ] Configurar logging estruturado
- [ ] Configurar métricas (Prometheus)
- [ ] Testar em ambiente de staging
- [ ] Deploy em produção
- [ ] Monitorar primeiros relatórios

---

## 16. EXEMPLO DE USO FINAL

### Requisição
```bash
curl -X POST http://localhost:8000/api/v1/reports/generate \
  -H "Content-Type: application/json" \
  -d '{
    "period_days": 30,
    "focus_areas": ["traffic", "conversions"],
    "detail_level": "executive",
    "language": "pt-br"
  }'
```

### Resposta Esperada (Resumida)
```json
{
  "report_id": "a1b2c3d4-...",
  "generated_at": "2024-01-22T15:30:00Z",
  "period": {
    "start_date": "2023-12-23",
    "end_date": "2024-01-22",
    "days": 30
  },
  "executive_summary": "Durante os últimos 30 dias, o site registrou 1.500 sessões com uma taxa de conversão de 2,5%, superando a meta estabelecida. O canal google/organic se destacou como principal fonte de conversões de alta qualidade, contribuindo com 60% do total apesar de representar apenas 35% do tráfego. A análise de machine learning identificou 3 grupos distintos de canais de tráfego, revelando oportunidades de otimização em canais sub-utilizados que apresentam potencial de crescimento...",
  
  "sections": [
    {
      "title": "🎯 Visão Geral de Performance",
      "content": "O período analisado apresentou resultados sólidos...",
      "key_insights": [
        "Taxa de conversão 25% acima da média do setor",
        "Bounce rate de 45% indica boa qualidade de tráfego",
        "Duração média de sessão cresceu 15% vs período anterior"
      ],
      "data_references": {
        "total_sessions": 1500,
        "total_conversions": 37,
        "conversion_rate": 2.47
      }
    },
    {
      "title": "📊 Análise de Canais de Tráfego",
      "content": "A segmentação por machine learning identificou 3 perfis distintos de canais:\n\n**Cluster 1: Canais de Alta Conversão** (8 canais)\nCaracterizado por google/organic, google/cpc e bing/organic. Este grupo apresenta as melhores métricas de conversão (4,2% em média) e engagement elevado. São canais maduros que já passaram por otimização...",
      "key_insights": [
        "Google Organic: 35% de tráfego, 60% de conversões",
        "Cluster de alta conversão tem 2x mais ROI que demais",
        "Direct traffic apresenta baixo engagement, investigar causas"
      ],
      "data_references": {
        "clusters_identified": 3,
        "top_channel": "google/organic"
      }
    }
  ],
  
  "recommendations": [
    {
      "priority": "high",
      "category": "traffic",
      "action": "Aumentar investimento em Google Ads para keywords do Cluster 0 (alto ROI)",
      "rationale": "Análise de clustering revelou que keywords deste grupo têm CTR de 8,5% e custo 30% menor que média. ROI projetado de 320%."
    },
    {
      "priority": "high",
      "category": "engagement",
      "action": "Otimizar páginas do Cluster 2 que apresentam alta rejeição (65%)",
      "rationale": "12 páginas identificadas recebem tráfego qualificado mas perdem 65% dos visitantes. Quick wins: melhorar CTAs e velocidade de carregamento."
    },
    {
      "priority": "medium",
      "category": "conversions",
      "action": "Criar landing pages específicas para tráfego do Facebook",
      "rationale": "Facebook traz volume interessante mas converte apenas 0,8%. Hipótese: expectativa do visitante não alinha com conteúdo genérico."
    }
  ],
  
  "metadata": {
    "data_sources": ["kpis", "channel_clusters", "keyword_clusters", "page_clusters", "correlations"],
    "ml_models_used": ["channel_profiling", "keyword_clustering", "page_segmentation"],
    "confidence_score": 0.87,
    "agent_model": "gpt-5-mini",
    "generation_timestamp": "2024-01-22T15:30:05Z",
    "tokens_used": {
      "prompt": 2150,
      "completion": 1420,
      "total": 3570
    }
  }
}
```

---

## 17. RESUMO EXECUTIVO DO PLANO

### O Que Vai Ser Construído
Um endpoint REST que recebe parâmetros de período e nível de detalhe, coleta dados de 4 endpoints de análise ML existentes, e utiliza um agente Agno (OpenAI GPT-5-mini) para gerar um relatório narrativo compreensível com insights acionáveis e recomendações priorizadas.

### Por Que É Importante
- **Problema Atual**: Usuários veem apenas números brutos em JSON
- **Solução**: Relatórios narrativos que contam uma história com os dados
- **Valor**: Democratiza acesso a insights de ML para não-técnicos

### Tecnologias Principais
- **Agno**: Framework multi-agent AI (setup simples, output schemas)
- **OpenAI GPT-5-mini**: Modelo de linguagem (custo/benefício ideal)
- **FastAPI**: Endpoint REST assíncrono
- **Pydantic**: Validação de schemas de entrada/saída

### Complexidade e Esforço
- **Complexidade**: Média (principalmente integração e prompt engineering)
- **Tempo Estimado**: 2-3 dias de desenvolvimento + 1 dia de testes
- **LOC Estimado**: ~400-500 linhas (endpoint + helpers + testes)

### Custos Operacionais
- **API OpenAI**: ~$0.0012 por relatório (~$1.20 por 1000 relatórios)
- **Infraestrutura**: Negligível (mesmo servidor FastAPI)
- **Total Mensal** (estimado 5000 relatórios): **~$6**

### Próximos Passos Imediatos
1. ✅ **Aprovação deste plano**
2. 🔧 Instalar dependências (agno, openai)
3. 🧪 Criar protótipo rápido (teste de conceito)
4. 🏗️ Implementar endpoint completo
5. 🧬 Testes e validação
6. 🚀 Deploy

---

## 18. PERGUNTAS E DECISÕES PENDENTES

### Para o Usuário Decidir

1. **Modelo OpenAI**
   - gpt-5-mini (mais rápido, mais barato, ~$1.20/1000 relatórios) ✅ RECOMENDADO
   - gpt-4o (mais inteligente, mais caro, ~$15/1000 relatórios)
   - Qual preferir?

2. **Idioma Padrão**
   - Português (pt-br) ✅ ASSUMIDO
   - Permitir múltiplos idiomas? (en, es, etc.)

3. **Nível de Detalhe Padrão**
   - Executive (resumido) ✅ RECOMENDADO
   - Detailed (completo)
   - Technical (com explicações ML)

4. **Cache**
   - Cachear relatórios por quanto tempo? (sugestão: 1h)
   - Cache por usuário ou global?

5. **Rate Limiting**
   - Quantos relatórios por usuário por hora? (sugestão: 5)

6. **Exportação**
   - Apenas JSON?
   - Incluir PDF na Fase 2?
   - Markdown puro como opção?

---

## 19. CONCLUSÃO

Este plano detalha a construção de um endpoint de **relatórios inteligentes** que transforma dados analíticos brutos em narrativas compreensíveis usando **Agno + OpenAI GPT**. 

### Destaques:
✅ **Arquitetura clara**: Coleta → Formatação → Agno → Resposta estruturada  
✅ **Custo acessível**: ~$0.001 por relatório  
✅ **Tempo de resposta**: 7-13 segundos  
✅ **Escalável**: Cache + rate limiting  
✅ **Evolutivo**: Roadmap de 4 fases  
✅ **Testável**: Casos de teste definidos  

### Decisão Necessária:
🔴 **Aprovação para implementar** (ou ajustes no plano)

---

**Documento criado em**: 22/01/2024  
**Versão**: 1.0  
**Autor**: Assistente IA  
**Status**: ⏳ Aguardando aprovação
