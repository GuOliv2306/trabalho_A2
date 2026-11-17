"""
Simulador de Dados GA4 e Google Search Console

Este módulo gera dados sintéticos realistas que emulam os retornos das APIs
do Google Analytics 4 e Google Search Console, permitindo desenvolvimento
e testes sem depender de dados reais.

Características:
- Distribuições estatísticas realistas (Poisson, Normal, Beta)
- Correlações entre métricas (ex: posição → CTR, sessões → conversões)
- Séries temporais com tendências e sazonalidade
- Long-tail distribution para keywords
- Proporções realistas de tráfego por fonte/dispositivo/país

Uso:
    python tests/simulador_dados.py --days 30 --verbose
"""

import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Tuple
import argparse

import numpy as np

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.collectors.db_storage import GA4DatabaseStorage


class DataSimulatorConfig:
    """Configurações globais do simulador"""
    
    # Propriedades
    PROPERTY_ID = "simulado_12345"
    SITE_URL = "https://example.com/"
    
    # Fontes de tráfego GA4 (realista)
    TRAFFIC_SOURCES = [
        ("google", "organic", "(not set)", 0.35),  # 35% orgânico Google
        ("(direct)", "(none)", "(not set)", 0.20),  # 20% direto
        ("google", "cpc", "brand_campaign", 0.15),  # 15% Google Ads
        ("facebook", "social", "social_campaign", 0.10),  # 10% Facebook
        ("instagram", "social", "influencer", 0.08),  # 8% Instagram
        ("bing", "organic", "(not set)", 0.05),  # 5% Bing orgânico
        ("referral", "referral", "(not set)", 0.04),  # 4% referral
        ("email", "email", "newsletter", 0.03),  # 3% email
    ]
    
    # Páginas do site (Landing Pages)
    LANDING_PAGES = [
        ("/", "Home", 0.25),
        ("/produtos", "Produtos", 0.20),
        ("/blog/artigo-1", "Artigo SEO Principal", 0.15),
        ("/sobre", "Sobre Nós", 0.10),
        ("/contato", "Contato", 0.08),
        ("/produtos/item-1", "Produto Destaque", 0.07),
        ("/blog/artigo-2", "Artigo Popular", 0.06),
        ("/produtos/categoria-a", "Categoria A", 0.05),
        ("/servicos", "Serviços", 0.04),
    ]
    
    # Eventos de conversão GA4
    CONVERSION_EVENTS = [
        ("purchase", 0.03),  # 3% de conversão
        ("generate_lead", 0.05),  # 5% gera lead
        ("sign_up", 0.08),  # 8% se cadastra
        ("add_to_cart", 0.15),  # 15% adiciona ao carrinho
        ("view_item", 0.40),  # 40% visualiza produto
    ]
    
    # Dispositivos (proporção realista mobile-first)
    DEVICES = [
        ("mobile", 0.60),  # 60% mobile
        ("desktop", 0.35),  # 35% desktop
        ("tablet", 0.05),  # 5% tablet
    ]
    
    # Países (distribuição realista para site brasileiro)
    COUNTRIES = [
        ("Brazil", "bra", 0.70),  # 70% Brasil
        ("United States", "usa", 0.10),  # 10% EUA
        ("Portugal", "prt", 0.05),  # 5% Portugal
        ("Argentina", "arg", 0.04),  # 4% Argentina
        ("Mexico", "mex", 0.03),  # 3% México
        ("Spain", "esp", 0.03),  # 3% Espanha
        ("(not set)", "zz", 0.05),  # 5% não identificado
    ]
    
    # Queries do Search Console (long-tail distribution)
    SEARCH_QUERIES = [
        # Head terms (alto volume, baixa conversão)
        ("produtos", 0.15, 5000, 1.5),
        ("loja online", 0.10, 3000, 2.0),
        ("comprar", 0.08, 2500, 2.5),
        
        # Mid-tail (volume médio, conversão média)
        ("melhores produtos 2025", 0.06, 1500, 3.0),
        ("produto qualidade preço", 0.05, 1200, 4.0),
        ("como escolher produto", 0.04, 1000, 5.0),
        ("produto barato online", 0.04, 900, 5.5),
        
        # Long-tail (baixo volume, alta conversão)
        ("comprar produto específico marca x", 0.03, 500, 1.2),
        ("produto categoria a modelo 2025", 0.03, 450, 1.8),
        ("melhor loja produto categoria b", 0.02, 300, 2.5),
        ("produto qualidade premium", 0.02, 250, 3.0),
        
        # Ultra long-tail (volume muito baixo, conversão alta)
        ("onde comprar produto x com desconto", 0.02, 150, 1.5),
        ("produto y vale a pena comprar", 0.02, 120, 2.0),
        ("comparação produto a vs produto b", 0.01, 80, 3.5),
        ("avaliação produto categoria premium", 0.01, 60, 4.0),
    ]


