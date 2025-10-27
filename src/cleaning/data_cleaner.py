"""
Módulo de limpeza e pré-processamento de dados GA4 e GSC.

Implementa estratégias para:
- Tratamento de valores nulos
- Remoção de duplicatas
- Normalização de dados
- Validação de métricas
"""

from typing import Dict, Any, List, Optional, Literal
from datetime import datetime
import json
from pathlib import Path


class DataCleaner:
    """Classe base para limpeza de dados."""

    @staticmethod
    def fill_null_numeric(
        value: Optional[float],
        strategy: Literal["zero", "mean", "median"] = "zero",
        fallback: float = 0.0
    ) -> float:
        """
        Preenche valores nulos em métricas numéricas.

        Args:
            value: Valor original (pode ser None)
            strategy: Estratégia de preenchimento
            fallback: Valor padrão se strategy não aplicável

        Returns:
            float: Valor preenchido
        """
        if value is None:
            return fallback
        
        try:
            return float(value)
        except (ValueError, TypeError):
            return fallback

    @staticmethod
    def fill_null_string(
        value: Optional[str],
        default: str = "(not set)"
    ) -> str:
        """
        Preenche valores nulos em dimensões de texto.

        Args:
            value: Valor original (pode ser None)
            default: Valor padrão para nulos

        Returns:
            str: Valor preenchido
        """
        if value is None or value == "" or value == "null":
            return default
        return str(value)

    @staticmethod
    def validate_ctr(clicks: float, impressions: float) -> float:
        """
        Calcula CTR validado, tratando divisão por zero.

        Args:
            clicks: Número de cliques
            impressions: Número de impressões

        Returns:
            float: CTR validado (0.0 a 1.0)
        """
        if impressions == 0 or impressions is None:
            return 0.0
        
        clicks = clicks or 0.0
        ctr = clicks / impressions
        
        # Limita CTR a valores válidos (0-1)
        return max(0.0, min(1.0, ctr))

    @staticmethod
    def validate_percentage(value: Optional[float]) -> float:
        """
        Valida e normaliza percentuais (0-1).

        Args:
            value: Valor percentual

        Returns:
            float: Percentual validado (0.0 a 1.0)
        """
        if value is None:
            return 0.0
        
        try:
            value = float(value)
            return max(0.0, min(1.0, value))
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def validate_position(position: Optional[float]) -> float:
        """
        Valida posição de busca (GSC).

        Args:
            position: Posição média

        Returns:
            float: Posição validada (>= 1.0)
        """
        if position is None:
            return 100.0  # Posição padrão para nulos
        
        try:
            position = float(position)
            return max(1.0, position)  # Posição mínima é 1
        except (ValueError, TypeError):
            return 100.0


