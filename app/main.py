from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import sys
from pathlib import Path
import numpy as np

# Adiciona src ao path
sys.path.append(str(Path(__file__).parent.parent))

# ✅ BANCO DE DADOS DIRETO - Não depende de GA4/GSC APIs
# db_storage acessa DuckDB diretamente, pronto para receber dados simulados
from src.collectors.db_storage import GA4DatabaseStorage

app = FastAPI(
    title="Dashboard Analytics API",
    description="API para análise de dados GA4 e GSC com ML predictions",
    version="1.0.0"
)

# CORS para frontend React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Instância global do banco - PRONTA PARA DADOS SIMULADOS
# Quando implementar o simulador, ele deve popular este mesmo banco
db = None

def get_db():
    """Lazy initialization do banco de dados."""
    global db
    if db is None:
        db = GA4DatabaseStorage()
    return db


# ===== MODELS =====

class PageSimulatorInput(BaseModel):
    """Input para simulação de performance de página."""
    contagemDePalavras: int = Field(..., ge=0, description="Contagem de palavras do conteúdo")
    numeroDeImagens: int = Field(..., ge=0, description="Número de imagens na página")
    precoDoProduto: float = Field(..., ge=0, description="Preço do produto (0 se não é produto)")


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
    - Features: sessions, page_views, bounce_rate, session_duration
    - Métricas de interesse: conversions, engagement_rate
    """
    try:
        # Query agregada para análise de correlação
        df = get_db().query_df("""
            SELECT 
                e.page_path,
                SUM(t.sessions) as sessions,
                SUM(t.screen_page_views) as page_views,
                AVG(t.average_session_duration) as avg_session_duration,
                AVG(e.engagement_rate) as engagement_rate,
                SUM(c.key_events) as conversions,
                AVG(e.engaged_sessions::FLOAT / NULLIF(e.engaged_sessions + (1 - e.engagement_rate) * e.engaged_sessions, 0)) as bounce_rate_inv
            FROM engagement e
            LEFT JOIN traffic t ON e.date = t.date
            LEFT JOIN conversions c ON e.date = c.date
            WHERE e.page_path IS NOT NULL
            GROUP BY e.page_path
            HAVING SUM(t.sessions) > 10
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


@app.get("/api/v1/analysis/page_clusters", tags=["Análises"])
async def get_page_clusters():
    """
    Retorna clusters de páginas (arquétipos) baseados em performance.
    
    Agrupa páginas por similaridade em:
    - Engajamento (alto/médio/baixo)
    - Conversão (boa/média/fraca)
    - Tráfego (alto/médio/baixo)
    """
    try:
        # Query para segmentar páginas em clusters baseados em métricas
        df = get_db().query_df("""
            SELECT 
                e.page_path,
                SUM(t.sessions) as sessions,
                AVG(t.average_session_duration) as avg_duration,
                AVG(e.engagement_rate) as engagement_rate,
                SUM(c.key_events) as conversions,
                CASE 
                    WHEN AVG(e.engagement_rate) > 0.6 AND SUM(c.key_events) > 50 THEN 0
                    WHEN SUM(c.key_events) > 50 THEN 1
                    WHEN AVG(e.engagement_rate) < 0.3 THEN 2
                    ELSE 3
                END as cluster_id
            FROM engagement e
            LEFT JOIN traffic t ON e.date = t.date AND e.page_path LIKE '%' || t.session_source || '%'
            LEFT JOIN conversions c ON e.date = c.date
            WHERE e.page_path IS NOT NULL
            GROUP BY e.page_path
            HAVING SUM(t.sessions) > 5
        """)
        
        if df.empty:
            return {"clusters": []}
        
        # Agrupa por cluster_id
        clusters = []
        cluster_names = {
            0: "Páginas de Alto Engajamento e Conversão",
            1: "Produtos de Sucesso (Boa Conversão)",
            2: "Páginas Problemáticas (Baixo Engajamento)",
            3: "Páginas Intermediárias"
        }
        
        import numpy as np
        
        def safe_mean(series):
            """Calcula média e substitui NaN por 0."""
            val = float(series.mean())
            return 0.0 if (np.isnan(val) or np.isinf(val)) else val
        
        for cluster_id in df['cluster_id'].unique():
            cluster_data = df[df['cluster_id'] == cluster_id]
            clusters.append({
                "clusterId": int(cluster_id),
                "clusterName": cluster_names.get(cluster_id, f"Cluster {cluster_id}"),
                "avgEngagementRate": round(safe_mean(cluster_data['engagement_rate']), 2),
                "avgSessionDuration": round(safe_mean(cluster_data['avg_duration']), 2),
                "avgConversions": int(safe_mean(cluster_data['conversions'])),
                "totalPaginas": int(len(cluster_data))
            })
        
        return {"clusters": sorted(clusters, key=lambda x: x['clusterId'])}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular clusters: {str(e)}")


# ===== ANÁLISE DE PÁGINA ESPECÍFICA =====