class GA4Simulator:
    """Simula dados do Google Analytics 4"""
    
    def __init__(self, property_id: str = DataSimulatorConfig.PROPERTY_ID):
        self.property_id = property_id
        self.config = DataSimulatorConfig
        
    def generate_traffic_data(
        self, 
        start_date: datetime, 
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Gera dados de tráfego (sessões, usuários, pageviews)
        
        Simula o retorno de: properties.runReport com dimensões
        [sessionSource, sessionMedium, sessionCampaignName]
        """
        traffic_data = []
        
        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)
            date_str = current_date.strftime("%Y-%m-%d")
            
            # Fator de sazonalidade (fins de semana têm menos tráfego B2B)
            weekday_factor = 0.7 if current_date.weekday() in [5, 6] else 1.0
            
            # Tendência crescente ao longo do tempo (crescimento orgânico)
            trend_factor = 1.0 + (day_offset * 0.01)  # 1% de crescimento por dia
            
            for source, medium, campaign, proportion in self.config.TRAFFIC_SOURCES:
                # Volume base de sessões por fonte (distribuição realista)
                base_sessions = int(random.gauss(1000, 200) * proportion * weekday_factor * trend_factor)
                base_sessions = max(10, base_sessions)  # mínimo 10 sessões
                
                # Usuários ativos (90-95% das sessões são únicos)
                active_users = int(base_sessions * random.uniform(0.90, 0.95))
                
                # Novos usuários (20-40% do total, varia por fonte)
                new_user_rate = 0.35 if medium == "organic" else 0.25
                new_users = int(active_users * random.uniform(new_user_rate - 0.05, new_user_rate + 0.05))
                
                # Pageviews (usuários veem 2-5 páginas em média)
                avg_pages_per_session = random.uniform(2.0, 5.0)
                page_views = int(base_sessions * avg_pages_per_session)
                
                # Duração média da sessão (segundos)
                # Orgânico geralmente tem maior engajamento
                if medium == "organic":
                    avg_duration = random.gauss(180, 60)  # ~3 min
                elif medium == "cpc":
                    avg_duration = random.gauss(120, 40)  # ~2 min
                elif medium == "social":
                    avg_duration = random.gauss(90, 30)  # ~1.5 min
                else:
                    avg_duration = random.gauss(60, 20)  # ~1 min
                
                avg_duration = max(10, avg_duration)  # mínimo 10 segundos
                
                traffic_data.append({
                    "property_id": self.property_id,
                    "date": date_str,
                    "session_source": source,
                    "session_medium": medium,
                    "session_campaign_name": campaign,
                    "sessions": base_sessions,
                    "active_users": active_users,
                    "new_users": new_users,
                    "screen_page_views": page_views,
                    "average_session_duration": round(avg_duration, 2),
                })
        
        return traffic_data
    
    def generate_conversions_data(
        self, 
        start_date: datetime, 
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Gera dados de conversões (eventos, receita, transações)
        
        Simula o retorno de: properties.runReport com dimensões
        [eventName, sessionSource, sessionMedium]
        """
        conversions_data = []
        
        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)
            date_str = current_date.strftime("%Y-%m-%d")
            
            # Base de tráfego do dia (para calcular conversões)
            daily_traffic = int(random.gauss(5000, 1000))
            
            for event_name, conversion_rate in self.config.CONVERSION_EVENTS:
                # Conversões por fonte de tráfego
                for source, medium, campaign, traffic_prop in self.config.TRAFFIC_SOURCES[:5]:  # Top 5 fontes
                    
                    # Tráfego desta fonte
                    source_traffic = int(daily_traffic * traffic_prop)
                    
                    # Eventos chave (conversões) - aplica taxa de conversão
                    key_events = int(source_traffic * conversion_rate * random.uniform(0.8, 1.2))
                    
                    # Contagem total do evento (pode ser maior que key_events)
                    event_count = int(key_events * random.uniform(1.0, 1.5))
                    
                    # Receita (apenas para eventos de compra)
                    if event_name == "purchase":
                        avg_order_value = random.gauss(150, 50)  # R$ 150 ± 50
                        total_revenue = round(key_events * avg_order_value, 2)
                        transactions = key_events
                        purchase_revenue = total_revenue
                    elif event_name == "add_to_cart":
                        # Alguma receita potencial
                        total_revenue = round(key_events * random.gauss(100, 30), 2)
                        transactions = 0
                        purchase_revenue = 0.0
                    else:
                        total_revenue = 0.0
                        transactions = 0
                        purchase_revenue = 0.0
                    
                    conversions_data.append({
                        "property_id": self.property_id,
                        "date": date_str,
                        "event_name": event_name,
                        "session_source": source,
                        "session_medium": medium,
                        "key_events": key_events,
                        "event_count": event_count,
                        "total_revenue": total_revenue,
                        "transactions": transactions,
                        "purchase_revenue": purchase_revenue,
                    })
        
        return conversions_data
    
    def generate_engagement_data(
        self, 
        start_date: datetime, 
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Gera dados de engajamento (por página, device, duração)
        
        Simula o retorno de: properties.runReport com dimensões
        [pagePath, unifiedScreenName, deviceCategory]
        """
        engagement_data = []
        
        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)
            date_str = current_date.strftime("%Y-%m-%d")
            
            for page_path, screen_name, page_proportion in self.config.LANDING_PAGES:
                for device, device_proportion in self.config.DEVICES:
                    
                    # Base de sessões para esta página/device
                    base_sessions = int(
                        random.gauss(500, 100) * page_proportion * device_proportion
                    )
                    base_sessions = max(5, base_sessions)
                    
                    # Engagement rate (páginas de produto geralmente têm maior engajamento)
                    if "produto" in page_path.lower():
                        engagement_rate = random.uniform(0.65, 0.85)
                    elif page_path == "/":
                        engagement_rate = random.uniform(0.50, 0.70)
                    else:
                        engagement_rate = random.uniform(0.40, 0.60)
                    
                    engaged_sessions = int(base_sessions * engagement_rate)
                    
                    # Duração média da sessão (mobile geralmente menor)
                    if device == "mobile":
                        avg_duration = random.gauss(120, 40)
                    elif device == "desktop":
                        avg_duration = random.gauss(180, 60)
                    else:  # tablet
                        avg_duration = random.gauss(150, 50)
                    
                    avg_duration = max(10, avg_duration)
                    
                    # Event count (interações na página)
                    event_count = int(base_sessions * random.uniform(3, 8))
                    
                    # User engagement duration (total de tempo engajado)
                    user_engagement_duration = int(engaged_sessions * avg_duration)
                    
                    engagement_data.append({
                        "property_id": self.property_id,
                        "date": date_str,
                        "page_path": page_path,
                        "unified_screen_name": screen_name,
                        "device_category": device,
                        "engagement_rate": round(engagement_rate, 4),
                        "engaged_sessions": engaged_sessions,
                        "average_session_duration": round(avg_duration, 2),
                        "event_count": event_count,
                        "user_engagement_duration": user_engagement_duration,
                    })
        
        return engagement_data


class GSCSimulator:
    """Simula dados do Google Search Console"""
    
    def __init__(self, site_url: str = DataSimulatorConfig.SITE_URL):
        self.site_url = site_url
        self.config = DataSimulatorConfig
    
    def _calculate_ctr_from_position(self, position: float) -> float:
        """
        Calcula CTR esperado baseado na posição média
        Baseado em estudos reais de CTR por posição no Google
        """
        # CTR médio por posição (aproximação realista)
        ctr_map = {
            1: 0.28,   # Posição 1: 28%
            2: 0.15,   # Posição 2: 15%
            3: 0.11,   # Posição 3: 11%
            4: 0.08,   # Posição 4-5: 8%
            5: 0.08,
            6: 0.05,   # Posição 6-10: 5-3%
            7: 0.04,
            8: 0.03,
            9: 0.03,
            10: 0.02,
        }
        
        # Interpola para posições intermediárias
        pos_floor = int(position)
        pos_ceil = pos_floor + 1
        
        ctr_floor = ctr_map.get(pos_floor, 0.01)
        ctr_ceil = ctr_map.get(pos_ceil, 0.01)
        
        # Interpolação linear
        fraction = position - pos_floor
        ctr = ctr_floor + (ctr_ceil - ctr_floor) * fraction
        
        # Adiciona variação natural (±20%)
        ctr *= random.uniform(0.8, 1.2)
        
        return min(1.0, max(0.001, ctr))  # Entre 0.1% e 100%
    
    def generate_query_performance(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Dict[str, Any]]:
        """
        Gera dados de performance por query (palavra-chave)
        
        Simula o retorno de: searchanalytics.query com dimensão [query]
        """
        query_data = []
        date_range_str = f"{start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}"
        
        for query, proportion, base_impressions, avg_position in self.config.SEARCH_QUERIES:
            # Impressões (com variação de ±30%)
            impressions = int(base_impressions * random.uniform(0.7, 1.3))
            
            # Posição média (com pequena variação)
            position = avg_position + random.uniform(-0.5, 0.5)
            position = max(1.0, min(20.0, position))  # Entre 1 e 20
            
            # CTR baseado na posição
            ctr = self._calculate_ctr_from_position(position)
            
            # Cliques baseados em CTR e impressões
            clicks = int(impressions * ctr)
            clicks = max(1, clicks)  # Mínimo 1 clique
            
            # Recalcula CTR exato
            ctr = clicks / impressions if impressions > 0 else 0.0
            
            query_data.append({
                "site_url": self.site_url,
                "query": query,
                "clicks": clicks,
                "impressions": impressions,
                "ctr": round(ctr, 4),
                "position": round(position, 2),
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
            })
        
        return query_data
    
    def generate_page_performance(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Dict[str, Any]]:
        """
        Gera dados de performance por página (URL)
        
        Simula o retorno de: searchanalytics.query com dimensão [page]
        """
        page_data = []
        
        for page_path, page_name, proportion in self.config.LANDING_PAGES:
            full_url = f"{self.site_url.rstrip('/')}{page_path}"
            
            # Impressões base (proporcional à popularidade da página)
            base_impressions = int(random.gauss(10000, 2000) * proportion)
            
            # Posição média (páginas principais têm melhor posição)
            if page_path == "/" or "produto" in page_path:
                avg_position = random.uniform(2.0, 5.0)
            else:
                avg_position = random.uniform(4.0, 8.0)
            
            # CTR baseado na posição
            ctr = self._calculate_ctr_from_position(avg_position)
            
            # Cliques
            clicks = int(base_impressions * ctr)
            
            # Recalcula CTR exato
            ctr = clicks / base_impressions if base_impressions > 0 else 0.0
            
            page_data.append({
                "site_url": self.site_url,
                "page": full_url,
                "clicks": clicks,
                "impressions": base_impressions,
                "ctr": round(ctr, 4),
                "position": round(avg_position, 2),
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
            })
        
        return page_data
    
    def generate_country_performance(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Dict[str, Any]]:
        """
        Gera dados de performance por país
        
        Simula o retorno de: searchanalytics.query com dimensão [country]
        """
        country_data = []
        
        for country_name, country_code, proportion in self.config.COUNTRIES:
            # Impressões proporcionais ao tráfego do país
            impressions = int(random.gauss(50000, 10000) * proportion)
            
            # Posição varia por país (países de língua nativa têm melhor posição)
            if country_code in ["bra", "prt"]:
                avg_position = random.uniform(2.5, 4.5)
            else:
                avg_position = random.uniform(5.0, 8.0)
            
            # CTR baseado na posição
            ctr = self._calculate_ctr_from_position(avg_position)
            
            # Cliques
            clicks = int(impressions * ctr)
            
            # Recalcula CTR exato
            ctr = clicks / impressions if impressions > 0 else 0.0
            
            country_data.append({
                "site_url": self.site_url,
                "country": country_code,
                "clicks": clicks,
                "impressions": impressions,
                "ctr": round(ctr, 4),
                "position": round(avg_position, 2),
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
            })
        
        return country_data
    
    def generate_device_performance(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Dict[str, Any]]:
        """
        Gera dados de performance por dispositivo
        
        Simula o retorno de: searchanalytics.query com dimensão [device]
        """
        device_data = []
        
        for device, proportion in self.config.DEVICES:
            # Impressões proporcionais ao uso do dispositivo
            impressions = int(random.gauss(60000, 12000) * proportion)
            
            # Posição similar entre dispositivos (mobile-first indexing)
            avg_position = random.uniform(3.0, 5.5)
            
            # CTR baseado na posição
            ctr = self._calculate_ctr_from_position(avg_position)
            
            # Mobile tende a ter CTR ligeiramente menor
            if device == "mobile":
                ctr *= 0.95
            
            # Cliques
            clicks = int(impressions * ctr)
            
            # Recalcula CTR exato
            ctr = clicks / impressions if impressions > 0 else 0.0
            
            device_data.append({
                "site_url": self.site_url,
                "device": device.upper(),  # GSC retorna em maiúsculas
                "clicks": clicks,
                "impressions": impressions,
                "ctr": round(ctr, 4),
                "position": round(avg_position, 2),
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
            })
        
        return device_data
    
    def generate_date_performance(
        self,
        start_date: datetime,
        days: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        Gera dados de performance diária (série temporal)
        
        Simula o retorno de: searchanalytics.query com dimensão [date]
        """
        date_data = []
        
        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)
            date_str = current_date.strftime("%Y-%m-%d")
            
            # Sazonalidade semanal
            weekday_factor = 0.75 if current_date.weekday() in [5, 6] else 1.0
            
            # Tendência crescente
            trend_factor = 1.0 + (day_offset * 0.005)  # 0.5% crescimento/dia
            
            # Volume base do dia
            base_impressions = int(random.gauss(8000, 1500) * weekday_factor * trend_factor)
            
            # Posição média (melhora ligeiramente ao longo do tempo)
            avg_position = random.uniform(3.5, 5.0) - (day_offset * 0.01)
            avg_position = max(1.5, avg_position)
            
            # CTR baseado na posição
            ctr = self._calculate_ctr_from_position(avg_position)
            
            # Cliques
            clicks = int(base_impressions * ctr)
            
            # Recalcula CTR exato
            ctr = clicks / base_impressions if base_impressions > 0 else 0.0
            
            date_data.append({
                "site_url": self.site_url,
                "date": date_str,
                "clicks": clicks,
                "impressions": base_impressions,
                "ctr": round(ctr, 4),
                "position": round(avg_position, 2),
            })
        
        return date_data


