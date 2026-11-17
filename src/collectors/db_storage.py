"""
Módulo para armazenamento de dados GA4 e GSC em banco de dados local (DuckDB).

Implementa schema, inserção de dados JSON (com limpeza automática) e queries básicas.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

try:
    import duckdb
except ImportError:
    duckdb = None

# Importa módulo de limpeza
try:
    from ..cleaning import GA4DataCleaner, GSCDataCleaner, DeduplicateData
    CLEANING_AVAILABLE = True
except ImportError:
    CLEANING_AVAILABLE = False
    print("⚠️  Módulo de limpeza não disponível. Dados serão inseridos sem pré-processamento.")


class GA4DatabaseStorage:
    """Gerencia armazenamento de dados GA4 e GSC em banco DuckDB."""

    def __init__(
        self,
        db_path: str = "data/processed/ga4_data.duckdb",
        auto_clean: bool = True,
        auto_deduplicate: bool = True
    ):
        """
        Inicializa storage do banco de dados.

        Args:
            db_path: Caminho para arquivo do banco DuckDB
            auto_clean: Se True, limpa dados automaticamente antes de inserir
            auto_deduplicate: Se True, remove duplicatas antes de inserir
        """
        if duckdb is None:
            raise ImportError(
                "DuckDB não instalado. Execute: pip install duckdb"
            )

        # Cria diretório se não existir
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self.db_path = db_path
        self.conn = duckdb.connect(db_path)
        self.auto_clean = auto_clean and CLEANING_AVAILABLE
        self.auto_deduplicate = auto_deduplicate and CLEANING_AVAILABLE
        
        if auto_clean and not CLEANING_AVAILABLE:
            print("⚠️  auto_clean=True mas módulo de limpeza não disponível")
        
        self._create_tables()

    def _create_tables(self):
        """Cria tabelas para armazenar dados GA4."""
        # Tabela para dados de tráfego
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS traffic (
                id INTEGER PRIMARY KEY,
                property_id VARCHAR,
                date DATE,
                session_source VARCHAR,
                session_medium VARCHAR,
                session_campaign_name VARCHAR,
                sessions BIGINT,
                active_users BIGINT,
                new_users BIGINT,
                screen_page_views BIGINT,
                average_session_duration DOUBLE,
                collected_at TIMESTAMP,
                UNIQUE(property_id, date, session_source, session_medium, session_campaign_name)
            )
        """)

        # Tabela para dados de conversões
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS conversions (
                id INTEGER PRIMARY KEY,
                property_id VARCHAR,
                date DATE,
                event_name VARCHAR,
                session_source VARCHAR,
                session_medium VARCHAR,
                key_events BIGINT,
                event_count BIGINT,
                total_revenue DOUBLE,
                transactions BIGINT,
                purchase_revenue DOUBLE,
                collected_at TIMESTAMP,
                UNIQUE(property_id, date, event_name, session_source, session_medium)
            )
        """)

        # Tabela para dados de engajamento
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS engagement (
                id INTEGER PRIMARY KEY,
                property_id VARCHAR,
                date DATE,
                page_path VARCHAR,
                unified_screen_name VARCHAR,
                device_category VARCHAR,
                engagement_rate DOUBLE,
                engaged_sessions BIGINT,
                average_session_duration DOUBLE,
                event_count BIGINT,
                user_engagement_duration BIGINT,
                collected_at TIMESTAMP,
                UNIQUE(property_id, date, page_path, unified_screen_name, device_category)
            )
        """)

        # Tabela para dados em tempo real
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS realtime_traffic (
                id INTEGER PRIMARY KEY,
                property_id VARCHAR,
                unified_screen_name VARCHAR,
                country VARCHAR,
                city VARCHAR,
                active_users BIGINT,
                screen_page_views BIGINT,
                collected_at TIMESTAMP
            )
        """)

        # ===== TABELAS GOOGLE SEARCH CONSOLE =====
        
        # Tabela para performance de queries (palavras-chave)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS gsc_query_performance (
                id INTEGER PRIMARY KEY,
                site_url VARCHAR,
                query VARCHAR,
                clicks BIGINT,
                impressions BIGINT,
                ctr DOUBLE,
                position DOUBLE,
                start_date DATE,
                end_date DATE,
                collected_at TIMESTAMP,
                UNIQUE(site_url, query, start_date, end_date)
            )
        """)

        # Tabela para performance de páginas (URLs)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS gsc_page_performance (
                id INTEGER PRIMARY KEY,
                site_url VARCHAR,
                page VARCHAR,
                clicks BIGINT,
                impressions BIGINT,
                ctr DOUBLE,
                position DOUBLE,
                start_date DATE,
                end_date DATE,
                collected_at TIMESTAMP,
                UNIQUE(site_url, page, start_date, end_date)
            )
        """)

        # Tabela para performance por país
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS gsc_country_performance (
                id INTEGER PRIMARY KEY,
                site_url VARCHAR,
                country VARCHAR,
                clicks BIGINT,
                impressions BIGINT,
                ctr DOUBLE,
                position DOUBLE,
                start_date DATE,
                end_date DATE,
                collected_at TIMESTAMP,
                UNIQUE(site_url, country, start_date, end_date)
            )
        """)

        # Tabela para performance por dispositivo
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS gsc_device_performance (
                id INTEGER PRIMARY KEY,
                site_url VARCHAR,
                device VARCHAR,
                clicks BIGINT,
                impressions BIGINT,
                ctr DOUBLE,
                position DOUBLE,
                start_date DATE,
                end_date DATE,
                collected_at TIMESTAMP,
                UNIQUE(site_url, device, start_date, end_date)
            )
        """)

        # Tabela para performance diária (série temporal)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS gsc_date_performance (
                id INTEGER PRIMARY KEY,
                site_url VARCHAR,
                date DATE,
                clicks BIGINT,
                impressions BIGINT,
                ctr DOUBLE,
                position DOUBLE,
                collected_at TIMESTAMP,
                UNIQUE(site_url, date)
            )
        """)

        # Tabela para performance combinada query+page
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS gsc_query_page_performance (
                id INTEGER PRIMARY KEY,
                site_url VARCHAR,
                query VARCHAR,
                page VARCHAR,
                clicks BIGINT,
                impressions BIGINT,
                ctr DOUBLE,
                position DOUBLE,
                start_date DATE,
                end_date DATE,
                collected_at TIMESTAMP,
                UNIQUE(site_url, query, page, start_date, end_date)
            )
        """)

        # ===== TABELAS QUASE-EXPERIMENTOS E ANÁLISE DE CONTEÚDO =====
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS seo_pages (
                page VARCHAR PRIMARY KEY, template VARCHAR, title VARCHAR, word_count BIGINT, byline VARCHAR
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS seo_page_daily (
                page VARCHAR, date DATE, clicks BIGINT, impressions BIGINT, position DOUBLE,
                PRIMARY KEY (page, date)
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS seo_interventions (
                intervention_id VARCHAR PRIMARY KEY, name VARCHAR, description VARCHAR,
                kind VARCHAR,          -- 'mudanca' (do site) ou 'externo' (da plataforma)
                date DATE, template VARCHAR, randomized BOOLEAN,
                true_effect DOUBLE     -- só existe porque o dado é simulado
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS seo_intervention_pages (
                intervention_id VARCHAR, page VARCHAR, grp VARCHAR,   -- 'tratado' ou 'controle'
                PRIMARY KEY (intervention_id, page)
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS seo_queries (
                query VARCHAR PRIMARY KEY, clicks BIGINT, impressions BIGINT, position DOUBLE,
                serp_features VARCHAR   -- 'formato:área|formato:área'
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS content_codes (
                corpus VARCHAR, unit_id VARCHAR, variable VARCHAR, coder VARCHAR, category VARCHAR,
                PRIMARY KEY (corpus, unit_id, variable, coder)
            )
        """)

        # ===== TABELAS MÉTODOS DIGITAIS (WIKIPEDIA) =====
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS wiki_pages (
                lang VARCHAR, title VARCHAR, seed VARCHAR, pageid BIGINT,
                length BIGINT, pageviews_30d BIGINT, collected_at TIMESTAMP,
                PRIMARY KEY (lang, seed, title)  -- um artigo pode estar no recorte de várias sementes
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS wiki_revisions (
                lang VARCHAR, title VARCHAR, revid BIGINT, parentid BIGINT,
                "timestamp" TIMESTAMP, "user" VARCHAR, actor_type VARCHAR,
                size BIGINT, size_diff BIGINT, minor BOOLEAN, comment VARCHAR,
                tags VARCHAR,  -- separadas por '|'
                PRIMARY KEY (lang, revid)
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS wiki_links (
                lang VARCHAR, seed VARCHAR, source VARCHAR, target VARCHAR,
                PRIMARY KEY (lang, seed, source, target)
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS wiki_editions (
                seed_lang VARCHAR, seed_title VARCHAR, lang VARCHAR, title VARCHAR,
                length BIGINT, pageviews_30d BIGINT,
                PRIMARY KEY (seed_lang, seed_title, lang)
            )
        """)

        print("OK Tabelas criadas/verificadas no banco de dados (GA4 + GSC)")

    def save_seo_experiment(self, data: Dict[str, Any]) -> Dict[str, int]:
        """
        Grava a saída de `ExperimentSimulator.generate`, substituindo o painel anterior,
        os códigos verdadeiros do simulador e os códigos automáticos dos corpora simulados
        (que precisam ser refeitos com POST /content-analysis/code). A referência fica.
        """
        tables = [("seo_pages", "pages"), ("seo_page_daily", "daily"), ("seo_interventions", "interventions"),
                  ("seo_intervention_pages", "intervention_pages"), ("seo_queries", "queries")]
        self.conn.execute("BEGIN")
        try:
            for table, key in tables:
                self.conn.execute(f"DELETE FROM {table}")
            self.conn.execute("""DELETE FROM content_codes WHERE coder = 'verdade_simulador'
                                 OR (corpus LIKE 'seo_%' AND coder IN ('regras', 'llm'))""")
            for table, key in tables + [("content_codes", "codes")]:
                self.conn.register("_seo_df", data[key])
                self.conn.execute(f"INSERT INTO {table} BY NAME SELECT * FROM _seo_df")
                self.conn.unregister("_seo_df")
            self.conn.execute("COMMIT")
        except Exception:
            self.conn.execute("ROLLBACK")
            raise
        return {key: len(data[key]) for _, key in tables}

    def save_codes(self, codes) -> int:
        """Grava códigos de análise de conteúdo (DataFrame corpus, unit_id, variable, coder, category), substituindo os iguais."""
        if len(codes) == 0:
            return 0
        self.conn.register("_codes_df", codes)
        self.conn.execute("INSERT OR REPLACE INTO content_codes BY NAME SELECT * FROM _codes_df")
        self.conn.unregister("_codes_df")
        return len(codes)

    def save_wiki(self, data: Dict[str, Any]) -> Dict[str, int]:
        """
        Grava o resultado de `wikipedia.collect_topic`. Páginas e links pertencem
        à semente (recoletar substitui o recorte dela sem tocar no de outras);
        revisões pertencem ao artigo e são atualizadas para os artigos coletados.

        Returns:
            Contagem de linhas gravadas por tabela.
        """
        import pandas as pd

        lang, seed = data["lang"], data["seed"]
        titles = [p["title"] for p in data["pages"]]

        pages = pd.DataFrame(data["pages"]).assign(lang=lang, seed=seed, collected_at=datetime.now())
        revisions = pd.DataFrame([
            {**r, "lang": lang, "title": t, "tags": "|".join(r["tags"])}
            for t, revs in data["revisions"].items() for r in revs
        ])
        if not revisions.empty:
            revisions["timestamp"] = pd.to_datetime(revisions["timestamp"], utc=True).dt.tz_localize(None)
        links = pd.DataFrame(data["links"], columns=["source", "target"]).assign(lang=lang, seed=seed)
        editions = pd.DataFrame(data["editions"]).assign(seed_lang=lang, seed_title=seed)

        self.conn.execute("BEGIN")
        try:
            self.conn.execute("DELETE FROM wiki_pages WHERE lang = ? AND seed = ?", [lang, seed])
            self.conn.execute("DELETE FROM wiki_links WHERE lang = ? AND seed = ?", [lang, seed])
            self.conn.execute("DELETE FROM wiki_revisions WHERE lang = ? AND title IN (SELECT unnest(?))", [lang, titles])
            self.conn.execute("DELETE FROM wiki_editions WHERE seed_lang = ? AND seed_title = ?", [lang, seed])
            for table, df in [("wiki_pages", pages), ("wiki_revisions", revisions),
                              ("wiki_links", links), ("wiki_editions", editions)]:
                if not df.empty:
                    self.conn.register("_wiki_df", df)
                    self.conn.execute(f"INSERT INTO {table} BY NAME SELECT * FROM _wiki_df")
                    self.conn.unregister("_wiki_df")
            # revisões de artigos que saíram de todos os recortes
            self.conn.execute(
                "DELETE FROM wiki_revisions WHERE lang = ? AND title NOT IN (SELECT title FROM wiki_pages WHERE lang = ?)",
                [lang, lang])
            self.conn.execute("COMMIT")
        except Exception:
            self.conn.execute("ROLLBACK")
            raise

        return {"pages": len(pages), "revisions": len(revisions), "links": len(links), "editions": len(editions)}

    def insert_from_json(self, json_filepath: str) -> int:
        """
        Insere dados de um arquivo JSON no banco.

        Args:
            json_filepath: Caminho do arquivo JSON com dados GA4

        Returns:
            Número de linhas inseridas
        """
        with open(json_filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        report_type = data["metadata"]["report_type"]
        collected_at = data["metadata"]["collected_at"]
        rows = data["rows"]

        # Identifica se é GA4 ou GSC
        if "property_id" in data["metadata"]:
            # GA4 data
            property_id = data["metadata"]["property_id"]
            insert_methods = {
                "traffic": self._insert_traffic_rows,
                "conversions": self._insert_conversion_rows,
                "engagement": self._insert_engagement_rows,
                "realtime_traffic": self._insert_realtime_rows,
            }
            
            if report_type not in insert_methods:
                raise ValueError(f"Tipo de report GA4 desconhecido: {report_type}")

            inserted_count = insert_methods[report_type](
                property_id, rows, collected_at
            )
        
        elif "site_url" in data["metadata"]:
            # GSC data
            site_url = data["metadata"]["site_url"]
            start_date = data["metadata"].get("start_date")
            end_date = data["metadata"].get("end_date")
            
            insert_methods = {
                "query_performance": self._insert_gsc_query_rows,
                "page_performance": self._insert_gsc_page_rows,
                "country_performance": self._insert_gsc_country_rows,
                "device_performance": self._insert_gsc_device_rows,
                "date_performance": self._insert_gsc_date_rows,
                "query_page_performance": self._insert_gsc_query_page_rows,
            }
            
            if report_type not in insert_methods:
                raise ValueError(f"Tipo de report GSC desconhecido: {report_type}")

            inserted_count = insert_methods[report_type](
                site_url, rows, collected_at, start_date, end_date
            )
        
        else:
            raise ValueError("Tipo de dados desconhecido (não é GA4 nem GSC)")

        print(f"OK Inseridas {inserted_count} linhas na tabela '{report_type}'")
        return inserted_count

    def _insert_traffic_rows(
        self, property_id: str, rows: List[Dict], collected_at: str
    ) -> int:
        """Insere rows de tráfego no banco."""
        # Deduplicação (se habilitado)
        if self.auto_deduplicate:
            original_count = len(rows)
            # Prepara rows com property_id e collected_at
            prepared_rows = [
                {**row, "property_id": property_id, "collected_at": collected_at}
                for row in rows
            ]
            deduplicated = DeduplicateData.deduplicate_ga4_traffic(prepared_rows)
            rows = deduplicated
            
            if len(rows) < original_count:
                print(f"  🔄 Deduplicação: {original_count} → {len(rows)} linhas "
                      f"({original_count - len(rows)} duplicatas removidas)")
        
        inserted = 0
        for row in rows:
            try:
                # Limpeza automática (se habilitado)
                if self.auto_clean:
                    cleaned_row = GA4DataCleaner.clean_traffic_row({
                        "property_id": property_id,
                        "date": row.get("date"),
                        "session_source": row.get("sessionSource"),
                        "session_medium": row.get("sessionMedium"),
                        "session_campaign_name": row.get("sessionCampaignName"),
                        "sessions": row.get("sessions"),
                        "active_users": row.get("activeUsers"),
                        "new_users": row.get("newUsers"),
                        "screen_page_views": row.get("screenPageViews"),
                        "average_session_duration": row.get("averageSessionDuration"),
                        "collected_at": collected_at,
                    })
                else:
                    cleaned_row = {
                        "property_id": property_id,
                        "date": row.get("date"),
                        "session_source": row.get("sessionSource"),
                        "session_medium": row.get("sessionMedium"),
                        "session_campaign_name": row.get("sessionCampaignName"),
                        "sessions": int(row.get("sessions", 0)),
                        "active_users": int(row.get("activeUsers", 0)),
                        "new_users": int(row.get("newUsers", 0)),
                        "screen_page_views": int(row.get("screenPageViews", 0)),
                        "average_session_duration": float(row.get("averageSessionDuration", 0)),
                        "collected_at": collected_at,
                    }
                
                self.conn.execute("""
                    INSERT OR REPLACE INTO traffic (
                        property_id, date, session_source, session_medium,
                        session_campaign_name, sessions, active_users, new_users,
                        screen_page_views, average_session_duration, collected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    cleaned_row["property_id"],
                    cleaned_row["date"],
                    cleaned_row["session_source"],
                    cleaned_row["session_medium"],
                    cleaned_row["session_campaign_name"],
                    int(cleaned_row["sessions"]),
                    int(cleaned_row["active_users"]),
                    int(cleaned_row["new_users"]),
                    int(cleaned_row["screen_page_views"]),
                    float(cleaned_row["average_session_duration"]),
                    cleaned_row["collected_at"],
                ])
                inserted += 1
            except Exception as e:
                print(f"Erro ao inserir row: {e}")
                continue

        return inserted

    def _insert_conversion_rows(
        self, property_id: str, rows: List[Dict], collected_at: str
    ) -> int:
        """Insere rows de conversões no banco."""
        inserted = 0
        for row in rows:
            try:
                self.conn.execute("""
                    INSERT OR REPLACE INTO conversions (
                        property_id, date, event_name, session_source,
                        session_medium, key_events, event_count, total_revenue,
                        transactions, purchase_revenue, collected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    property_id,
                    row.get("date"),
                    row.get("eventName"),
                    row.get("sessionSource"),
                    row.get("sessionMedium"),
                    int(row.get("keyEvents", 0)),
                    int(row.get("eventCount", 0)),
                    float(row.get("totalRevenue", 0)),
                    int(row.get("transactions", 0)),
                    float(row.get("purchaseRevenue", 0)),
                    collected_at,
                ])
                inserted += 1
            except Exception as e:
                print(f"Erro ao inserir row: {e}")
                continue

        return inserted

    def _insert_engagement_rows(
        self, property_id: str, rows: List[Dict], collected_at: str
    ) -> int:
        """Insere rows de engajamento no banco."""
        inserted = 0
        for row in rows:
            try:
                self.conn.execute("""
                    INSERT OR REPLACE INTO engagement (
                        property_id, date, page_path, unified_screen_name,
                        device_category, engagement_rate, engaged_sessions,
                        average_session_duration, event_count,
                        user_engagement_duration, collected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    property_id,
                    row.get("date"),
                    row.get("pagePath"),
                    row.get("unifiedScreenName"),
                    row.get("deviceCategory"),
                    float(row.get("engagementRate", 0)),
                    int(row.get("engagedSessions", 0)),
                    float(row.get("averageSessionDuration", 0)),
                    int(row.get("eventCount", 0)),
                    int(row.get("userEngagementDuration", 0)),
                    collected_at,
                ])
                inserted += 1
            except Exception as e:
                print(f"Erro ao inserir row: {e}")
                continue

        return inserted

    def _insert_realtime_rows(
        self, property_id: str, rows: List[Dict], collected_at: str
    ) -> int:
        """Insere rows de tráfego em tempo real no banco."""
        inserted = 0
        for row in rows:
            try:
                self.conn.execute("""
                    INSERT INTO realtime_traffic (
                        property_id, unified_screen_name, country, city,
                        active_users, screen_page_views, collected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, [
                    property_id,
                    row.get("unifiedScreenName"),
                    row.get("country"),
                    row.get("city"),
                    int(row.get("activeUsers", 0)),
                    int(row.get("screenPageViews", 0)),
                    collected_at,
                ])
                inserted += 1
            except Exception as e:
                print(f"Erro ao inserir row: {e}")
                continue

        return inserted

    # ===== MÉTODOS DE INSERÇÃO GOOGLE SEARCH CONSOLE =====

    def _insert_gsc_query_rows(
        self, site_url: str, rows: List[Dict], collected_at: str,
        start_date: str, end_date: str
    ) -> int:
        """Insere rows de performance de queries do GSC no banco."""
        inserted = 0
        for row in rows:
            try:
                self.conn.execute("""
                    INSERT OR REPLACE INTO gsc_query_performance (
                        site_url, query, clicks, impressions, ctr, position,
                        start_date, end_date, collected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    site_url,
                    row.get("query"),
                    int(row.get("clicks", 0)),
                    int(row.get("impressions", 0)),
                    float(row.get("ctr", 0.0)),
                    float(row.get("position", 0.0)),
                    start_date,
                    end_date,
                    collected_at,
                ])
                inserted += 1
            except Exception as e:
                print(f"Erro ao inserir query row: {e}")
                continue
        return inserted

    def _insert_gsc_page_rows(
        self, site_url: str, rows: List[Dict], collected_at: str,
        start_date: str, end_date: str
    ) -> int:
        """Insere rows de performance de páginas do GSC no banco."""
        inserted = 0
        for row in rows:
            try:
                self.conn.execute("""
                    INSERT OR REPLACE INTO gsc_page_performance (
                        site_url, page, clicks, impressions, ctr, position,
                        start_date, end_date, collected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    site_url,
                    row.get("page"),
                    int(row.get("clicks", 0)),
                    int(row.get("impressions", 0)),
                    float(row.get("ctr", 0.0)),
                    float(row.get("position", 0.0)),
                    start_date,
                    end_date,
                    collected_at,
                ])
                inserted += 1
            except Exception as e:
                print(f"Erro ao inserir page row: {e}")
                continue
        return inserted

    def _insert_gsc_country_rows(
        self, site_url: str, rows: List[Dict], collected_at: str,
        start_date: str, end_date: str
    ) -> int:
        """Insere rows de performance por país do GSC no banco."""
        inserted = 0
        for row in rows:
            try:
                self.conn.execute("""
                    INSERT OR REPLACE INTO gsc_country_performance (
                        site_url, country, clicks, impressions, ctr, position,
                        start_date, end_date, collected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    site_url,
                    row.get("country"),
                    int(row.get("clicks", 0)),
                    int(row.get("impressions", 0)),
                    float(row.get("ctr", 0.0)),
                    float(row.get("position", 0.0)),
                    start_date,
                    end_date,
                    collected_at,
                ])
                inserted += 1
            except Exception as e:
                print(f"Erro ao inserir country row: {e}")
                continue
        return inserted

    def _insert_gsc_device_rows(
        self, site_url: str, rows: List[Dict], collected_at: str,
        start_date: str, end_date: str
    ) -> int:
        """Insere rows de performance por dispositivo do GSC no banco."""
        inserted = 0
        for row in rows:
            try:
                self.conn.execute("""
                    INSERT OR REPLACE INTO gsc_device_performance (
                        site_url, device, clicks, impressions, ctr, position,
                        start_date, end_date, collected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    site_url,
                    row.get("device"),
                    int(row.get("clicks", 0)),
                    int(row.get("impressions", 0)),
                    float(row.get("ctr", 0.0)),
                    float(row.get("position", 0.0)),
                    start_date,
                    end_date,
                    collected_at,
                ])
                inserted += 1
            except Exception as e:
                print(f"Erro ao inserir device row: {e}")
                continue
        return inserted

    def _insert_gsc_date_rows(
        self, site_url: str, rows: List[Dict], collected_at: str,
        start_date: str = None, end_date: str = None
    ) -> int:
        """Insere rows de performance diária do GSC no banco."""
        inserted = 0
        for row in rows:
            try:
                self.conn.execute("""
                    INSERT OR REPLACE INTO gsc_date_performance (
                        site_url, date, clicks, impressions, ctr, position,
                        collected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, [
                    site_url,
                    row.get("date"),
                    int(row.get("clicks", 0)),
                    int(row.get("impressions", 0)),
                    float(row.get("ctr", 0.0)),
                    float(row.get("position", 0.0)),
                    collected_at,
                ])
                inserted += 1
            except Exception as e:
                print(f"Erro ao inserir date row: {e}")
                continue
        return inserted

    def _insert_gsc_query_page_rows(
        self, site_url: str, rows: List[Dict], collected_at: str,
        start_date: str, end_date: str
    ) -> int:
        """Insere rows de performance query+page do GSC no banco."""
        inserted = 0
        for row in rows:
            try:
                self.conn.execute("""
                    INSERT OR REPLACE INTO gsc_query_page_performance (
                        site_url, query, page, clicks, impressions, ctr, position,
                        start_date, end_date, collected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    site_url,
                    row.get("query"),
                    row.get("page"),
                    int(row.get("clicks", 0)),
                    int(row.get("impressions", 0)),
                    float(row.get("ctr", 0.0)),
                    float(row.get("position", 0.0)),
                    start_date,
                    end_date,
                    collected_at,
                ])
                inserted += 1
            except Exception as e:
                print(f"Erro ao inserir query_page row: {e}")
                continue
        return inserted

    def query(self, sql: str) -> List[tuple]:
        """
        Executa query SQL customizada.

        Args:
            sql: Query SQL

        Returns:
            Lista de tuplas com resultados
        """
        result = self.conn.execute(sql).fetchall()
        return result
    
    def query_df(self, sql: str):
        """
        Executa query SQL e retorna um pandas DataFrame.

        Args:
            sql: Query SQL

        Returns:
            pandas DataFrame com resultados
        """
        import pandas as pd
        result = self.conn.execute(sql).fetchdf()
        return result

    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas resumidas do banco (GA4 + GSC).

        Returns:
            Dict com contagens e datas por tabela
        """
        stats = {}

        # Tabelas GA4
        ga4_tables = ["traffic", "conversions", "engagement", "realtime_traffic"]
        for table in ga4_tables:
            count = self.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            stats[f"ga4_{table}"] = {"row_count": count}

            if count > 0 and table != "realtime_traffic":
                date_range = self.conn.execute(f"""
                    SELECT MIN(date), MAX(date) FROM {table}
                """).fetchone()
                stats[f"ga4_{table}"]["date_range"] = {
                    "min": str(date_range[0]) if date_range[0] else None,
                    "max": str(date_range[1]) if date_range[1] else None,
                }

        # Tabelas GSC
        gsc_tables = [
            "gsc_query_performance",
            "gsc_page_performance",
            "gsc_country_performance",
            "gsc_device_performance",
            "gsc_date_performance",
            "gsc_query_page_performance",
        ]
        for table in gsc_tables:
            count = self.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            stats[table] = {"row_count": count}

            if count > 0:
                if table == "gsc_date_performance":
                    # Tabela diária usa campo 'date' direto
                    date_range = self.conn.execute(f"""
                        SELECT MIN(date), MAX(date) FROM {table}
                    """).fetchone()
                else:
                    # Outras tabelas GSC usam start_date/end_date
                    date_range = self.conn.execute(f"""
                        SELECT MIN(start_date), MAX(end_date) FROM {table}
                    """).fetchone()
                
                stats[table]["date_range"] = {
                    "min": str(date_range[0]) if date_range[0] else None,
                    "max": str(date_range[1]) if date_range[1] else None,
                }

        return stats

    def close(self):
        """Fecha conexão com banco."""
        self.conn.close()
        print("OK Conexão com banco fechada")
    
    # ===== MÉTODOS PÚBLICOS PARA INSERÇÃO DIRETA (usado pelo simulador) =====
    
    def insert_traffic_data(self, rows: List[Dict[str, Any]]) -> int:
        """
        Insere dados de tráfego diretamente (para simulador).
        
        Args:
            rows: Lista de dicts com chaves: property_id, date, session_source,
                  session_medium, session_campaign_name, sessions, active_users,
                  new_users, screen_page_views, average_session_duration
        
        Returns:
            Número de registros inseridos
        """
        inserted = 0
        collected_at = datetime.now().isoformat()
        
        # Pega o próximo ID disponível
        max_id_result = self.conn.execute("SELECT COALESCE(MAX(id), 0) FROM traffic").fetchone()
        next_id = max_id_result[0] + 1 if max_id_result else 1
        
        for row in rows:
            try:
                self.conn.execute("""
                    INSERT INTO traffic (
                        id, property_id, date, session_source, session_medium,
                        session_campaign_name, sessions, active_users, new_users,
                        screen_page_views, average_session_duration, collected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    next_id,
                    row["property_id"],
                    row["date"],
                    row["session_source"],
                    row["session_medium"],
                    row["session_campaign_name"],
                    int(row["sessions"]),
                    int(row["active_users"]),
                    int(row["new_users"]),
                    int(row["screen_page_views"]),
                    float(row["average_session_duration"]),
                    collected_at,
                ])
                next_id += 1
                inserted += 1
            except Exception as e:
                print(f"  ⚠️  Erro ao inserir traffic row: {e}")
                continue
        
        return inserted
    
    def insert_conversions_data(self, rows: List[Dict[str, Any]]) -> int:
        """
        Insere dados de conversões diretamente (para simulador).
        
        Args:
            rows: Lista de dicts com chaves: property_id, date, event_name,
                  session_source, session_medium, key_events, event_count,
                  total_revenue, transactions, purchase_revenue
        
        Returns:
            Número de registros inseridos
        """
        inserted = 0
        collected_at = datetime.now().isoformat()
        
        # Pega o próximo ID disponível
        max_id_result = self.conn.execute("SELECT COALESCE(MAX(id), 0) FROM conversions").fetchone()
        next_id = max_id_result[0] + 1 if max_id_result else 1
        
        for row in rows:
            try:
                self.conn.execute("""
                    INSERT INTO conversions (
                        id, property_id, date, event_name, session_source,
                        session_medium, key_events, event_count, total_revenue,
                        transactions, purchase_revenue, collected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    next_id,
                    row["property_id"],
                    row["date"],
                    row["event_name"],
                    row["session_source"],
                    row["session_medium"],
                    int(row["key_events"]),
                    int(row["event_count"]),
                    float(row["total_revenue"]),
                    int(row["transactions"]),
                    float(row["purchase_revenue"]),
                    collected_at,
                ])
                next_id += 1
                inserted += 1
            except Exception as e:
                print(f"  ⚠️  Erro ao inserir conversions row: {e}")
                continue
        
        return inserted
    
    def insert_engagement_data(self, rows: List[Dict[str, Any]]) -> int:
        """
        Insere dados de engajamento diretamente (para simulador).
        
        Args:
            rows: Lista de dicts com chaves: property_id, date, page_path,
                  unified_screen_name, device_category, engagement_rate,
                  engaged_sessions, average_session_duration, event_count,
                  user_engagement_duration
        
        Returns:
            Número de registros inseridos
        """
        inserted = 0
        collected_at = datetime.now().isoformat()
        
        # Pega o próximo ID disponível
        max_id_result = self.conn.execute("SELECT COALESCE(MAX(id), 0) FROM engagement").fetchone()
        next_id = max_id_result[0] + 1 if max_id_result else 1
        
        for row in rows:
            try:
                self.conn.execute("""
                    INSERT INTO engagement (
                        id, property_id, date, page_path, unified_screen_name,
                        device_category, engagement_rate, engaged_sessions,
                        average_session_duration, event_count,
                        user_engagement_duration, collected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    next_id,
                    row["property_id"],
                    row["date"],
                    row["page_path"],
                    row["unified_screen_name"],
                    row["device_category"],
                    float(row["engagement_rate"]),
                    int(row["engaged_sessions"]),
                    float(row["average_session_duration"]),
                    int(row["event_count"]),
                    int(row["user_engagement_duration"]),
                    collected_at,
                ])
                next_id += 1
                inserted += 1
            except Exception as e:
                print(f"  ⚠️  Erro ao inserir engagement row: {e}")
                continue
        
        return inserted
    
    def insert_gsc_query_data(self, rows: List[Dict[str, Any]]) -> int:
        """
        Insere dados de queries GSC diretamente (para simulador).
        
        Args:
            rows: Lista de dicts com chaves: site_url, query, clicks,
                  impressions, ctr, position, start_date, end_date
        
        Returns:
            Número de registros inseridos
        """
        inserted = 0
        collected_at = datetime.now().isoformat()
        
        # Pega o próximo ID disponível
        max_id_result = self.conn.execute("SELECT COALESCE(MAX(id), 0) FROM gsc_query_performance").fetchone()
        next_id = max_id_result[0] + 1 if max_id_result else 1
        
        for row in rows:
            try:
                self.conn.execute("""
                    INSERT INTO gsc_query_performance (
                        id, site_url, query, clicks, impressions, ctr, position,
                        start_date, end_date, collected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    next_id,
                    row["site_url"],
                    row["query"],
                    int(row["clicks"]),
                    int(row["impressions"]),
                    float(row["ctr"]),
                    float(row["position"]),
                    row["start_date"],
                    row["end_date"],
                    collected_at,
                ])
                next_id += 1
                inserted += 1
            except Exception as e:
                print(f"  ⚠️  Erro ao inserir query row: {e}")
                continue
        
        return inserted
    
    def insert_gsc_page_data(self, rows: List[Dict[str, Any]]) -> int:
        """
        Insere dados de páginas GSC diretamente (para simulador).
        
        Args:
            rows: Lista de dicts com chaves: site_url, page, clicks,
                  impressions, ctr, position, start_date, end_date
        
        Returns:
            Número de registros inseridos
        """
        inserted = 0
        collected_at = datetime.now().isoformat()
        
        # Pega o próximo ID disponível
        max_id_result = self.conn.execute("SELECT COALESCE(MAX(id), 0) FROM gsc_page_performance").fetchone()
        next_id = max_id_result[0] + 1 if max_id_result else 1
        
        for row in rows:
            try:
                self.conn.execute("""
                    INSERT INTO gsc_page_performance (
                        id, site_url, page, clicks, impressions, ctr, position,
                        start_date, end_date, collected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    next_id,
                    row["site_url"],
                    row["page"],
                    int(row["clicks"]),
                    int(row["impressions"]),
                    float(row["ctr"]),
                    float(row["position"]),
                    row["start_date"],
                    row["end_date"],
                    collected_at,
                ])
                next_id += 1
                inserted += 1
            except Exception as e:
                print(f"  ⚠️  Erro ao inserir page row: {e}")
                continue
        
        return inserted
    
    def insert_gsc_country_data(self, rows: List[Dict[str, Any]]) -> int:
        """
        Insere dados de países GSC diretamente (para simulador).
        
        Args:
            rows: Lista de dicts com chaves: site_url, country, clicks,
                  impressions, ctr, position, start_date, end_date
        
        Returns:
            Número de registros inseridos
        """
        inserted = 0
        collected_at = datetime.now().isoformat()
        
        # Pega o próximo ID disponível
        max_id_result = self.conn.execute("SELECT COALESCE(MAX(id), 0) FROM gsc_country_performance").fetchone()
        next_id = max_id_result[0] + 1 if max_id_result else 1
        
        for row in rows:
            try:
                self.conn.execute("""
                    INSERT INTO gsc_country_performance (
                        id, site_url, country, clicks, impressions, ctr, position,
                        start_date, end_date, collected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    next_id,
                    row["site_url"],
                    row["country"],
                    int(row["clicks"]),
                    int(row["impressions"]),
                    float(row["ctr"]),
                    float(row["position"]),
                    row["start_date"],
                    row["end_date"],
                    collected_at,
                ])
                next_id += 1
                inserted += 1
            except Exception as e:
                print(f"  ⚠️  Erro ao inserir country row: {e}")
                continue
        
        return inserted
    
    def insert_gsc_device_data(self, rows: List[Dict[str, Any]]) -> int:
        """
        Insere dados de dispositivos GSC diretamente (para simulador).
        
        Args:
            rows: Lista de dicts com chaves: site_url, device, clicks,
                  impressions, ctr, position, start_date, end_date
        
        Returns:
            Número de registros inseridos
        """
        inserted = 0
        collected_at = datetime.now().isoformat()
        
        # Pega o próximo ID disponível
        max_id_result = self.conn.execute("SELECT COALESCE(MAX(id), 0) FROM gsc_device_performance").fetchone()
        next_id = max_id_result[0] + 1 if max_id_result else 1
        
        for row in rows:
            try:
                self.conn.execute("""
                    INSERT INTO gsc_device_performance (
                        id, site_url, device, clicks, impressions, ctr, position,
                        start_date, end_date, collected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    next_id,
                    row["site_url"],
                    row["device"],
                    int(row["clicks"]),
                    int(row["impressions"]),
                    float(row["ctr"]),
                    float(row["position"]),
                    row["start_date"],
                    row["end_date"],
                    collected_at,
                ])
                next_id += 1
                inserted += 1
            except Exception as e:
                print(f"  ⚠️  Erro ao inserir device row: {e}")
                continue
        
        return inserted
    
    def insert_gsc_date_data(self, rows: List[Dict[str, Any]]) -> int:
        """
        Insere dados de série temporal GSC diretamente (para simulador).
        
        Args:
            rows: Lista de dicts com chaves: site_url, date, clicks,
                  impressions, ctr, position
        
        Returns:
            Número de registros inseridos
        """
        inserted = 0
        collected_at = datetime.now().isoformat()
        
        # Pega o próximo ID disponível
        max_id_result = self.conn.execute("SELECT COALESCE(MAX(id), 0) FROM gsc_date_performance").fetchone()
        next_id = max_id_result[0] + 1 if max_id_result else 1
        
        for row in rows:
            try:
                self.conn.execute("""
                    INSERT INTO gsc_date_performance (
                        id, site_url, date, clicks, impressions, ctr, position,
                        collected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    next_id,
                    row["site_url"],
                    row["date"],
                    int(row["clicks"]),
                    int(row["impressions"]),
                    float(row["ctr"]),
                    float(row["position"]),
                    collected_at,
                ])
                next_id += 1
                inserted += 1
            except Exception as e:
                print(f"  ⚠️  Erro ao inserir date row: {e}")
                continue
        
        return inserted
