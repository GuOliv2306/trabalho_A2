from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List, Literal
from contextlib import asynccontextmanager
import re
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import uuid
from datetime import date, datetime, timedelta
import logging
import asyncio
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente do .env
load_dotenv()

# Adiciona src ao path
sys.path.append(str(Path(__file__).parent.parent))

# ✅ BANCO DE DADOS DIRETO - Não depende de GA4/GSC APIs
# db_storage acessa DuckDB diretamente, pronto para receber dados simulados
from src.collectors.db_storage import GA4DatabaseStorage

# ✅ MÓDULOS DE MACHINE LEARNING
from src.ml import ChannelProfiler, KeywordClusterer

# ✅ MÉTODOS DIGITAIS
from src.digital_methods import analysis, wikipedia

# ✅ QUASE-EXPERIMENTOS
from src.quasi_experiments import analysis as quasi

# ✅ MÓDULOS DE RELATÓRIO AGNO
from app.report_models import (
    ReportRequest, 
    AnalyticsReport,
    format_kpis,
    format_channel_clusters,
    format_keyword_clusters,
    format_digital_methods,
    format_correlations,
    calculate_confidence_score
)
from app.report_agent import create_report_agent

# Logger
logger = logging.getLogger(__name__)

# ✅ Instância global do banco - PRONTA PARA DADOS SIMULADOS
# Quando implementar o simulador, ele deve popular este mesmo banco
db = None