@app.get("/api/v1/page_analysis", tags=["Análises Preditivas"])
async def get_page_analysis(path: str = Query(..., description="Caminho da página (ex: /produtos/item-1)")):
    """
    Retorna análise completa de uma página específica.
    
    - **path**: Caminho da página (ex: /produtos/item-1)
    
    Retorna dados reais + previsões ML.
    """
    try:
        # Busca dados da página
        page_data = get_db().query_df(f"""
            SELECT 
                e.page_path,
                SUM(t.sessions) as sessions,
                AVG(t.average_session_duration) as avg_session_duration,
                AVG(e.engagement_rate) as engagement_rate,
                SUM(t.screen_page_views) as page_views,
                SUM(c.key_events) as conversions
            FROM engagement e
            LEFT JOIN traffic t ON e.date = t.date
            LEFT JOIN conversions c ON e.date = c.date
            WHERE e.page_path = '{path}'
            GROUP BY e.page_path
        """)
        
        if page_data.empty:
            raise HTTPException(status_code=404, detail=f"Página '{path}' não encontrada")
        
        row = page_data.iloc[0]
        
        # Classifica risco de rejeição baseado em engagement
        engagement = float(row['engagement_rate']) if row['engagement_rate'] else 0
        risco = "Baixo" if engagement > 0.6 else "Médio" if engagement > 0.4 else "Alto"
        
        # Classifica tipo de página
        conversions = int(row['conversions']) if row['conversions'] else 0
        if conversions > 50:
            cluster_name = "Produto de Sucesso"
        elif engagement > 0.6:
            cluster_name = "Conteúdo de Alto Engajamento"
        else:
            cluster_name = "Página com Potencial de Melhoria"
        
        return {
            "pagePath": path,
            "dadosReais": {
                "sessions": int(row['sessions']) if row['sessions'] else 0,
                "pageViews": int(row['page_views']) if row['page_views'] else 0,
                "averageSessionDuration": round(float(row['avg_session_duration']), 2) if row['avg_session_duration'] else 0,
                "engagementRate": round(engagement, 2),
                "conversions": conversions
            },
            "analisePreditiva": {
                "clusterName": cluster_name,
                "riscoDeRejeicao": risco
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao analisar página: {str(e)}")


# ===== SIMULADOR PREDITIVO =====

@app.post("/api/v1/predict/simulator", tags=["Análises Preditivas"])
async def predict_simulator(input_data: PageSimulatorInput):
    """
    Simula performance esperada de uma nova página baseado em features.
    
    Recebe características de conteúdo e retorna estimativas de:
    - Taxa de conversão
    - Taxa de rejeição
    - Duração média de sessão
    - Recomendações de otimização
    """
    try:
        # Busca dados históricos similares para baseline
        similar_pages = get_db().query_df("""
            SELECT 
                AVG(e.engagement_rate) as avg_engagement,
                AVG(t.average_session_duration) as avg_duration,
                AVG(c.key_events::FLOAT / NULLIF(t.sessions, 0)) as conversion_rate
            FROM engagement e
            LEFT JOIN traffic t ON e.date = t.date
            LEFT JOIN conversions c ON e.date = c.date
            WHERE t.sessions > 10
        """)
        
        # Modelo simplificado baseado em heurísticas
        palavras = input_data.contagemDePalavras
        imagens = input_data.numeroDeImagens
        preco = input_data.precoDoProduto
        
        # Baseline do banco
        baseline_engagement = float(similar_pages['avg_engagement'].iloc[0]) if not similar_pages.empty else 0.5
        baseline_duration = float(similar_pages['avg_duration'].iloc[0]) if not similar_pages.empty else 180
        baseline_conversion = float(similar_pages['conversion_rate'].iloc[0]) if not similar_pages.empty else 0.02
        
        # Ajustes baseados em features
        # Contagem de palavras: mais palavras = maior duração, melhor engagement
        word_factor = min(palavras / 1000, 1.5)  # Cap em 1.5x
        
        # Imagens: mais imagens = melhor engagement, mas pode aumentar bounce se muitas
        image_factor = 1 + (min(imagens, 5) * 0.05)  # +5% por imagem, max 5
        
        # Preço: produtos caros tendem a ter menor conversão
        price_factor = 1.0 if preco == 0 else max(0.5, 1 - (preco / 1000) * 0.1)
        
        # Predições
        estimated_engagement = min(baseline_engagement * word_factor * image_factor, 1.0)
        estimated_bounce = max(0.1, 1 - estimated_engagement)
        estimated_duration = baseline_duration * word_factor
        estimated_conversion_per_1k = (baseline_conversion * 1000) * price_factor * image_factor
        
        # Recomendações
        recommendations = []
        if palavras < 300:
            recommendations.append("⚠️ Contagem de palavras baixa. Considere expandir o conteúdo para melhorar engajamento.")
        elif palavras > 2000:
            recommendations.append("✅ Excelente contagem de palavras para engajamento.")
        else:
            recommendations.append("✅ Boa contagem de palavras.")
        
        if imagens < 2:
            recommendations.append("⚠️ Poucas imagens. Adicionar mais imagens pode melhorar a taxa de engajamento.")
        elif imagens > 10:
            recommendations.append("⚠️ Muitas imagens podem aumentar o tempo de carregamento. Otimize.")
        else:
            recommendations.append("✅ Número adequado de imagens.")
        
        if preco > 500:
            recommendations.append("💰 Produto de alto valor. Considere adicionar mais informações e provas sociais para aumentar conversão.")
        elif preco > 0:
            recommendations.append("💰 Produto de valor médio. Destaque benefícios e diferenciais.")
        
        if estimated_bounce > 0.7:
            recommendations.append("🚨 Taxa de rejeição estimada alta. Considere melhorar o conteúdo ou adicionar CTAs mais claros.")
        
        return {
            "inputFeatures": {
                "contagemDePalavras": palavras,
                "numeroDeImagens": imagens,
                "precoDoProduto": preco
            },
            "predictedPerformance": {
                "estimativaEngagementRate": round(estimated_engagement, 2),
                "estimativaBounceRate": round(estimated_bounce, 2),
                "estimativaSessionDuration": round(estimated_duration, 1),
                "estimativaConversoesPorMilSessoes": round(estimated_conversion_per_1k, 1)
            },
            "recommendations": recommendations
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao simular performance: {str(e)}")


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


@app.on_event("shutdown")
async def shutdown_event():
    """Fecha conexão com banco ao desligar."""
    db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="localhost",
        port=8000,
        reload=True,
        log_level="info"
    )