class ExperimentSimulator:
    """
    Simula o que os quase-experimentos e a análise de conteúdo precisam e o resto do
    simulador não tem: um painel página×dia com intervenções de efeito conhecido, e
    consultas/páginas com texto e com o código verdadeiro de cada variável.

    Determinístico para um mesmo `seed`.
    """

    TEMPLATES = {"produto": 40, "categoria": 24, "post": 30}
    INSTITUCIONAIS = [("/", "Home"), ("/sobre", "Sobre nós"), ("/contato", "Contato"),
                      ("/servicos", "Serviços"), ("/politica-de-privacidade", "Política de privacidade")]
    PRODUTOS = ["tênis de corrida", "mochila de trilha", "garrafa térmica", "relógio esportivo", "barraca de camping",
                "fone bluetooth", "bicicleta ergométrica", "colchonete de yoga", "lanterna de cabeça", "saco de dormir",
                "bota de trekking", "jaqueta impermeável"]
    MARCAS = ["trilhamax", "corremais", "campobase"]
    AUTORES = ["Ana Lima", "Bruno Reis", "Carla Nunes", "Diego Prado"]
    # (dia relativo ao início de uma janela de 120 dias, efeito relativo verdadeiro)
    UPDATE_ALGORITMO = (95, -0.12)

    def __init__(self, seed: int = 42, site_url: str = DataSimulatorConfig.SITE_URL):
        self.seed = seed
        self.site_url = site_url.rstrip("/")

    # ---------- páginas ----------
    def _pages(self, rng):
        import pandas as pd
        rows, codes = [], []

        def add(path, template, title, tipo):
            profundidade = rng.choice(["rasa", "media", "profunda"], p=[0.3, 0.45, 0.25])
            words = {"rasa": rng.integers(80, 300), "media": rng.integers(300, 1200),
                     "profunda": rng.integers(1200, 3500)}[profundidade]
            if tipo in ("home", "institucional", "categoria"):
                autoria = "sem_autoria"
            else:
                autoria = rng.choice(["sem_autoria", "autor_identificado", "autor_com_credenciais"], p=[0.35, 0.4, 0.25])
            autor = rng.choice(self.AUTORES)
            byline = {
                # "Equipe" e "Redação" parecem assinatura, mas não identificam ninguém
                "sem_autoria": rng.choice(["", "", "Equipe Editorial", "Redação"]),
                "autor_identificado": rng.choice([f"Por {autor}", f"Escrito por {autor}", f"{autor}"]),
                "autor_com_credenciais": rng.choice([
                    f"Por {autor}, fisioterapeuta com 10 anos de experiência em corrida",
                    f"Por {autor}. Revisado por especialista em equipamentos",
                    f"{autor}, guia de montanha certificado, testou o produto por 3 meses",
                ]),
            }[autoria]
            page = self.site_url + path
            rows.append({"page": page, "template": template, "title": title, "word_count": int(words), "byline": byline})
            for variable, category in [("tipo_pagina", tipo), ("profundidade", profundidade), ("autoria", autoria)]:
                codes.append({"corpus": "seo_paginas", "unit_id": page, "variable": variable,
                              "coder": "verdade_simulador", "category": category})

        for path, title in self.INSTITUCIONAIS:
            add(path, "institucional", title, "home" if path == "/" else "institucional")
        for i in range(self.TEMPLATES["produto"]):
            nome = self.PRODUTOS[i % len(self.PRODUTOS)]
            add(f"/produtos/item-{i + 1:02d}", "produto", f"{nome.capitalize()} modelo {i + 1}", "produto")
        for i in range(self.TEMPLATES["categoria"]):
            add(f"/produtos/categoria-{i + 1:02d}", "categoria", f"Categoria: {self.PRODUTOS[i % len(self.PRODUTOS)]}", "categoria")
        for i in range(self.TEMPLATES["post"]):
            nome = self.PRODUTOS[i % len(self.PRODUTOS)]
            titulo = [f"Como escolher {nome}", f"Guia completo de {nome}", f"{nome.capitalize()}: vale a pena?"][i % 3]
            add(f"/blog/artigo-{i + 1:02d}", "post", titulo, "post")
        return pd.DataFrame(rows), codes

    # ---------- intervenções ----------
    def _interventions(self, rng, pages, base, start):
        import pandas as pd

        def of(template):
            return pages.loc[pages["template"] == template, "page"].tolist()

        def day(n):
            return (start + timedelta(days=n)).date()

        produtos, categorias, posts = of("produto"), of("categoria"), of("post")
        # escolhida a dedo: as categorias de maior tráfego (viés de seleção de propósito)
        cat_tratadas = sorted(categorias, key=lambda p: -base[p])[:12]
        # sorteada: metade dos produtos
        prod_tratados = set(rng.permutation(produtos)[:20].tolist())

        interventions = pd.DataFrame([
            {"intervention_id": "titulos_blog", "name": "Novos títulos nos posts do blog",
             "description": "Todos os posts tiveram o título reescrito no mesmo dia.", "kind": "mudanca",
             "date": day(60), "template": "post", "randomized": False, "true_effect": 0.15},
            {"intervention_id": "schema_categorias", "name": "Dados estruturados nas categorias de maior tráfego",
             "description": "A equipe escolheu as 12 categorias mais visitadas para receber a mudança.", "kind": "mudanca",
             "date": day(70), "template": "categoria", "randomized": False, "true_effect": 0.20},
            {"intervention_id": "descricao_produtos_ab", "name": "Teste A/B: nova descrição de produto",
             "description": "Metade das páginas de produto, sorteada, recebeu a nova descrição.", "kind": "mudanca",
             "date": day(75), "template": "produto", "randomized": True, "true_effect": 0.10},
            {"intervention_id": "update_algoritmo", "name": "Atualização do algoritmo do buscador",
             "description": "Evento externo que atingiu todas as páginas do site.", "kind": "externo",
             "date": day(self.UPDATE_ALGORITMO[0]), "template": None, "randomized": False,
             "true_effect": self.UPDATE_ALGORITMO[1]},
        ])
        cat_controle = [p for p in categorias if p not in cat_tratadas]
        mapping = (
            [("titulos_blog", p, "tratado") for p in posts]
            + [("titulos_blog", p, "controle") for p in cat_controle]   # categorias nunca alteradas
            + [("schema_categorias", p, "tratado") for p in cat_tratadas]
            + [("schema_categorias", p, "controle") for p in cat_controle]
            + [("descricao_produtos_ab", p, "tratado" if p in prod_tratados else "controle") for p in produtos]
        )
        return interventions, pd.DataFrame(mapping, columns=["intervention_id", "page", "grp"])

    # ---------- painel página×dia ----------
    def _daily(self, rng, pages, base, start, days, interventions, mapping):
        import numpy as np
        import pandas as pd

        effect_start = {}   # página -> (dia, efeito)
        for row in interventions[interventions["kind"] == "mudanca"].itertuples():
            offset = (row.date - start.date()).days
            for page in mapping.query("intervention_id == @row.intervention_id and grp == 'tratado'")["page"]:
                effect_start[page] = (offset, row.true_effect)
        upd_day, upd_effect = self.UPDATE_ALGORITMO

        t = np.arange(days)
        common = (1 + 0.15 * np.sin(2 * np.pi * (t + start.weekday()) / 7)) * (1 + 0.001 * t)
        common = common * np.where(t >= upd_day, 1 + upd_effect, 1.0)
        frames = []
        for page in pages["page"]:
            off, eff = effect_start.get(page, (days + 1, 0.0))
            treated_now = t >= off
            lam = base[page] * common * np.where(treated_now, 1 + eff, 1.0)
            clicks = rng.poisson(lam)
            position = np.clip(rng.normal(6.0, 1.5) - np.where(treated_now, 0.4, 0.0) + rng.normal(0, 0.3, days), 1, 50)
            impressions = np.maximum(clicks, rng.poisson(lam * position * 2.5))
            frames.append(pd.DataFrame({
                "page": page, "date": [(start + timedelta(days=int(d))).date() for d in t],
                "clicks": clicks, "impressions": impressions, "position": np.round(position, 2),
            }))
        return pd.concat(frames, ignore_index=True)

    # ---------- consultas ----------
    def _queries(self, rng):
        import pandas as pd
        patterns = {
            "informacional": ["como escolher {p}", "o que é {p}", "como usar {p}", "para que serve {p}",
                              "dicas de {p}", "{p} como funciona"],
            "navegacional": ["{m}", "{m} site oficial", "{m} login", "loja {m}", "{m} telefone"],
            "comercial": ["melhor {p}", "{p} vale a pena", "{p} avaliação", "{p} ou {q}", "top 10 {p}",
                          "{p}"],            # consulta "seca": a intenção não está escrita
            "transacional": ["comprar {p}", "{p} preço", "{p} promoção", "{p} frete grátis", "{p} barato", "onde comprar {p}"],
        }
        formats = {   # formato dominante da página de resultados, por intenção
            "informacional": (["snippet_em_destaque", "video", "links_organicos"], [0.5, 0.2, 0.3]),
            "navegacional": (["sitelinks", "links_organicos"], [0.8, 0.2]),
            "comercial": (["links_organicos", "shopping", "video"], [0.55, 0.3, 0.15]),
            "transacional": (["shopping", "links_organicos", "pacote_local"], [0.6, 0.25, 0.15]),
        }
        ctr_factor = {"links_organicos": 1.0, "sitelinks": 1.6, "snippet_em_destaque": 0.6,
                      "video": 0.7, "shopping": 0.5, "pacote_local": 0.65}
        rows, codes, seen = [], [], set()
        for intent, pats in patterns.items():
            for pat in pats:
                for i, p in enumerate(self.PRODUTOS):
                    query = pat.format(p=p, q=self.PRODUTOS[(i + 5) % len(self.PRODUTOS)], m=self.MARCAS[i % len(self.MARCAS)])
                    if query in seen:
                        continue
                    seen.add(query)
                    names, probs = formats[intent]
                    dominant = str(rng.choice(names, p=probs))
                    others = [n for n in ctr_factor if n != dominant]
                    extra = str(rng.choice(others))
                    share = round(float(rng.uniform(0.5, 0.8)), 2)
                    position = round(float(np.clip(rng.lognormal(1.2, 0.6), 1, 40)), 2)
                    impressions = int(rng.lognormal(6, 1))
                    ctr = min(0.6, 0.30 / position * ctr_factor[dominant])
                    rows.append({"query": query, "clicks": int(rng.binomial(impressions, ctr)), "impressions": impressions,
                                 "position": position, "serp_features": f"{dominant}:{share}|{extra}:{round(1 - share, 2)}"})
                    for variable, category in [("intencao", intent), ("formato_serp", dominant)]:
                        codes.append({"corpus": "seo_consultas", "unit_id": query, "variable": variable,
                                      "coder": "verdade_simulador", "category": category})
        return pd.DataFrame(rows), codes

    def generate(self, days: int = 120, end_date: datetime = None) -> Dict[str, Any]:
        """Devolve DataFrames: pages, daily, interventions, intervention_pages, queries, codes."""
        import pandas as pd
        if days < 110:
            raise ValueError("O painel de experimentos precisa de pelo menos 110 dias (intervenções até o dia 95).")
        rng = np.random.default_rng(self.seed)
        end = (end_date or datetime(2025, 11, 11)).replace(hour=0, minute=0, second=0, microsecond=0)
        start = end - timedelta(days=days - 1)
        pages, page_codes = self._pages(rng)
        scale = {"produto": 3.6, "categoria": 4.2, "post": 3.9, "institucional": 3.0}
        base = {r.page: float(rng.lognormal(scale[r.template], 0.5)) for r in pages.itertuples()}
        interventions, mapping = self._interventions(rng, pages, base, start)
        # sequências separadas: o painel depende das datas, as consultas não podem depender dele
        daily = self._daily(np.random.default_rng([self.seed, 1]), pages, base, start, days, interventions, mapping)
        queries, query_codes = self._queries(np.random.default_rng([self.seed, 2]))
        return {"pages": pages, "daily": daily, "interventions": interventions, "intervention_pages": mapping,
                "queries": queries, "codes": pd.DataFrame(page_codes + query_codes)}