class GA4DataCleaner(DataCleaner):
    """Limpeza especializada para dados GA4."""

    @classmethod
    def clean_traffic_row(cls, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Limpa uma linha de dados de tráfego GA4.

        Args:
            row: Dicionário com dados brutos

        Returns:
            Dict: Dados limpos e validados
        """
        return {
            # Dimensões (texto)
            "property_id": cls.fill_null_string(row.get("property_id")),
            "date": row.get("date"),  # Assumido já validado
            "session_source": cls.fill_null_string(
                row.get("session_source"), "(direct)"
            ),
            "session_medium": cls.fill_null_string(
                row.get("session_medium"), "(none)"
            ),
            "session_campaign_name": cls.fill_null_string(
                row.get("session_campaign_name"), "(not set)"
            ),
            
            # Métricas (numéricas)
            "sessions": cls.fill_null_numeric(row.get("sessions"), "zero"),
            "active_users": cls.fill_null_numeric(row.get("active_users"), "zero"),
            "new_users": cls.fill_null_numeric(row.get("new_users"), "zero"),
            "screen_page_views": cls.fill_null_numeric(row.get("screen_page_views"), "zero"),
            "average_session_duration": cls.fill_null_numeric(
                row.get("average_session_duration"), "zero"
            ),
            "collected_at": row.get("collected_at", datetime.now().isoformat()),
        }

    @classmethod
    def clean_conversion_row(cls, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Limpa uma linha de dados de conversões GA4.

        Args:
            row: Dicionário com dados brutos

        Returns:
            Dict: Dados limpos e validados
        """
        return {
            # Dimensões
            "property_id": cls.fill_null_string(row.get("property_id")),
            "date": row.get("date"),
            "event_name": cls.fill_null_string(row.get("event_name"), "(not set)"),
            "session_source": cls.fill_null_string(
                row.get("session_source"), "(direct)"
            ),
            "session_medium": cls.fill_null_string(
                row.get("session_medium"), "(none)"
            ),
            
            # Métricas
            "key_events": cls.fill_null_numeric(row.get("key_events"), "zero"),
            "event_count": cls.fill_null_numeric(row.get("event_count"), "zero"),
            "total_revenue": cls.fill_null_numeric(row.get("total_revenue"), "zero"),
            "transactions": cls.fill_null_numeric(row.get("transactions"), "zero"),
            "purchase_revenue": cls.fill_null_numeric(row.get("purchase_revenue"), "zero"),
            "collected_at": row.get("collected_at", datetime.now().isoformat()),
        }

    @classmethod
    def clean_engagement_row(cls, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Limpa uma linha de dados de engajamento GA4.

        Args:
            row: Dicionário com dados brutos

        Returns:
            Dict: Dados limpos e validados
        """
        # Valida engagement_rate como percentual
        engagement_rate = cls.validate_percentage(row.get("engagement_rate"))
        
        return {
            # Dimensões
            "property_id": cls.fill_null_string(row.get("property_id")),
            "date": row.get("date"),
            "page_path": cls.fill_null_string(row.get("page_path"), "/"),
            "unified_screen_name": cls.fill_null_string(
                row.get("unified_screen_name"), "(not set)"
            ),
            "device_category": cls.fill_null_string(
                row.get("device_category"), "desktop"
            ),
            
            # Métricas
            "engagement_rate": engagement_rate,
            "engaged_sessions": cls.fill_null_numeric(row.get("engaged_sessions"), "zero"),
            "average_session_duration": cls.fill_null_numeric(
                row.get("average_session_duration"), "zero"
            ),
            "event_count": cls.fill_null_numeric(row.get("event_count"), "zero"),
            "user_engagement_duration": cls.fill_null_numeric(
                row.get("user_engagement_duration"), "zero"
            ),
            "collected_at": row.get("collected_at", datetime.now().isoformat()),
        }

    @classmethod
    def clean_realtime_row(cls, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Limpa uma linha de dados realtime GA4.

        Args:
            row: Dicionário com dados brutos

        Returns:
            Dict: Dados limpos e validados
        """
        return {
            # Dimensões
            "property_id": cls.fill_null_string(row.get("property_id")),
            "unified_screen_name": cls.fill_null_string(
                row.get("unified_screen_name"), "(not set)"
            ),
            "country": cls.fill_null_string(row.get("country"), "(not set)"),
            "city": cls.fill_null_string(row.get("city"), "(not set)"),
            
            # Métricas
            "active_users": cls.fill_null_numeric(row.get("active_users"), "zero"),
            "screen_page_views": cls.fill_null_numeric(row.get("screen_page_views"), "zero"),
            "collected_at": row.get("collected_at", datetime.now().isoformat()),
        }


class GSCDataCleaner(DataCleaner):
    """Limpeza especializada para dados Google Search Console."""

    @classmethod
    def clean_query_row(cls, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Limpa uma linha de performance de query (GSC).

        Args:
            row: Dicionário com dados brutos

        Returns:
            Dict: Dados limpos e validados
        """
        clicks = cls.fill_null_numeric(row.get("clicks"), "zero")
        impressions = cls.fill_null_numeric(row.get("impressions"), "zero")
        
        # Recalcula CTR se necessário
        ctr_original = row.get("ctr")
        if ctr_original is None and impressions > 0:
            ctr = cls.validate_ctr(clicks, impressions)
        else:
            ctr = cls.validate_percentage(ctr_original)
        
        return {
            # Dimensões
            "site_url": cls.fill_null_string(row.get("site_url")),
            "query": cls.fill_null_string(row.get("query"), "(not provided)"),
            "start_date": row.get("start_date"),
            "end_date": row.get("end_date"),
            
            # Métricas
            "clicks": clicks,
            "impressions": impressions,
            "ctr": ctr,
            "position": cls.validate_position(row.get("position")),
            "collected_at": row.get("collected_at", datetime.now().isoformat()),
        }

    @classmethod
    def clean_page_row(cls, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Limpa uma linha de performance de página (GSC).

        Args:
            row: Dicionário com dados brutos

        Returns:
            Dict: Dados limpos e validados
        """
        clicks = cls.fill_null_numeric(row.get("clicks"), "zero")
        impressions = cls.fill_null_numeric(row.get("impressions"), "zero")
        
        ctr_original = row.get("ctr")
        if ctr_original is None and impressions > 0:
            ctr = cls.validate_ctr(clicks, impressions)
        else:
            ctr = cls.validate_percentage(ctr_original)
        
        return {
            # Dimensões
            "site_url": cls.fill_null_string(row.get("site_url")),
            "page": cls.fill_null_string(row.get("page"), "/"),
            "start_date": row.get("start_date"),
            "end_date": row.get("end_date"),
            
            # Métricas
            "clicks": clicks,
            "impressions": impressions,
            "ctr": ctr,
            "position": cls.validate_position(row.get("position")),
            "collected_at": row.get("collected_at", datetime.now().isoformat()),
        }

    @classmethod
    def clean_country_row(cls, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Limpa uma linha de performance por país (GSC).

        Args:
            row: Dicionário com dados brutos

        Returns:
            Dict: Dados limpos e validados
        """
        clicks = cls.fill_null_numeric(row.get("clicks"), "zero")
        impressions = cls.fill_null_numeric(row.get("impressions"), "zero")
        
        ctr_original = row.get("ctr")
        if ctr_original is None and impressions > 0:
            ctr = cls.validate_ctr(clicks, impressions)
        else:
            ctr = cls.validate_percentage(ctr_original)
        
        return {
            # Dimensões
            "site_url": cls.fill_null_string(row.get("site_url")),
            "country": cls.fill_null_string(row.get("country"), "(not set)"),
            "start_date": row.get("start_date"),
            "end_date": row.get("end_date"),
            
            # Métricas
            "clicks": clicks,
            "impressions": impressions,
            "ctr": ctr,
            "position": cls.validate_position(row.get("position")),
            "collected_at": row.get("collected_at", datetime.now().isoformat()),
        }

    @classmethod
    def clean_device_row(cls, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Limpa uma linha de performance por dispositivo (GSC).

        Args:
            row: Dicionário com dados brutos

        Returns:
            Dict: Dados limpos e validados
        """
        clicks = cls.fill_null_numeric(row.get("clicks"), "zero")
        impressions = cls.fill_null_numeric(row.get("impressions"), "zero")
        
        ctr_original = row.get("ctr")
        if ctr_original is None and impressions > 0:
            ctr = cls.validate_ctr(clicks, impressions)
        else:
            ctr = cls.validate_percentage(ctr_original)
        
        # Normaliza device
        device = cls.fill_null_string(row.get("device"), "DESKTOP").upper()
        if device not in ["DESKTOP", "MOBILE", "TABLET"]:
            device = "DESKTOP"
        
        return {
            # Dimensões
            "site_url": cls.fill_null_string(row.get("site_url")),
            "device": device,
            "start_date": row.get("start_date"),
            "end_date": row.get("end_date"),
            
            # Métricas
            "clicks": clicks,
            "impressions": impressions,
            "ctr": ctr,
            "position": cls.validate_position(row.get("position")),
            "collected_at": row.get("collected_at", datetime.now().isoformat()),
        }

    @classmethod
    def clean_date_row(cls, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Limpa uma linha de série temporal (GSC).

        Args:
            row: Dicionário com dados brutos

        Returns:
            Dict: Dados limpos e validados
        """
        clicks = cls.fill_null_numeric(row.get("clicks"), "zero")
        impressions = cls.fill_null_numeric(row.get("impressions"), "zero")
        
        ctr_original = row.get("ctr")
        if ctr_original is None and impressions > 0:
            ctr = cls.validate_ctr(clicks, impressions)
        else:
            ctr = cls.validate_percentage(ctr_original)
        
        return {
            # Dimensões
            "site_url": cls.fill_null_string(row.get("site_url")),
            "date": row.get("date"),
            
            # Métricas
            "clicks": clicks,
            "impressions": impressions,
            "ctr": ctr,
            "position": cls.validate_position(row.get("position")),
            "collected_at": row.get("collected_at", datetime.now().isoformat()),
        }

    @classmethod
    def clean_query_page_row(cls, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Limpa uma linha de query+page (GSC).

        Args:
            row: Dicionário com dados brutos

        Returns:
            Dict: Dados limpos e validados
        """
        clicks = cls.fill_null_numeric(row.get("clicks"), "zero")
        impressions = cls.fill_null_numeric(row.get("impressions"), "zero")
        
        ctr_original = row.get("ctr")
        if ctr_original is None and impressions > 0:
            ctr = cls.validate_ctr(clicks, impressions)
        else:
            ctr = cls.validate_percentage(ctr_original)
        
        return {
            # Dimensões
            "site_url": cls.fill_null_string(row.get("site_url")),
            "query": cls.fill_null_string(row.get("query"), "(not provided)"),
            "page": cls.fill_null_string(row.get("page"), "/"),
            "start_date": row.get("start_date"),
            "end_date": row.get("end_date"),
            
            # Métricas
            "clicks": clicks,
            "impressions": impressions,
            "ctr": ctr,
            "position": cls.validate_position(row.get("position")),
            "collected_at": row.get("collected_at", datetime.now().isoformat()),
        }


class JSONCleaner:
    """Limpa arquivos JSON antes de inserção no banco."""

    @staticmethod
    def clean_json_file(
        input_path: str,
        output_path: Optional[str] = None,
        source: Literal["ga4", "gsc"] = "ga4"
    ) -> Dict[str, Any]:
        """
        Limpa arquivo JSON completo.

        Args:
            input_path: Caminho do arquivo JSON original
            output_path: Caminho para salvar JSON limpo (opcional)
            source: Fonte dos dados ("ga4" ou "gsc")

        Returns:
            Dict: Dados limpos
        """
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Determina tipo de report
        report_type = data.get("report_type", "")
        
        # Limpa rows com base no tipo
        if "rows" in data and isinstance(data["rows"], list):
            cleaned_rows = []
            
            for row in data["rows"]:
                if source == "ga4":
                    cleaned_row = JSONCleaner._clean_ga4_row(row, report_type)
                else:  # gsc
                    cleaned_row = JSONCleaner._clean_gsc_row(row, report_type)
                
                cleaned_rows.append(cleaned_row)
            
            data["rows"] = cleaned_rows
        
        # Salva se output_path fornecido
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        return data

    @staticmethod
    def _clean_ga4_row(row: Dict[str, Any], report_type: str) -> Dict[str, Any]:
        """Limpa row GA4 com base no tipo."""
        if report_type == "traffic":
            return GA4DataCleaner.clean_traffic_row(row)
        elif report_type == "conversions":
            return GA4DataCleaner.clean_conversion_row(row)
        elif report_type == "engagement":
            return GA4DataCleaner.clean_engagement_row(row)
        elif report_type == "realtime_traffic":
            return GA4DataCleaner.clean_realtime_row(row)
        else:
            return row

    @staticmethod
    def _clean_gsc_row(row: Dict[str, Any], report_type: str) -> Dict[str, Any]:
        """Limpa row GSC com base no tipo."""
        if report_type == "query_performance":
            return GSCDataCleaner.clean_query_row(row)
        elif report_type == "page_performance":
            return GSCDataCleaner.clean_page_row(row)
        elif report_type == "country_performance":
            return GSCDataCleaner.clean_country_row(row)
        elif report_type == "device_performance":
            return GSCDataCleaner.clean_device_row(row)
        elif report_type == "date_performance":
            return GSCDataCleaner.clean_date_row(row)
        elif report_type == "query_page_performance":
            return GSCDataCleaner.clean_query_page_row(row)
        else:
            return row