def get_db():
    """Lazy initialization do banco de dados."""
    global db
    if db is None:
        db = GA4DatabaseStorage()
    return db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação."""
    # Startup
    yield
    # Shutdown
    if db is not None:
        db.close()


app = FastAPI(
    title="Dashboard Analytics API",
    description="API de analytics e métodos digitais (Wikipedia real + GA4/GSC simulados)",
    version="1.0.0",
    lifespan=lifespan
)

# CORS para frontend React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== HEALTH CHECK =====

@app.get("/health")
async def health():
    """Endpoint simples para checar se a API está no ar."""
    return {"status": "ok"}


# ===== DASHBOARD OVERVIEW =====

@app.get("/api/v1/overview/kpis", tags=["Dashboard"])
async def get_kpis():
    """
    Retorna KPIs principais do site (cards do dashboard).
    
    - **totalPaginas**: Total de páginas únicas rastreadas
    - **sessoesTotais**: Soma de todas as sessões (GA4)
    - **conversoesTotais**: Soma de todas as conversões
    - **mediaBounceRate**: Taxa média de rejeição
    - **mediaSessionDuration**: Duração média de sessão (segundos)
    """
    try:
        # Total de páginas únicas
        total_paginas = get_db().query_df("""
            SELECT COUNT(DISTINCT page_path) as total
            FROM engagement
            WHERE page_path IS NOT NULL
        """)
        
        # Sessões totais
        sessoes_totais = get_db().query_df("""
            SELECT COALESCE(SUM(sessions), 0) as total
            FROM traffic
        """)
        
        # Conversões totais
        conversoes_totais = get_db().query_df("""
            SELECT COALESCE(SUM(key_events), 0) as total
            FROM conversions
        """)
        
        # Taxa de rejeição média (calculada via engagement)
        bounce_rate = get_db().query_df("""
            SELECT 
                COALESCE(
                    1.0 - (SUM(engaged_sessions)::FLOAT / NULLIF(SUM(engaged_sessions + (1 - engagement_rate) * engaged_sessions), 0)),
                    0
                ) as avg_bounce_rate
            FROM engagement
        """)
        
        # Duração média de sessão
        avg_duration = get_db().query_df("""
            SELECT COALESCE(AVG(average_session_duration), 0) as avg_duration
            FROM traffic
            WHERE average_session_duration IS NOT NULL
        """)
        
        return {
            "totalPaginas": int(total_paginas['total'].iloc[0]) if not total_paginas.empty else 0,
            "sessoesTotais": int(sessoes_totais['total'].iloc[0]) if not sessoes_totais.empty else 0,
            "conversoesTotais": int(conversoes_totais['total'].iloc[0]) if not conversoes_totais.empty else 0,
            "mediaBounceRate": round(float(bounce_rate['avg_bounce_rate'].iloc[0]), 2) if not bounce_rate.empty else 0.0,
            "mediaSessionDuration": round(float(avg_duration['avg_duration'].iloc[0]), 2) if not avg_duration.empty else 0.0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular KPIs: {str(e)}")


# ===== ANÁLISES ESTÁTICAS =====

@app.get("/api/v1/analysis/correlation_matrix", tags=["Análises"])
async def get_correlation_matrix():
    """
    Retorna matriz de correlação entre features e métricas principais.
    
    Calcula correlações entre:
    - Features de engagement: engagement_rate, event_count, session_duration
    - Métricas agregadas por data
    """
    try:
        # Agregação por data (nível temporal - único relacionamento válido)
        df = get_db().query_df("""
            SELECT 
                e.date,
                AVG(e.engagement_rate) as engagement_rate,
                SUM(e.event_count) as event_count,
                AVG(e.average_session_duration) as avg_session_duration,
                SUM(e.engaged_sessions) as engaged_sessions,
                (SELECT SUM(sessions) FROM traffic t WHERE t.date = e.date) as sessions,
                (SELECT SUM(screen_page_views) FROM traffic t WHERE t.date = e.date) as page_views,
                (SELECT SUM(key_events) FROM conversions c WHERE c.date = e.date) as conversions
            FROM engagement e
            WHERE e.date IS NOT NULL
            GROUP BY e.date
            HAVING SUM(e.event_count) > 5
        """)
        
        if df.empty or len(df) < 2:
            return {
                "conversions": {"sessions": 0, "page_views": 0, "avg_session_duration": 0},
                "bounceRate": {"sessions": 0, "page_views": 0, "avg_session_duration": 0},
                "averageSessionDuration": {"sessions": 0, "page_views": 0, "conversions": 0}
            }
        
        # Calcula correlações usando pandas e substitui NaN por 0
        import numpy as np
        corr_matrix = df[['sessions', 'page_views', 'avg_session_duration', 'conversions', 'engagement_rate']].corr().fillna(0)
        
        def safe_float(value):
            """Converte para float e substitui NaN/Inf por 0."""
            val = float(value)
            return 0.0 if (np.isnan(val) or np.isinf(val)) else round(val, 2)
        
        return {
            "conversions": {
                "sessions": safe_float(corr_matrix.loc['conversions', 'sessions']) if 'conversions' in corr_matrix.index else 0,
                "pageViews": safe_float(corr_matrix.loc['conversions', 'page_views']) if 'conversions' in corr_matrix.index else 0,
                "avgSessionDuration": safe_float(corr_matrix.loc['conversions', 'avg_session_duration']) if 'conversions' in corr_matrix.index else 0
            },
            "engagementRate": {
                "sessions": safe_float(corr_matrix.loc['engagement_rate', 'sessions']) if 'engagement_rate' in corr_matrix.index else 0,
                "pageViews": safe_float(corr_matrix.loc['engagement_rate', 'page_views']) if 'engagement_rate' in corr_matrix.index else 0,
                "avgSessionDuration": safe_float(corr_matrix.loc['engagement_rate', 'avg_session_duration']) if 'engagement_rate' in corr_matrix.index else 0
            },
            "averageSessionDuration": {
                "sessions": safe_float(corr_matrix.loc['avg_session_duration', 'sessions']) if 'avg_session_duration' in corr_matrix.index else 0,
                "pageViews": safe_float(corr_matrix.loc['avg_session_duration', 'page_views']) if 'avg_session_duration' in corr_matrix.index else 0,
                "conversions": safe_float(corr_matrix.loc['avg_session_duration', 'conversions']) if 'avg_session_duration' in corr_matrix.index else 0
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular correlações: {str(e)}")


# ===== MACHINE LEARNING ENDPOINTS =====

@app.get("/api/v1/ml/channel_clusters", tags=["Machine Learning"])
async def get_channel_clusters(n_clusters: int = Query(3, ge=2, le=10, description="Número de clusters")):
    """
    Aplica clustering K-Means em canais de tráfego (source/medium).
    
    Usa o módulo **ChannelProfiler** para agrupar canais por similaridade de performance.
    
    - **n_clusters**: Número de clusters desejado (padrão: 3)
    
    Retorna:
    - Dados agregados com cluster_id
    - Centros dos clusters
    - Resumo estatístico dos segmentos
    """
    try:
        # Busca dados agregados de tráfego por source/medium
        df = get_db().query_df("""
            SELECT 
                session_source as source,
                session_medium as medium,
                SUM(sessions) as sessions,
                SUM(active_users) as activeUsers,
                SUM(new_users) as newUsers,
                SUM(screen_page_views) as screenPageViews,
                AVG(average_session_duration) as averageSessionDuration
            FROM traffic
            WHERE session_source IS NOT NULL AND session_medium IS NOT NULL
            GROUP BY session_source, session_medium
            HAVING SUM(sessions) > 5
        """)
        
        if df.empty or len(df) < n_clusters:
            # Para geração de relatórios, retorna estrutura vazia ao invés de erro
            logger.warning(f"Dados insuficientes para clustering de canais: {len(df)} canais encontrados (mínimo: {n_clusters})")
            return {
                "algoritmo": "K-Means Clustering",
                "n_clusters": n_clusters,
                "total_canais": 0,
                "clusters": {},
                "warning": f"Dados insuficientes. Necessário pelo menos {n_clusters} canais com mais de 5 sessões."
            }
        
        # Aplica o ChannelProfiler
        profiler = ChannelProfiler(n_clusters=n_clusters)
        df_clustered = profiler.fit_transform(df)
        
        # Prepara resposta com estrutura compatível com report_models.py
        clusters_dict = {}
        for cluster_id in range(n_clusters):
            cluster_data = df_clustered[df_clustered['cluster'] == cluster_id]
            clusters_dict[str(cluster_id)] = {
                'count': len(cluster_data),
                'channels': [f"{row['source']}/{row['medium']}" for _, row in cluster_data.iterrows()],
                'avg_metrics': {
                    'sessions': float(cluster_data['sessions'].mean()),
                    'active_users': float(cluster_data.get('activeUsers', cluster_data.get('active_users', pd.Series([0]))).mean()),
                    'new_users': float(cluster_data.get('newUsers', cluster_data.get('new_users', pd.Series([0]))).mean()),
                    'screen_page_views': float(cluster_data.get('screenPageViews', cluster_data.get('screen_page_views', pd.Series([0]))).mean()),
                    'avg_duration': float(cluster_data.get('averageSessionDuration', cluster_data.get('average_session_duration', pd.Series([0]))).mean())
                }
            }
        
        return {
            "algoritmo": "K-Means Clustering",
            "n_clusters": n_clusters,
            "total_canais": len(df_clustered),
            "clusters": clusters_dict,
            "canais": df_clustered[['source', 'medium', 'sessions', 'cluster']].to_dict('records'),
            "cluster_centers": profiler.get_cluster_centers().to_dict('records'),
            "segment_summary": profiler.get_segment_summary(df_clustered).to_dict('records')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao aplicar clustering de canais: {str(e)}")


@app.get("/api/v1/ml/keyword_clusters", tags=["Machine Learning"])
async def get_keyword_clusters(n_clusters: int = Query(4, ge=2, le=10, description="Número de clusters")):
    """
    Aplica clustering K-Means em palavras-chave do Google Search Console.
    
    Usa o módulo **KeywordClusterer** para agrupar queries por similaridade de performance.
    
    - **n_clusters**: Número de clusters desejado (padrão: 4)
    
    Retorna:
    - Keywords com cluster_id
    - Centros dos clusters
    - Resumo estatístico dos segmentos
    """
    try:
        # Busca dados agregados de queries do GSC
        df = get_db().query_df("""
            SELECT 
                query,
                SUM(clicks) as clicks,
                SUM(impressions) as impressions,
                AVG(ctr) as ctr,
                AVG(position) as position
            FROM gsc_query_performance
            WHERE query IS NOT NULL
            GROUP BY query
            HAVING SUM(impressions) > 50
        """)
        
        if df.empty or len(df) < n_clusters:
            # Para geração de relatórios, retorna estrutura vazia ao invés de erro
            logger.warning(f"Dados insuficientes para clustering de keywords: {len(df)} queries encontradas (mínimo: {n_clusters})")
            return {
                "algoritmo": "K-Means Clustering",
                "n_clusters": n_clusters,
                "total_keywords": 0,
                "clusters": {},
                "warning": f"Dados insuficientes. Necessário pelo menos {n_clusters} queries com mais de 50 impressões."
            }
        
        # Aplica o KeywordClusterer
        clusterer = KeywordClusterer(n_clusters=n_clusters)
        df_clustered = clusterer.fit_transform(df)
        
        # Prepara resposta com estrutura compatível com report_models.py
        clusters_dict = {}
        for cluster_id in range(n_clusters):
            cluster_data = df_clustered[df_clustered['cluster'] == cluster_id]
            clusters_dict[str(cluster_id)] = {
                'count': len(cluster_data),
                'queries': cluster_data['query'].tolist(),
                'avg_metrics': {
                    'clicks': float(cluster_data['clicks'].mean()),
                    'impressions': float(cluster_data['impressions'].mean()),
                    'ctr': float(cluster_data['ctr'].mean() * 100),  # Converter para %
                    'position': float(cluster_data['position'].mean())
                }
            }
        
        return {
            "algoritmo": "K-Means Clustering",
            "n_clusters": n_clusters,
            "total_keywords": len(df_clustered),
            "clusters": clusters_dict,
            "keywords": df_clustered[['query', 'clicks', 'impressions', 'ctr', 'position', 'cluster']].to_dict('records'),
            "cluster_centers": clusterer.get_cluster_centers().to_dict('records'),
            "segment_summary": clusterer.get_segment_summary(df_clustered).to_dict('records')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao aplicar clustering de keywords: {str(e)}")


# ===== VISUALIZAÇÃO COMPLETA DOS DADOS =====

@app.get("/api/v1/data/all", tags=["Dados Brutos"])
async def get_all_data(
    limit: int = Query(10, ge=1, le=1000, description="Limite de registros por tabela")
):
    """
    Retorna uma visão completa de todos os dados do banco.
    
    - **limit**: Número máximo de registros a retornar por tabela (padrão: 10, máx: 1000)
    
    Retorna dados de todas as 8 tabelas:
    - GA4: traffic, conversions, engagement
    - GSC: query_performance, page_performance, country_performance, device_performance, date_performance
    """
    try:
        result = {
            "resumo": {},
            "ga4": {},
            "gsc": {}
        }
        
        # ===== RESUMO GERAL =====
        tabelas = [
            "traffic",
            "conversions", 
            "engagement",
            "gsc_query_performance",
            "gsc_page_performance",
            "gsc_country_performance",
            "gsc_device_performance",
            "gsc_date_performance"
        ]
        
        resumo_info = []
        for tabela in tabelas:
            count_df = get_db().query_df(f"SELECT COUNT(*) as total FROM {tabela}")
            total = int(count_df['total'].iloc[0]) if not count_df.empty else 0
            
            # Pega datas min/max se existir coluna date
            try:
                date_df = get_db().query_df(f"SELECT MIN(date) as min_date, MAX(date) as max_date FROM {tabela}")
                if not date_df.empty and date_df['min_date'].iloc[0] is not None:
                    periodo = f"{date_df['min_date'].iloc[0]} a {date_df['max_date'].iloc[0]}"
                else:
                    periodo = "N/A"
            except:
                periodo = "N/A"
            
            resumo_info.append({
                "tabela": tabela,
                "registros": total,
                "periodo": periodo
            })
        
        result["resumo"]["tabelas"] = resumo_info
        result["resumo"]["total_registros"] = sum([t["registros"] for t in resumo_info])
        
        # ===== DADOS GA4 =====
        
        # Traffic
        traffic_df = get_db().query_df(f"""
            SELECT *
            FROM traffic
            ORDER BY date DESC, sessions DESC
            LIMIT {limit}
        """)
        result["ga4"]["traffic"] = {
            "total": int(get_db().query_df("SELECT COUNT(*) as total FROM traffic")['total'].iloc[0]),
            "dados": traffic_df.to_dict('records') if not traffic_df.empty else []
        }
        
        # Conversions
        conversions_df = get_db().query_df(f"""
            SELECT *
            FROM conversions
            ORDER BY date DESC, key_events DESC
            LIMIT {limit}
        """)
        result["ga4"]["conversions"] = {
            "total": int(get_db().query_df("SELECT COUNT(*) as total FROM conversions")['total'].iloc[0]),
            "dados": conversions_df.to_dict('records') if not conversions_df.empty else []
        }
        
        # Engagement
        engagement_df = get_db().query_df(f"""
            SELECT *
            FROM engagement
            ORDER BY date DESC, engaged_sessions DESC
            LIMIT {limit}
        """)
        result["ga4"]["engagement"] = {
            "total": int(get_db().query_df("SELECT COUNT(*) as total FROM engagement")['total'].iloc[0]),
            "dados": engagement_df.to_dict('records') if not engagement_df.empty else []
        }
        
        # ===== DADOS GSC =====
        
        # Query Performance
        query_df = get_db().query_df(f"""
            SELECT *
            FROM gsc_query_performance
            ORDER BY clicks DESC
            LIMIT {limit}
        """)
        result["gsc"]["query_performance"] = {
            "total": int(get_db().query_df("SELECT COUNT(*) as total FROM gsc_query_performance")['total'].iloc[0]),
            "dados": query_df.to_dict('records') if not query_df.empty else []
        }
        
        # Page Performance
        page_df = get_db().query_df(f"""
            SELECT *
            FROM gsc_page_performance
            ORDER BY clicks DESC
            LIMIT {limit}
        """)
        result["gsc"]["page_performance"] = {
            "total": int(get_db().query_df("SELECT COUNT(*) as total FROM gsc_page_performance")['total'].iloc[0]),
            "dados": page_df.to_dict('records') if not page_df.empty else []
        }
        
        # Country Performance
        country_df = get_db().query_df(f"""
            SELECT *
            FROM gsc_country_performance
            ORDER BY clicks DESC
            LIMIT {limit}
        """)
        result["gsc"]["country_performance"] = {
            "total": int(get_db().query_df("SELECT COUNT(*) as total FROM gsc_country_performance")['total'].iloc[0]),
            "dados": country_df.to_dict('records') if not country_df.empty else []
        }
        
        # Device Performance
        device_df = get_db().query_df(f"""
            SELECT *
            FROM gsc_device_performance
            ORDER BY clicks DESC
            LIMIT {limit}
        """)
        result["gsc"]["device_performance"] = {
            "total": int(get_db().query_df("SELECT COUNT(*) as total FROM gsc_device_performance")['total'].iloc[0]),
            "dados": device_df.to_dict('records') if not device_df.empty else []
        }
        
        # Date Performance (Série Temporal)
        date_df = get_db().query_df(f"""
            SELECT *
            FROM gsc_date_performance
            ORDER BY date DESC
            LIMIT {limit}
        """)
        result["gsc"]["date_performance"] = {
            "total": int(get_db().query_df("SELECT COUNT(*) as total FROM gsc_date_performance")['total'].iloc[0]),
            "dados": date_df.to_dict('records') if not date_df.empty else []
        }
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar dados: {str(e)}")


@app.get("/api/v1/data/summary", tags=["Dados Brutos"])
async def get_data_summary():
    """
    Retorna apenas um resumo estatístico dos dados sem os registros completos.
    
    Útil para verificar rapidamente o estado do banco de dados.
    """
    try:
        result = {
            "database": "ga4_data.duckdb",
            "tabelas": []
        }
        
        tabelas_info = [
            ("traffic", "Tráfego GA4", ["sessions", "active_users", "screen_page_views"]),
            ("conversions", "Conversões GA4", ["key_events", "event_count"]),
            ("engagement", "Engajamento GA4", ["engaged_sessions", "engagement_rate"]),
            ("gsc_query_performance", "Queries GSC", ["clicks", "impressions", "ctr"]),
            ("gsc_page_performance", "Páginas GSC", ["clicks", "impressions"]),
            ("gsc_country_performance", "Países GSC", ["clicks", "impressions"]),
            ("gsc_device_performance", "Dispositivos GSC", ["clicks", "impressions"]),
            ("gsc_date_performance", "Série Temporal GSC", ["clicks", "impressions"])
        ]
        
        for tabela, descricao, metricas_chave in tabelas_info:
            # Contagem total
            count_df = get_db().query_df(f"SELECT COUNT(*) as total FROM {tabela}")
            total = int(count_df['total'].iloc[0]) if not count_df.empty else 0
            
            # Período
            try:
                date_df = get_db().query_df(f"SELECT MIN(date) as min_date, MAX(date) as max_date FROM {tabela}")
                if not date_df.empty and date_df['min_date'].iloc[0] is not None:
                    min_date = str(date_df['min_date'].iloc[0])
                    max_date = str(date_df['max_date'].iloc[0])
                else:
                    min_date = max_date = None
            except:
                min_date = max_date = None
            
            # Estatísticas das métricas principais
            stats = {}
            for metrica in metricas_chave:
                try:
                    stats_df = get_db().query_df(f"""
                        SELECT 
                            COALESCE(SUM({metrica}), 0) as total,
                            COALESCE(AVG({metrica}), 0) as media,
                            COALESCE(MAX({metrica}), 0) as maximo
                        FROM {tabela}
                    """)
                    if not stats_df.empty:
                        stats[metrica] = {
                            "total": float(stats_df['total'].iloc[0]),
                            "media": round(float(stats_df['media'].iloc[0]), 2),
                            "maximo": float(stats_df['maximo'].iloc[0])
                        }
                except:
                    stats[metrica] = {"total": 0, "media": 0, "maximo": 0}
            
            result["tabelas"].append({
                "nome": tabela,
                "descricao": descricao,
                "registros": total,
                "periodo": {
                    "inicio": min_date,
                    "fim": max_date
                },
                "metricas": stats
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar resumo: {str(e)}")




# ===== MÉTODOS DIGITAIS =====
# Objetos nativos do meio (revisões, reversões, links, ranking). Toda resposta traz
# `leitura_do_meio`: o que o dado diz sobre a plataforma que o produziu.

# vira hostname ({lang}.wikipedia.org): só letras e hífens, nunca ponto ou barra
WIKI_LANG = r"^[a-z]{2,12}(-[a-z]{2,12}){0,2}$"


class WikipediaCollectRequest(BaseModel):
    """Request para coletar um tema na Wikipedia a partir de uma página-semente."""
    seed: str = Field(..., min_length=1, max_length=255, description="Título do artigo-semente")
    lang: str = Field(default="pt", pattern=WIKI_LANG, description="Edição linguística")
    max_pages: int = Field(default=10, ge=1, le=25, description="Semente + vizinhos de link recíproco")
    titles: Optional[List[str]] = Field(default=None, max_length=24,
                                        description="Corpus curado: substitui a descoberta automática de vizinhos")
    rev_limit: int = Field(default=500, ge=50, le=2000, description="Revisões mais recentes por artigo")
    edition_langs: List[str] = Field(default=["en", "es", "fr", "de"], max_length=10)
    admin_key: Optional[str] = Field(default=None, description="Chave de administrador (configurar em .env)")

    @field_validator("seed")
    @classmethod
    def _one_title(cls, v: str) -> str:
        # "|" e U+001F separam títulos na API da Wikipedia: aceitar burlaria os limites de artigos por coleta
        if "|" in v or not v.strip() or any(ord(c) < 32 for c in v):
            raise ValueError("título inválido (vazio, com '|' ou com caractere de controle)")
        return v

    @field_validator("titles")
    @classmethod
    def _titles(cls, v):
        return None if v is None else [cls._one_title(t) for t in v]


def _wiki_df(sql: str, params: list) -> pd.DataFrame:
    return get_db().conn.execute(sql, params).fetchdf()


def _wiki_tag_era(lang: str):
    """Primeira tag de reversão observada no corpus do idioma (None se não houver)."""
    return get_db().conn.execute(
        """SELECT MIN("timestamp") FROM wiki_revisions
           WHERE lang = ? AND (tags LIKE '%mw-reverted%' OR tags LIKE '%mw-manual-revert%')""", [lang]).fetchone()[0]


@app.post("/api/v1/digital-methods/wikipedia/collect", tags=["Métodos Digitais"])
async def collect_wikipedia(request: WikipediaCollectRequest):
    """
    Coleta dados reais da API pública da Wikipedia e grava no DuckDB.

    Recorte: a página-semente + os artigos que ela linka **e** que linkam de volta,
    ordenados por pageviews dos últimos 30 dias; ou, com `titles`, a semente + essa lista
    curada. Para cada um: histórico de edições.
    Também: links entre os artigos coletados e a semente em outras edições linguísticas.
    """
    admin_key_env = os.getenv("ADMIN_KEY", None)
    if admin_key_env and request.admin_key != admin_key_env:
        raise HTTPException(status_code=403, detail="Acesso negado. ADMIN_KEY inválida ou ausente.")

    langs = [l for l in request.edition_langs if re.fullmatch(WIKI_LANG, l)]
    try:
        # rede fora do event loop; escrita no banco de volta nele (uma conexão DuckDB só)
        data = await asyncio.to_thread(
            wikipedia.collect_topic, seed=request.seed, lang=request.lang, max_pages=request.max_pages,
            rev_limit=request.rev_limit, edition_langs=langs, titles=request.titles,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Falha ao coletar da Wikipedia: {str(e)}")

    try:
        stored = get_db().save_wiki(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gravar coleta: {str(e)}")
    return {
        "seed": data["seed"],
        "lang": data["lang"],
        "articles": [p["title"] for p in data["pages"]],
        "stored": stored,
        "not_found": data.get("not_found", []),
        "criterio_de_recorte": "semente + lista curada (titles)" if request.titles
        else "semente + vizinhos de link recíproco, ordenados por pageviews (30 dias)",
    }


@app.get("/api/v1/digital-methods/wikipedia/edit-history", tags=["Métodos Digitais"])
async def wikipedia_edit_history(title: str = Query(..., description="Título do artigo coletado"),
                                 lang: str = Query("pt")):
    """
    Perfil do histórico de edições de um artigo: quem edita (registrados, anônimos, robôs),
    concentração entre editores, reversões, interface de edição, linha do tempo e picos.
    """
    try:
        revs = _wiki_df("SELECT * FROM wiki_revisions WHERE lang = ? AND title = ?", [lang, title])
        if revs.empty:
            raise HTTPException(status_code=404, detail=f"Artigo '{title}' ({lang}) não coletado. Use POST /wikipedia/collect.")
        # mesma régua da rota /controversy: era das tags do corpus, não só deste artigo
        profile = analysis.edit_history_profile(revs, tagged_era_start=_wiki_tag_era(lang))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar histórico: {str(e)}")
    return {"title": title, "lang": lang, **profile, "leitura_do_meio": analysis.LEITURAS["edit_history"]}


@app.get("/api/v1/digital-methods/wikipedia/controversy", tags=["Métodos Digitais"])
async def wikipedia_controversy(lang: str = Query("pt"),
                                seed: Optional[str] = Query(None, description="Filtra por página-semente"),
                                min_edits: int = Query(20, ge=1, description="Abaixo disso a taxa é marcada low_sample")):
    """
    Cartografia de controvérsia: artigos coletados ordenados por taxa de reversão, com quem
    edita e quanta atenção (pageviews) cada um recebe. Todas as colunas contam só edições
    desde a primeira tag de reversão observada no corpus (`plataforma.tag_era_start`).
    """
    try:
        pages = _wiki_df("""
            SELECT title, MIN(seed) AS seed, COALESCE(MAX(pageviews_30d), 0) AS pageviews_30d,
                   COALESCE(MAX(length), 0) AS length
            FROM wiki_pages WHERE lang = ? AND (? IS NULL OR seed = ?) GROUP BY title
        """, [lang, seed, seed])
        revs = _wiki_df("SELECT * FROM wiki_revisions WHERE lang = ?", [lang])
        era = _wiki_tag_era(lang)
        anon = revs[revs["actor_type"] == "anon"]

        articles = []
        for page in pages.itertuples():
            sampled = revs[revs["title"] == page.title]
            if sampled.empty:
                continue
            in_era = sampled[sampled["timestamp"] >= era] if era is not None else sampled.iloc[0:0]
            p = analysis.edit_history_profile(in_era, tagged_era_start=era)
            has = bool(p["total_edits"])
            articles.append({
                "title": page.title,
                "seed": page.seed,
                "edits_sampled": len(sampled),
                "edits_in_tag_era": len(in_era),
                "low_sample": len(in_era) < min_edits,
                "revert_rate": p["reverts"]["revert_rate"] if has else None,
                "unique_editors": p["unique_editors"] if has else None,
                "anon_share": p["actor_shares"].get("anon", 0.0) if has else None,
                "bot_share": p["actor_shares"].get("bot", 0.0) if has else None,
                "top_editor_share": p["concentration"]["top_editor_share"] if has else None,
                "bursts": len(p["bursts"]) if has else None,
                "pageviews_30d": int(page.pageviews_30d),
                "length": int(page.length),
            })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar coleta: {str(e)}")

    articles.sort(key=lambda a: (a["low_sample"], -(a["revert_rate"] or 0), -a["edits_in_tag_era"], a["title"]))
    return {
        "lang": lang,
        "plataforma": {
            "tag_era_start": pd.Timestamp(era, tz="UTC").isoformat() if era is not None else None,
            "last_anon_edit": pd.Timestamp(anon["timestamp"].max(), tz="UTC").isoformat() if not anon.empty else None,
        },
        "min_edits": min_edits,
        "articles": articles,
        "leitura_do_meio": analysis.LEITURAS["controversy"],
    }


@app.get("/api/v1/digital-methods/wikipedia/link-network", tags=["Métodos Digitais"])
async def wikipedia_link_network(lang: str = Query("pt"),
                                 seed: Optional[str] = Query(None, description="Filtra por página-semente")):
    """Rede dirigida de hiperlinks entre os artigos coletados (nós com grau, arestas, densidade, reciprocidade)."""
    try:
        nodes = _wiki_df("SELECT DISTINCT title FROM wiki_pages WHERE lang = ? AND (? IS NULL OR seed = ?)",
                         [lang, seed, seed])["title"].tolist()
        edges = _wiki_df("SELECT DISTINCT source, target FROM wiki_links WHERE lang = ? AND (? IS NULL OR seed = ?)",
                         [lang, seed, seed])
        network = analysis.link_network(edges, nodes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar rede: {str(e)}")
    return {"lang": lang, **network, "leitura_do_meio": analysis.LEITURAS["link_network"]}


@app.get("/api/v1/digital-methods/wikipedia/editions", tags=["Métodos Digitais"])
async def wikipedia_editions(title: str = Query(..., description="Título da página-semente"),
                             lang: str = Query("pt")):
    """O mesmo artigo em várias edições linguísticas: tamanho e audiência (pageviews 30 dias)."""
    try:
        df = _wiki_df("""
            SELECT lang, title, length, pageviews_30d FROM wiki_editions
            WHERE seed_lang = ? AND seed_title = ? ORDER BY pageviews_30d DESC, lang
        """, [lang, title])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar edições: {str(e)}")
    if df.empty:
        raise HTTPException(status_code=404, detail=f"Semente '{title}' ({lang}) não coletada. Use POST /wikipedia/collect.")
    total = int(df["pageviews_30d"].sum())
    editions = [
        {"lang": r.lang, "title": r.title, "length": int(r.length), "pageviews_30d": int(r.pageviews_30d),
         "pageviews_share": round(r.pageviews_30d / total, 4) if total else 0.0}
        for r in df.itertuples()
    ]
    return {"seed": title, "seed_lang": lang, "editions": editions, "leitura_do_meio": analysis.LEITURAS["editions"]}


@app.get("/api/v1/digital-methods/search/rank-effect", tags=["Métodos Digitais"])
async def search_rank_effect():
    """
    O ranking produz o clique: curva de CTR por posição, fatia de cliques e impressões
    capturada pelo top 3 e correlação de postos entre posição e CTR.
    """
    try:
        df = get_db().query_df("SELECT query, clicks, impressions, position FROM gsc_query_performance")
        result = analysis.rank_effect(df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar buscas: {str(e)}")
    return {**result, "leitura_do_meio": analysis.LEITURAS["rank_effect"]}


@app.get("/api/v1/digital-methods/search/query-network", tags=["Métodos Digitais"])
async def search_query_network():
    """Rede de coocorrência de termos nas consultas de busca (nós = termos, arestas = aparecem na mesma consulta)."""
    try:
        df = get_db().query_df("SELECT query, clicks, impressions FROM gsc_query_performance")
        result = analysis.query_term_network(df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar buscas: {str(e)}")
    return {**result, "leitura_do_meio": analysis.LEITURAS["query_network"]}


# ===== QUASE-EXPERIMENTOS =====
# "A mudança X causou a subida ou a queda?" Cada rota devolve o efeito estimado, o
# efeito verdadeiro do simulador (`true_effect`) e os pressupostos do método.

def _intervention(intervention_id: str) -> dict:
    df = get_db().conn.execute(
        "SELECT * FROM seo_interventions WHERE intervention_id = ?", [intervention_id]).fetchdf()
    if df.empty:
        raise HTTPException(status_code=404, detail=f"Intervenção '{intervention_id}' não encontrada.")
    row = df.iloc[0].to_dict()
    if row["kind"] != "mudanca":
        raise HTTPException(status_code=400, detail="Evento externo: atinge o site inteiro, não há páginas tratadas para comparar.")
    return row


def _intervention_panel(intervention_id: str, metric: str) -> pd.DataFrame:
    """Painel unit, date, y, treated das páginas (tratadas e de controle) de uma intervenção."""
    return get_db().conn.execute(f"""
        SELECT d.page AS unit, d.date, d.{metric} AS y, (m.grp = 'tratado') AS treated
        FROM seo_page_daily d JOIN seo_intervention_pages m ON m.page = d.page
        WHERE m.intervention_id = ?
    """, [intervention_id]).fetchdf()   # metric vem de um Literal validado pelo FastAPI


def _daily_sum(panel: pd.DataFrame, treated: bool) -> pd.DataFrame:
    return panel[panel["treated"] == treated].groupby("date", as_index=False)["y"].sum()


def _quasi(method: str, intervention_id: str, metric: str, run) -> dict:
    """Monta o painel, roda o estimador e embrulha a resposta comum às rotas."""
    info = _intervention(intervention_id)
    try:
        panel = _intervention_panel(intervention_id, metric)
        result = run(info, panel)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao estimar efeito: {str(e)}")
    return {
        "intervention_id": intervention_id,
        "name": info["name"],
        "date": str(info["date"])[:10],
        "metric": metric,
        "method": method,
        "true_effect": float(info["true_effect"]),
        **result,
        "pressupostos": quasi.PRESSUPOSTOS[method],
        "leitura_do_meio": quasi.LEITURA_DO_MEIO,
    }


QuasiMetric = Literal["clicks", "impressions"]


@app.get("/api/v1/quasi-experiments/interventions", tags=["Quase-experimentos"])
async def list_interventions():
    """Registro de mudanças do site e eventos externos, com o tamanho de cada grupo."""
    try:
        df = get_db().query_df("""
            SELECT i.*, COUNT(*) FILTER (WHERE m.grp = 'tratado') AS n_treated,
                   COUNT(*) FILTER (WHERE m.grp = 'controle') AS n_control
            FROM seo_interventions i LEFT JOIN seo_intervention_pages m USING (intervention_id)
            GROUP BY ALL ORDER BY i.date
        """)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar intervenções: {str(e)}")
    df["date"] = df["date"].astype(str).str[:10]
    return {"interventions": df.astype(object).where(df.notna(), None).to_dict("records"),
            "leitura_do_meio": quasi.LEITURA_DO_MEIO}


@app.get("/api/v1/quasi-experiments/its", tags=["Quase-experimentos"])
async def quasi_its(intervention_id: str = Query(...), metric: QuasiMetric = Query("clicks"),
                    end_date: Optional[date] = Query(None, description="Corta a janela (ex.: antes de um update do algoritmo)")):
    """Série temporal interrompida: as páginas tratadas contra a própria tendência anterior."""
    return _quasi("its", intervention_id, metric, lambda info, panel: quasi.interrupted_time_series(
        _daily_sum(panel, True), info["date"], end_date=end_date))


@app.get("/api/v1/quasi-experiments/control-counterfactual", tags=["Quase-experimentos"])
async def quasi_control_counterfactual(intervention_id: str = Query(...), metric: QuasiMetric = Query("clicks"),
                                       end_date: Optional[date] = Query(None)):
    """Contrafactual previsto pelas páginas de controle (a lógica do CausalImpact, com regressão simples)."""
    return _quasi("control_counterfactual", intervention_id, metric, lambda info, panel: quasi.control_counterfactual(
        _daily_sum(panel, True), _daily_sum(panel, False), info["date"], end_date=end_date))


@app.get("/api/v1/quasi-experiments/did", tags=["Quase-experimentos"])
async def quasi_did(intervention_id: str = Query(...), metric: QuasiMetric = Query("clicks"),
                    end_date: Optional[date] = Query(None)):
    """Diferença-em-diferenças: páginas alteradas contra páginas parecidas que não mudaram."""
    return _quasi("did", intervention_id, metric, lambda info, panel: quasi.diff_in_diff(
        panel, info["date"], end_date=end_date))


@app.get("/api/v1/quasi-experiments/ab-test", tags=["Quase-experimentos"])
async def quasi_ab_test(intervention_id: str = Query(...), metric: QuasiMetric = Query("clicks"),
                        end_date: Optional[date] = Query(None)):
    """Teste A/B de SEO por grupos de páginas sorteados, com p-valor por permutação."""
    def run(info, panel):
        if not info["randomized"]:
            raise HTTPException(status_code=400, detail="Esta intervenção não foi sorteada: use /did. Teste A/B exige sorteio.")
        return quasi.ab_test(panel, info["date"], end_date=end_date)
    return _quasi("ab", intervention_id, metric, run)


@app.get("/api/v1/quasi-experiments/ab-split", tags=["Quase-experimentos"])
async def quasi_ab_split(template: str = Query(..., description="produto, categoria ou post"),
                         seed: int = Query(0, ge=0), days: int = Query(28, ge=7, le=365)):
    """
    Planeja um teste A/B: sorteia as páginas de um template em dois grupos, estratificando
    pelos cliques dos últimos `days` dias para os grupos nascerem parecidos.
    """
    try:
        pages = get_db().conn.execute("""
            SELECT p.page AS unit, COALESCE(SUM(d.clicks), 0) AS pre_metric
            FROM seo_pages p LEFT JOIN seo_page_daily d ON d.page = p.page
                 AND d.date > (SELECT MAX(date) FROM seo_page_daily) - CAST(? AS INTEGER)
            WHERE p.template = ? GROUP BY p.page
        """, [days, template]).fetchdf()
        if pages.empty:
            raise HTTPException(status_code=404, detail=f"Nenhuma página com template '{template}'.")
        result = quasi.ab_split(pages, seed=seed)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao sortear grupos: {str(e)}")
    return {"template": template, **result, "pressupostos": quasi.PRESSUPOSTOS["ab"]}


async def collect_digital_methods() -> dict:
    """Resumo de métodos digitais para o relatório de IA (efeito do ranking + controvérsia na Wikipedia)."""
    return {
        "rank_effect": await search_rank_effect(),
        # chamada direta: os defaults Query() não se resolvem, passar tudo explícito
        "controversy": await wikipedia_controversy(lang="pt", seed=None, min_edits=20),
    }


# ===== RELATÓRIOS INTELIGENTES COM AGNO =====

@app.post("/api/v1/reports/generate", tags=["Reports"], response_model=dict)
async def generate_report(request: ReportRequest):
    """
    🤖 Gera relatório analítico narrativo usando IA (Agno + OpenAI).
    
    Este endpoint coleta dados de todas as análises disponíveis e usa um agente de IA
    para gerar um relatório compreensível com insights acionáveis e recomendações.
    
    **Parâmetros:**
    - **period_days**: Período de análise (padrão: 30 dias)
    - **focus_areas**: Áreas de foco opcionais (traffic, conversions, engagement, keywords)
    - **detail_level**: Nível de detalhe (executive, detailed, technical)
    - **language**: Idioma do relatório (padrão: pt-br)
    
    **Retorna:**
    - Executive summary narrativo
    - Seções detalhadas com insights por área
    - Recomendações priorizadas (high/medium/low)
    - Metadata com confidence score
    
    **Tempo de resposta esperado:** 7-15 segundos
    """
    try:
        logger.info(f"Iniciando geração de relatório: period_days={request.period_days}, detail_level={request.detail_level}")
        
        # ETAPA 1: Coleta paralela de dados de todos os endpoints
        logger.info("Coletando dados dos endpoints...")
        
        async def collect_all_data():
            """Coleta dados de todos os endpoints em paralelo."""
            tasks = {
                'kpis': get_kpis(),
                'channel_clusters': get_channel_clusters(n_clusters=3),
                'keyword_clusters': get_keyword_clusters(n_clusters=3),
                'digital_methods': collect_digital_methods(),
                'correlations': get_correlation_matrix()
            }
            
            results = {}
            for key, task in tasks.items():
                try:
                    result = await task
                    results[key] = result
                    
                    # Log detalhado para debug
                    if key.endswith('_clusters'):
                        total_key = f"total_{key.replace('_clusters', 's')}"
                        total = result.get(total_key, result.get('total_canais', result.get('total_keywords', result.get('total_paginas', 0))))
                        if total == 0:
                            logger.warning(f"⚠️ Endpoint {key} retornou 0 items - dados insuficientes para clustering")
                        else:
                            logger.info(f"✅ Endpoint {key} coletado com sucesso: {total} items em {result.get('n_clusters', 0)} clusters")
                    else:
                        logger.info(f"✅ Endpoint {key} coletado com sucesso")
                        
                except Exception as e:
                    logger.error(f"❌ Erro ao coletar {key}: {str(e)}")
                    results[key] = {}
            
            return results
        
        data_collection = await collect_all_data()
        
        # Adicionar informações de período
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=request.period_days)
        data_collection['period'] = {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'days': request.period_days
        }
        
        logger.info("Dados coletados com sucesso")
        
        # ETAPA 2: Preparar contexto estruturado para o agente
        context_prompt = f"""
