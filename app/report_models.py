"""
Modelos Pydantic e funções auxiliares para geração de relatórios com Agno.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta


# ===== MODELOS DE INPUT =====

class ReportRequest(BaseModel):
    """Request para geração de relatório."""
    period_days: int = Field(default=30, ge=1, le=365, description="Período de análise em dias")
    focus_areas: Optional[List[str]] = Field(
        default=None, 
        description="Áreas de foco: traffic, conversions, engagement, keywords"
    )
    detail_level: str = Field(
        default="executive", 
        description="Nível de detalhe: executive, detailed, technical"
    )
    language: str = Field(default="pt-br", description="Idioma do relatório")


# ===== MODELOS DE OUTPUT =====

class ReportSection(BaseModel):
    """Seção individual do relatório."""
    title: str = Field(..., description="Título da seção")
    content: str = Field(..., description="Conteúdo narrativo da seção")
    key_insights: List[str] = Field(..., description="Insights principais (lista de 2-4 insights)")


class Recommendation(BaseModel):
    """Recomendação estratégica."""
    priority: str = Field(..., description="Prioridade: high, medium, low")
    category: str = Field(..., description="Categoria: traffic, conversions, engagement, keywords")
    action: str = Field(..., description="Ação específica e acionável")
    rationale: str = Field(..., description="Justificativa baseada em dados")


class AnalyticsReport(BaseModel):
    """Estrutura completa do relatório analítico."""
    executive_summary: str = Field(..., description="Resumo executivo do período")
    sections: List[ReportSection] = Field(..., description="Seções do relatório (5 seções)")
    recommendations: List[Recommendation] = Field(..., description="Recomendações priorizadas (5-8 recomendações)")
    
    class Config:
        json_schema_extra = {
            "required": ["executive_summary", "sections", "recommendations"]
        }


# ===== FUNÇÕES AUXILIARES DE FORMATAÇÃO =====

def format_kpis(kpis: dict) -> str:
    """Formata KPIs em texto legível para o agente."""
    # A API retorna em camelCase, precisamos mapear
    total_pages = kpis.get('totalPaginas', kpis.get('total_pages', 0))
    total_sessions = kpis.get('sessoesTotais', kpis.get('total_sessions', 0))
    total_conversions = kpis.get('conversoesTotais', kpis.get('total_conversions', 0))
    bounce_rate = kpis.get('mediaBounceRate', kpis.get('bounce_rate', 0)) * 100  # Converter para %
    avg_duration = kpis.get('mediaSessionDuration', kpis.get('avg_session_duration', 0))
    
    # Calcular taxa de conversão
    conversion_rate = (total_conversions / total_sessions * 100) if total_sessions > 0 else 0
    
    return f"""
**Métricas Principais do Período:**
- Total de Páginas Únicas: {total_pages:,}
- Total de Sessões: {total_sessions:,}
- Total de Conversões: {total_conversions:,}
- Taxa de Conversão: {conversion_rate:.2f}%
- Taxa de Rejeição (Bounce Rate): {bounce_rate:.2f}%
- Duração Média da Sessão: {avg_duration:.1f} segundos
"""


def format_channel_clusters(clusters: dict) -> str:
    """Formata clusters de canais em texto estruturado."""
    if not clusters or 'clusters' not in clusters:
        return "Dados de clusters de canais não disponíveis."
    
    output = ["**Clusters de Canais de Tráfego (K-Means):**\n"]
    
    for cluster_id, cluster_data in clusters['clusters'].items():
        channels_list = cluster_data.get('channels', [])
        channels_preview = ', '.join(channels_list[:5])
        if len(channels_list) > 5:
            channels_preview += f" (+ {len(channels_list) - 5} outros)"
        
        avg_metrics = cluster_data.get('avg_metrics', {})
        
        output.append(f"""
### Cluster {cluster_id}
- **Tamanho**: {cluster_data.get('count', 0)} canais
- **Canais**: {channels_preview}
- **Características Médias**:
  * Sessões: {avg_metrics.get('sessions', 0):.0f}
  * Usuários Ativos: {avg_metrics.get('active_users', 0):.0f}
  * Novos Usuários: {avg_metrics.get('new_users', 0):.0f}
  * Visualizações: {avg_metrics.get('screen_page_views', 0):.0f}
  * Duração Média: {avg_metrics.get('avg_duration', 0):.0f}s
