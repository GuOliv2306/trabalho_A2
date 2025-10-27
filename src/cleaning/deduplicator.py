"""
Utilitários para detecção e remoção de duplicatas.

Implementa estratégias para identificar e remover registros duplicados
em dados GA4 e GSC, mantendo a versão mais recente ou completa.
"""

from typing import List, Dict, Any, Set, Tuple
from datetime import datetime


class DeduplicateData:
    """Remove duplicatas de datasets GA4 e GSC."""

    @staticmethod
    def deduplicate_ga4_traffic(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicatas de dados de tráfego GA4.

        Chave única: (property_id, date, session_source, session_medium, session_campaign_name)
        Estratégia: Mantém registro com collected_at mais recente

        Args:
            rows: Lista de registros de tráfego

        Returns:
            List: Registros únicos
        """
        seen: Dict[Tuple, Dict[str, Any]] = {}
        
        for row in rows:
            key = (
                row.get("property_id"),
                row.get("date"),
                row.get("session_source"),
                row.get("session_medium"),
                row.get("session_campaign_name"),
            )
            
            # Se já existe, compara collected_at
            if key in seen:
                existing_time = seen[key].get("collected_at", "")
                new_time = row.get("collected_at", "")
                
                # Mantém o mais recente
                if new_time > existing_time:
                    seen[key] = row
            else:
                seen[key] = row
        
        return list(seen.values())

    @staticmethod
    def deduplicate_ga4_conversions(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicatas de dados de conversões GA4.

        Chave única: (property_id, date, event_name, session_source, session_medium)

        Args:
            rows: Lista de registros de conversões

        Returns:
            List: Registros únicos
        """
        seen: Dict[Tuple, Dict[str, Any]] = {}
        
        for row in rows:
            key = (
                row.get("property_id"),
                row.get("date"),
                row.get("event_name"),
                row.get("session_source"),
                row.get("session_medium"),
            )
            
            if key in seen:
                existing_time = seen[key].get("collected_at", "")
                new_time = row.get("collected_at", "")
                
                if new_time > existing_time:
                    seen[key] = row
            else:
                seen[key] = row
        
        return list(seen.values())

    @staticmethod
    def deduplicate_ga4_engagement(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicatas de dados de engajamento GA4.

        Chave única: (property_id, date, page_path, unified_screen_name, device_category)

        Args:
            rows: Lista de registros de engajamento

        Returns:
            List: Registros únicos
        """
        seen: Dict[Tuple, Dict[str, Any]] = {}
        
        for row in rows:
            key = (
                row.get("property_id"),
                row.get("date"),
                row.get("page_path"),
                row.get("unified_screen_name"),
                row.get("device_category"),
            )
            
            if key in seen:
                existing_time = seen[key].get("collected_at", "")
                new_time = row.get("collected_at", "")
                
                if new_time > existing_time:
                    seen[key] = row
            else:
                seen[key] = row
        
        return list(seen.values())

    @staticmethod
    def deduplicate_gsc_query(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicatas de performance de queries GSC.

        Chave única: (site_url, query, start_date, end_date)

        Args:
            rows: Lista de registros de queries

        Returns:
            List: Registros únicos
        """
        seen: Dict[Tuple, Dict[str, Any]] = {}
        
        for row in rows:
            key = (
                row.get("site_url"),
                row.get("query"),
                row.get("start_date"),
                row.get("end_date"),
            )
            
            if key in seen:
                existing_time = seen[key].get("collected_at", "")
                new_time = row.get("collected_at", "")
                
                if new_time > existing_time:
                    seen[key] = row
            else:
                seen[key] = row
        
        return list(seen.values())

    @staticmethod
    def deduplicate_gsc_page(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicatas de performance de páginas GSC.

        Chave única: (site_url, page, start_date, end_date)

        Args:
            rows: Lista de registros de páginas

        Returns:
            List: Registros únicos
        """
        seen: Dict[Tuple, Dict[str, Any]] = {}
        
        for row in rows:
            key = (
                row.get("site_url"),
                row.get("page"),
                row.get("start_date"),
                row.get("end_date"),
            )
            
            if key in seen:
                existing_time = seen[key].get("collected_at", "")
                new_time = row.get("collected_at", "")
                
                if new_time > existing_time:
                    seen[key] = row
            else:
                seen[key] = row
        
        return list(seen.values())

    @staticmethod
    def deduplicate_gsc_country(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicatas de performance por país GSC.

        Chave única: (site_url, country, start_date, end_date)

        Args:
            rows: Lista de registros de países

        Returns:
            List: Registros únicos
        """
        seen: Dict[Tuple, Dict[str, Any]] = {}
        
        for row in rows:
            key = (
                row.get("site_url"),
                row.get("country"),
                row.get("start_date"),
                row.get("end_date"),
            )
            
            if key in seen:
                existing_time = seen[key].get("collected_at", "")
                new_time = row.get("collected_at", "")
                
                if new_time > existing_time:
                    seen[key] = row
            else:
                seen[key] = row
        
        return list(seen.values())

    @staticmethod
    def deduplicate_gsc_device(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicatas de performance por dispositivo GSC.

        Chave única: (site_url, device, start_date, end_date)

        Args:
            rows: Lista de registros de dispositivos

        Returns:
            List: Registros únicos
        """
        seen: Dict[Tuple, Dict[str, Any]] = {}
        
        for row in rows:
            key = (
                row.get("site_url"),
                row.get("device"),
                row.get("start_date"),
                row.get("end_date"),
            )
            
            if key in seen:
                existing_time = seen[key].get("collected_at", "")
                new_time = row.get("collected_at", "")
                
                if new_time > existing_time:
                    seen[key] = row
            else:
                seen[key] = row
        
        return list(seen.values())

    @staticmethod
    def deduplicate_gsc_date(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicatas de série temporal GSC.

        Chave única: (site_url, date)

        Args:
            rows: Lista de registros temporais

        Returns:
            List: Registros únicos
        """
        seen: Dict[Tuple, Dict[str, Any]] = {}
        
        for row in rows:
            key = (
                row.get("site_url"),
                row.get("date"),
            )
            
            if key in seen:
                existing_time = seen[key].get("collected_at", "")
                new_time = row.get("collected_at", "")
                
                if new_time > existing_time:
                    seen[key] = row
            else:
                seen[key] = row
        
        return list(seen.values())

    @staticmethod
    def deduplicate_gsc_query_page(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicatas de query+page GSC.

        Chave única: (site_url, query, page, start_date, end_date)

        Args:
            rows: Lista de registros query+page

        Returns:
            List: Registros únicos
        """
        seen: Dict[Tuple, Dict[str, Any]] = {}
        
        for row in rows:
            key = (
                row.get("site_url"),
                row.get("query"),
                row.get("page"),
                row.get("start_date"),
                row.get("end_date"),
            )
            
            if key in seen:
                existing_time = seen[key].get("collected_at", "")
                new_time = row.get("collected_at", "")
                
                if new_time > existing_time:
                    seen[key] = row
            else:
                seen[key] = row
        
        return list(seen.values())

    @staticmethod
    def find_duplicates_report(rows: List[Dict[str, Any]], key_fields: List[str]) -> Dict[str, Any]:
        """
        Gera relatório de duplicatas encontradas.

        Args:
            rows: Lista de registros
            key_fields: Campos que formam chave única

        Returns:
            Dict: Relatório com contagens e exemplos
        """
        seen_keys: Dict[Tuple, int] = {}
        duplicates_examples: List[Dict[str, Any]] = []
        
        for row in rows:
            key = tuple(row.get(field) for field in key_fields)
            
            if key in seen_keys:
                seen_keys[key] += 1
                
                # Guarda exemplo (até 10)
                if len(duplicates_examples) < 10:
                    duplicates_examples.append({
                        "key": dict(zip(key_fields, key)),
                        "count": seen_keys[key] + 1
                    })
            else:
                seen_keys[key] = 1
        
        # Conta duplicatas
        duplicate_count = sum(1 for count in seen_keys.values() if count > 1)
        total_duplicate_rows = sum(count - 1 for count in seen_keys.values() if count > 1)
        
        return {
            "total_rows": len(rows),
            "unique_keys": len(seen_keys),
            "duplicate_keys": duplicate_count,
            "duplicate_rows_count": total_duplicate_rows,
            "examples": duplicates_examples[:5],  # Top 5 exemplos
        }