Gere um relatório analítico completo baseado nos seguintes dados de marketing digital:

## 📅 Período de Análise
- **Início**: {data_collection['period']['start_date']}
- **Fim**: {data_collection['period']['end_date']}
- **Duração**: {data_collection['period']['days']} dias

## 📊 KPIs Gerais
{format_kpis(data_collection.get('kpis', {}))}

## 🚀 Clusters de Canais de Tráfego
{format_channel_clusters(data_collection.get('channel_clusters', {}))}

## 🔍 Clusters de Keywords (Google Search Console)
{format_keyword_clusters(data_collection.get('keyword_clusters', {}))}

## 🧭 Métodos Digitais (leitura do meio)
{format_digital_methods(data_collection.get('digital_methods', {}))}

## 🔗 Matriz de Correlação entre Métricas
{format_correlations(data_collection.get('correlations', {}))}

---

## 🎯 Instruções Específicas para este Relatório

- **Nível de Detalhe**: {request.detail_level}
- **Áreas de Foco**: {', '.join(request.focus_areas) if request.focus_areas else 'Análise completa de todas as áreas'}
- **Idioma**: {request.language}
- **Tom**: {'Executivo e estratégico' if request.detail_level == 'executive' else 'Detalhado e técnico' if request.detail_level == 'technical' else 'Balanceado'}