""")
    
    return "\n".join(output)


def format_keyword_clusters(clusters: dict) -> str:
    """Formata clusters de keywords em texto estruturado."""
    if not clusters or 'clusters' not in clusters:
        return "Dados de clusters de keywords não disponíveis."
    
    output = ["**Clusters de Keywords/Queries (K-Means):**\n"]
    
    for cluster_id, cluster_data in clusters['clusters'].items():
        queries_list = cluster_data.get('queries', [])
        queries_preview = ', '.join([f'"{q}"' for q in queries_list[:5]])
        if len(queries_list) > 5:
            queries_preview += f" (+ {len(queries_list) - 5} outras)"
        
        avg_metrics = cluster_data.get('avg_metrics', {})
        
        output.append(f"""
### Cluster {cluster_id}
- **Tamanho**: {cluster_data.get('count', 0)} keywords
- **Queries Exemplo**: {queries_preview}
- **Características Médias**:
  * Clicks: {avg_metrics.get('clicks', 0):.1f}
  * Impressões: {avg_metrics.get('impressions', 0):.1f}
  * CTR: {avg_metrics.get('ctr', 0):.2f}%
  * Posição Média: {avg_metrics.get('position', 0):.1f}
""")
    
    return "\n".join(output)


def format_page_clusters(clusters: dict) -> str:
    """Formata clusters de páginas em texto estruturado."""
    if not clusters or 'clusters' not in clusters:
        return "Dados de clusters de páginas não disponíveis."
    
    output = ["**Clusters de Páginas (K-Means):**\n"]
    
    for cluster_id, cluster_data in clusters['clusters'].items():
        pages_list = cluster_data.get('pages', [])
        pages_preview = ', '.join(pages_list[:5])
        if len(pages_list) > 5:
            pages_preview += f" (+ {len(pages_list) - 5} outras)"
        
        avg_metrics = cluster_data.get('avg_metrics', {})
        
        output.append(f"""
### Cluster {cluster_id}
- **Tamanho**: {cluster_data.get('count', 0)} páginas
- **Páginas Exemplo**: {pages_preview}
- **Características Médias**:
  * Taxa de Engajamento: {avg_metrics.get('engagement_rate', 0):.2f}%
  * Eventos por Sessão: {avg_metrics.get('event_count', 0):.1f}
  * Duração Média: {avg_metrics.get('avg_duration', 0):.1f}s
""")
    
    return "\n".join(output)


def format_correlations(correlations: dict) -> str:
    """Formata matriz de correlação destacando correlações significativas."""
    if not correlations:
        return "Dados de correlação não disponíveis."
    
    output = ["**Correlações Significativas entre Métricas (|r| > 0.3):**\n"]
    
    significant = []
    for metric1, corr_dict in correlations.items():
        if not isinstance(corr_dict, dict):
            continue
        for metric2, value in corr_dict.items():
            if metric1 >= metric2:  # Evita duplicatas
                continue
            if isinstance(value, (int, float)) and abs(value) > 0.3:
                direction = "positiva" if value > 0 else "negativa"
                strength = "forte" if abs(value) > 0.7 else "moderada"
                significant.append(
                    f"- **{metric1}** ↔ **{metric2}**: {value:.2f} (correlação {direction} {strength})"
                )
    
    if significant:
        output.extend(significant)
    else:
        output.append("- Nenhuma correlação significativa detectada (|r| > 0.3)")
    
    return "\n".join(output)


def calculate_confidence_score(data_collection: dict) -> float:
    """
    Calcula score de confiança do relatório baseado em:
    - Completude dos dados (40%)
    - Qualidade dos clusters (30%) 
    - Volume de dados (30%)
    """
    # Completude: quantas fontes têm dados
    sources = ['kpis', 'channel_clusters', 'keyword_clusters', 'page_clusters', 'correlations']
    available_sources = sum(1 for s in sources if data_collection.get(s))
    completeness = available_sources / len(sources)
    
    # Qualidade dos clusters: média de elementos por cluster
    cluster_quality = 0.5  # Default
    total_clusters = 0
    total_elements = 0
    
    for cluster_type in ['channel_clusters', 'keyword_clusters', 'page_clusters']:
        cluster_data = data_collection.get(cluster_type, {})
        if 'clusters' in cluster_data:
            for cluster_info in cluster_data['clusters'].values():
                total_clusters += 1
                total_elements += cluster_info.get('count', 0)
    
    if total_clusters > 0:
        avg_cluster_size = total_elements / total_clusters
        cluster_quality = min(avg_cluster_size / 20, 1.0)  # Normaliza para 0-1
    
    # Volume de dados: baseado em sessões
    kpis = data_collection.get('kpis', {})
    total_sessions = kpis.get('total_sessions', 0)
    data_volume = min(total_sessions / 1000, 1.0)  # Normaliza para 0-1
    
    # Fórmula final
    confidence = (completeness * 0.4) + (cluster_quality * 0.3) + (data_volume * 0.3)
    
    return round(confidence, 2)