def main():
    """Função principal - executa simulação completa"""
    parser = argparse.ArgumentParser(
        description="Simulador de dados GA4 e Google Search Console"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Número de dias de dados a gerar (padrão: 30)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Mostra informações detalhadas durante a execução"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Limpa dados existentes antes de inserir novos"
    )
    
    args = parser.parse_args()
    
    # Configura encoding UTF-8 para Windows
    import sys
    import io
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    print("=" * 70)
    print("🔮 SIMULADOR DE DADOS - GA4 & GOOGLE SEARCH CONSOLE")
    print("=" * 70)
    print()
    
    # Conecta ao banco
    try:
        db = GA4DatabaseStorage()
        print("✅ Conectado ao banco de dados DuckDB")
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco: {e}")
        return 1
    
    # Limpa dados se solicitado
    if args.clear:
        print("\n🗑️  Limpando dados existentes...")
        tables = [
            "traffic", "conversions", "engagement",
            "gsc_query_performance", "gsc_page_performance",
            "gsc_country_performance", "gsc_device_performance",
            "gsc_date_performance"
        ]
        for table in tables:
            try:
                db.conn.execute(f"DELETE FROM {table}")
                print(f"   ✓ Tabela '{table}' limpa")
            except Exception as e:
                print(f"   ⚠️  Erro ao limpar '{table}': {e}")
        print()
    
    # Define período de simulação
    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.days - 1)
    
    print(f"📅 Período de simulação:")
    print(f"   De: {start_date.strftime('%Y-%m-%d')}")
    print(f"   Até: {end_date.strftime('%Y-%m-%d')}")
    print(f"   Total: {args.days} dias")
    print()
    
    # ========== SIMULAÇÃO GA4 ==========
    print("📊 GOOGLE ANALYTICS 4")
    print("-" * 70)
    
    ga4_sim = GA4Simulator()
    
    # 1. Tráfego
    print("🚦 Gerando dados de tráfego...")
    traffic_data = ga4_sim.generate_traffic_data(start_date, args.days)
    if args.verbose:
        print(f"   → {len(traffic_data)} registros gerados")
    
    db.insert_traffic_data(traffic_data)
    print(f"   ✅ {len(traffic_data)} registros de tráfego inseridos")
    
    # 2. Conversões
    print("🎯 Gerando dados de conversões...")
    conversions_data = ga4_sim.generate_conversions_data(start_date, args.days)
    if args.verbose:
        print(f"   → {len(conversions_data)} registros gerados")
    
    db.insert_conversions_data(conversions_data)
    print(f"   ✅ {len(conversions_data)} registros de conversões inseridos")
    
    # 3. Engajamento
    print("💎 Gerando dados de engajamento...")
    engagement_data = ga4_sim.generate_engagement_data(start_date, args.days)
    if args.verbose:
        print(f"   → {len(engagement_data)} registros gerados")
    
    db.insert_engagement_data(engagement_data)
    print(f"   ✅ {len(engagement_data)} registros de engajamento inseridos")
    
    print()
    
    # ========== SIMULAÇÃO GSC ==========
    print("🔍 GOOGLE SEARCH CONSOLE")
    print("-" * 70)
    
    gsc_sim = GSCSimulator()
    
    # 1. Performance por Query
    print("🔑 Gerando dados de queries (palavras-chave)...")
    query_data = gsc_sim.generate_query_performance(start_date, end_date)
    if args.verbose:
        print(f"   → {len(query_data)} registros gerados")
    
    db.insert_gsc_query_data(query_data)
    print(f"   ✅ {len(query_data)} registros de queries inseridos")
    
    # 2. Performance por Página
    print("📄 Gerando dados de páginas...")
    page_data = gsc_sim.generate_page_performance(start_date, end_date)
    if args.verbose:
        print(f"   → {len(page_data)} registros gerados")
    
    db.insert_gsc_page_data(page_data)
    print(f"   ✅ {len(page_data)} registros de páginas inseridos")
    
    # 3. Performance por País
    print("🌍 Gerando dados por país...")
    country_data = gsc_sim.generate_country_performance(start_date, end_date)
    if args.verbose:
        print(f"   → {len(country_data)} registros gerados")
    
    db.insert_gsc_country_data(country_data)
    print(f"   ✅ {len(country_data)} registros por país inseridos")
    
    # 4. Performance por Dispositivo
    print("📱 Gerando dados por dispositivo...")
    device_data = gsc_sim.generate_device_performance(start_date, end_date)
    if args.verbose:
        print(f"   → {len(device_data)} registros gerados")
    
    db.insert_gsc_device_data(device_data)
    print(f"   ✅ {len(device_data)} registros por dispositivo inseridos")
    
    # 5. Performance Diária (Série Temporal)
    print("📈 Gerando série temporal diária...")
    date_data = gsc_sim.generate_date_performance(start_date, args.days)
    if args.verbose:
        print(f"   → {len(date_data)} registros gerados")
    
    db.insert_gsc_date_data(date_data)
    print(f"   ✅ {len(date_data)} registros de série temporal inseridos")
    
    print()
    
    # ========== RESUMO FINAL ==========
    print("=" * 70)
    print("✨ SIMULAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 70)
    print()
    print("📊 Resumo dos dados inseridos:")
    print(f"   GA4 Traffic:             {len(traffic_data):>6} registros")
    print(f"   GA4 Conversions:         {len(conversions_data):>6} registros")
    print(f"   GA4 Engagement:          {len(engagement_data):>6} registros")
    print(f"   GSC Query Performance:   {len(query_data):>6} registros")
    print(f"   GSC Page Performance:    {len(page_data):>6} registros")
    print(f"   GSC Country Performance: {len(country_data):>6} registros")
    print(f"   GSC Device Performance:  {len(device_data):>6} registros")
    print(f"   GSC Date Performance:    {len(date_data):>6} registros")
    print("   " + "-" * 40)
    total = (len(traffic_data) + len(conversions_data) + len(engagement_data) +
             len(query_data) + len(page_data) + len(country_data) +
             len(device_data) + len(date_data))
    print(f"   TOTAL:                   {total:>6} registros")
    print()
    print("🚀 Próximos passos:")
    print("   1. Inicie a API: uvicorn app.main:app --reload")
    print("   2. Acesse: http://localhost:8000/docs")
    print("   3. Teste os endpoints com os dados simulados!")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