## 📋 Lembre-se de:
1. Dar nomes significativos aos clusters (não usar apenas números)
2. Incluir 2-4 key insights por seção
3. Gerar 5-8 recomendações priorizadas
4. Sempre citar dados específicos
5. Usar linguagem clara para stakeholders não-técnicos
"""
        
        logger.info("Contexto preparado, invocando agente Agno...")
        
        # ETAPA 3: Invocar agente Agno para geração do relatório
        try:
            # Criar agente (lazy initialization)
            logger.info("Criando agente Agno...")
            agent = create_report_agent(debug_mode=True)  # Debug ativado temporariamente
            logger.info("Agente criado com sucesso")
            
            # Executar geração do relatório
            logger.info("Executando agent.run()...")
            response = agent.run(context_prompt)
            logger.info(f"Response recebido: type={type(response)}")
            logger.info(f"Response.__class__.__name__: {response.__class__.__name__}")
            logger.info(f"hasattr(response, 'content'): {hasattr(response, 'content')}")
            if hasattr(response, 'content'):
                logger.info(f"type(response.content): {type(response.content)}")
                logger.info(f"response.content.__class__.__name__: {response.content.__class__.__name__}")
            
            # O Agno retorna o objeto diretamente quando usa output_schema
            if hasattr(response, 'content') and isinstance(response.content, AnalyticsReport):
                logger.info("✅ Response.content é AnalyticsReport (Pydantic model)")
                report_data = {
                    "executive_summary": response.content.executive_summary,
                    "sections": [s.dict() for s in response.content.sections],
                    "recommendations": [r.dict() for r in response.content.recommendations]
                }
                logger.info(f"Relatório parseado: {len(report_data['sections'])} seções, {len(report_data['recommendations'])} recomendações")
            elif hasattr(response, 'content') and isinstance(response.content, str):
                logger.info(f"Response tem content (string)")
                # Tentar parsear como JSON
                import json
                try:
                    report_data = json.loads(response.content)
                    logger.info("JSON parseado com sucesso")
                except Exception as json_error:
                    logger.warning(f"Resposta não é JSON válido: {str(json_error)}")
                    # Se não for JSON válido, criar estrutura básica
                    report_data = {
                        "executive_summary": str(response.content)[:500],
                        "sections": [],
                        "recommendations": []
                    }
            else:
                logger.error(f"Tipo não reconhecido! response type: {type(response)}")
                raise Exception(f"Resposta do agente em formato não esperado: {type(response)}")
            
            logger.info("Relatório gerado com sucesso pelo agente")
            
        except Exception as e:
            logger.error(f"Erro ao invocar agente Agno: {str(e)}", exc_info=True)
            # Fallback: gerar relatório simplificado
            logger.info("Usando fallback: relatório simplificado")
            report_data = generate_simple_fallback_report(data_collection)
        
        # ETAPA 4: Calcular confidence score
        confidence = calculate_confidence_score(data_collection)
        
        # ETAPA 5: Estruturar resposta final
        report = {
            "report_id": str(uuid.uuid4()),
            "generated_at": datetime.now().isoformat(),
            "period": data_collection['period'],
            "executive_summary": report_data.get("executive_summary", ""),
            "sections": report_data.get("sections", []),
            "recommendations": report_data.get("recommendations", []),
            "metadata": {
                "data_sources": list(data_collection.keys()),
                "ml_models_used": ["channel_profiling", "keyword_clustering"],
                "agent_model": "gpt-4o-mini",
                "confidence_score": confidence,
                "generation_timestamp": datetime.now().isoformat(),
                "request_parameters": {
                    "period_days": request.period_days,
                    "detail_level": request.detail_level,
                    "focus_areas": request.focus_areas,
                    "language": request.language
                }
            }
        }
        
        logger.info(f"Relatório completo gerado: report_id={report['report_id']}, confidence={confidence}")
        
        return report
        
    except Exception as e:
        logger.error(f"Erro ao gerar relatório: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao gerar relatório: {str(e)}"
        )


def generate_simple_fallback_report(data: dict) -> dict:
    """
    Gera relatório simplificado quando Agno falha.
    Não usa IA, apenas formata os dados coletados.
    """
    kpis = data.get('kpis', {})
    
    # Mapear campos para formato correto
    total_pages = kpis.get('totalPaginas', 0)
    total_sessions = kpis.get('sessoesTotais', 0)
    total_conversions = kpis.get('conversoesTotais', 0)
    bounce_rate = kpis.get('mediaBounceRate', 0) * 100
    
    conversion_rate = (total_conversions / total_sessions * 100) if total_sessions > 0 else 0
    
    return {
        "executive_summary": f"""
Relatório gerado em modo simplificado (sem IA).

Durante o período analisado, foram registradas {total_sessions:,} sessões 
com {total_conversions:,} conversões, resultando em uma taxa de conversão 
de {conversion_rate:.2f}%. A taxa de rejeição foi de {bounce_rate:.2f}%.

Dados completos disponíveis nos endpoints individuais de análise.
""".strip(),
        "sections": [
            {
                "title": "🧭 Métodos Digitais — leitura do meio",
                "content": format_digital_methods(data.get('digital_methods', {})),
                "key_insights": ["Cada métrica é produzida pela plataforma: leia as ressalvas antes de concluir"]
            },
            {
                "title": "📊 KPIs Principais",
                "content": format_kpis(kpis),
                "key_insights": ["Relatório em modo simplificado", "Configure OPENAI_API_KEY para relatórios completos"]
            }
        ],
        "recommendations": []
    }


# ===== ENDPOINT ADMINISTRATIVO - POPULAR DADOS =====

class PopulateDatabaseRequest(BaseModel):
    """Request para popular o banco de dados com dados simulados."""
    days: int = Field(default=30, ge=1, le=365, description="Número de dias de dados a gerar")
    overwrite: bool = Field(default=False, description="Se True, limpa dados existentes antes de popular")
    admin_key: Optional[str] = Field(default=None, description="Chave de administrador (configurar em .env)")


@app.post("/api/v1/admin/populate-database")
async def populate_database(request: PopulateDatabaseRequest):
    """
    🔒 ENDPOINT ADMINISTRATIVO - Popular banco de dados com dados simulados
    
    Este endpoint permite gerar dados sintéticos realistas para testes e desenvolvimento.
    
    **IMPORTANTE**: Em produção, configure ADMIN_KEY no .env para proteger este endpoint.
    
    Parâmetros:
    - days: Número de dias de dados históricos (1-365)
    - overwrite: Se True, limpa dados existentes
    - admin_key: Chave de segurança (obrigatória em produção)
    
    Exemplo:
    ```bash
    curl -X POST "http://localhost:8000/api/v1/admin/populate-database" \\
      -H "Content-Type: application/json" \\
      -d '{"days": 30, "overwrite": false, "admin_key": "sua_chave_secreta"}'
    ```
    """
    
    # 🔒 Verificação de segurança em produção
    admin_key_env = os.getenv("ADMIN_KEY", None)
    if admin_key_env:  # Se ADMIN_KEY está configurada no .env
        if not request.admin_key or request.admin_key != admin_key_env:
            raise HTTPException(
                status_code=403,
                detail="Acesso negado. ADMIN_KEY inválida ou ausente."
            )
    
    try:
        # Importa os simuladores (GA4 e GSC)
        from tests.simulador_dados import GA4Simulator, GSCSimulator
        from datetime import datetime, timedelta
        
        logger.info(f"🔄 Iniciando população do banco de dados: {request.days} dias")
        
        # Calcular período
        end_date = datetime.now()
        start_date = end_date - timedelta(days=request.days)
        
        # Instancia os simuladores
        ga4_sim = GA4Simulator()
        gsc_sim = GSCSimulator()
        
        # Se overwrite=True, limpa dados existentes
        db_instance = get_db()
        if request.overwrite:
            logger.warning("⚠️ Modo overwrite ativado - limpando dados existentes...")
            try:
                # Limpar tabelas
                db_instance.conn.execute("DELETE FROM traffic")
                db_instance.conn.execute("DELETE FROM engagement")
                db_instance.conn.execute("DELETE FROM conversions")
                db_instance.conn.execute("DELETE FROM gsc_query_performance")
                logger.info("✅ Dados antigos removidos com sucesso")
            except Exception as e:
                logger.error(f"❌ Erro ao limpar dados: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Erro ao limpar dados existentes: {str(e)}"
                )
        
        # Gera dados simulados
        logger.info("📊 Gerando dados simulados...")
        
        # GA4 Traffic
        ga4_traffic = ga4_sim.generate_traffic_data(start_date, request.days)
        logger.info(f"   → {len(ga4_traffic)} registros de tráfego")
        
        # GA4 Engagement  
        ga4_engagement = ga4_sim.generate_engagement_data(start_date, request.days)
        logger.info(f"   → {len(ga4_engagement)} registros de engagement")
        
        # GA4 Conversions
        ga4_conversions = ga4_sim.generate_conversions_data(start_date, request.days)
        logger.info(f"   → {len(ga4_conversions)} registros de conversões")
        
        # GSC Performance
        gsc_data = gsc_sim.generate_query_performance(start_date, end_date)
        logger.info(f"   → {len(gsc_data)} registros GSC")
        
        # Salva no banco
        logger.info("💾 Salvando no banco de dados...")
        
        # Traffic (inserir em lote é mais rápido)
        db_instance.insert_traffic_data(ga4_traffic)
        logger.info(f"   ✅ {len(ga4_traffic)} registros de tráfego salvos")
        
        # Engagement
        db_instance.insert_engagement_data(ga4_engagement)
        logger.info(f"   ✅ {len(ga4_engagement)} registros de engagement salvos")
        
        # Conversions
        db_instance.insert_conversions_data(ga4_conversions)
        logger.info(f"   ✅ {len(ga4_conversions)} registros de conversões salvos")
        
        # GSC
        db_instance.insert_gsc_query_data(gsc_data)
        logger.info(f"   ✅ {len(gsc_data)} registros GSC salvos")
        
        logger.info("✅ População do banco concluída com sucesso!")
        
        # Retorna estatísticas
        return {
            "status": "success",
            "message": f"Banco de dados populado com {request.days} dias de dados",
            "statistics": {
                "days_generated": request.days,
                "traffic_records": len(ga4_traffic),
                "engagement_records": len(ga4_engagement),
                "conversion_records": len(ga4_conversions),
                "gsc_records": len(gsc_data),
                "overwrite_mode": request.overwrite
            },
            "next_steps": [
                "Use GET /api/v1/kpis para visualizar KPIs",
                "Use POST /api/v1/reports/generate para gerar relatórios",
                "Use GET /api/v1/channel-clusters para análise de canais"
            ]
        }
        
    except ImportError as e:
        logger.error(f"❌ Erro ao importar simulador: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Módulo simulador não encontrado. Certifique-se de que tests/simulador_dados.py existe."
        )
    except Exception as e:
        logger.error(f"❌ Erro ao popular banco: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao popular banco de dados: {str(e)}"
        )


@app.get("/api/v1/admin/database-stats")
async def get_database_stats():
    """
    📊 Estatísticas do banco de dados
    
    Retorna informações sobre os dados armazenados no DuckDB.
    """
    try:
        db_instance = get_db()
        
        # Consulta contagens (nomes corretos das tabelas)
        traffic_count = db_instance.conn.execute(
            "SELECT COUNT(*) FROM traffic"
        ).fetchone()[0]
        
        engagement_count = db_instance.conn.execute(
            "SELECT COUNT(*) FROM engagement"
        ).fetchone()[0]
        
        conversions_count = db_instance.conn.execute(
            "SELECT COUNT(*) FROM conversions"
        ).fetchone()[0]
        
        gsc_count = db_instance.conn.execute(
            "SELECT COUNT(*) FROM gsc_query_performance"
        ).fetchone()[0]
        
        # Período de dados
        date_range = db_instance.conn.execute("""
            SELECT 
                MIN(date) as min_date,
                MAX(date) as max_date
            FROM traffic
        """).fetchone()
        
        return {
            "database_file": "data/processed/ga4_data.duckdb",
            "record_counts": {
                "traffic": traffic_count,
                "engagement": engagement_count,
                "conversions": conversions_count,
                "gsc_query_performance": gsc_count,
                "total": traffic_count + engagement_count + conversions_count + gsc_count
            },
            "date_range": {
                "start": str(date_range[0]) if date_range[0] else None,
                "end": str(date_range[1]) if date_range[1] else None
            },
            "status": "operational"
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter estatísticas: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao consultar banco de dados: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    import os
    
    # Usar 0.0.0.0 para aceitar conexões externas (Render, produção)
    # Usar porta do ambiente ou 8000 como padrão
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",  # ✅ Aceita conexões de qualquer IP (necessário para Render)
        port=int(os.getenv("PORT", 8000)),  # ✅ Render define PORT automaticamente
        reload=True,
        log_level="info"
    )
