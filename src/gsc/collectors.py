"""
Funções especializadas para coletar dados do Google Search Console.

Implementa métodos prontos para coleta de queries, páginas, países e dispositivos.

⚠️ CONEXÃO COM GSC REMOVIDA - AGUARDANDO DADOS SIMULADOS
Este módulo dependia do GSCClient que foi desabilitado.
Adapte para usar dados simulados no futuro.
"""

from typing import Dict, Any, Optional, List
# ⚠️ IMPORT DESABILITADO - GSCClient não funciona mais
# from .gsc_client import GSCClient


class GSCDataCollector:
    """
    Coletor especializado de dados do Google Search Console.
    
    ⚠️ ATENÇÃO: Classe desabilitada - requer adaptação para dados simulados!
    """

    def __init__(self, site_url: str, credentials_path: Optional[str] = None):
        """
        ⚠️ DESABILITADO - Aguardando dados simulados.
        """
        # ⚠️ Linha abaixo causaria erro pois GSCClient está desabilitado
        # self.client = GSCClient(site_url, credentials_path)
        
        raise NotImplementedError(
            "⚠️ GSCDataCollector desabilitado. "
            "Implemente um simulador de dados antes de usar esta classe."
        )

    # ⚠️ MÉTODOS ABAIXO DESABILITADOS - Requeriam GSCClient funcional
    # Descomentar e adaptar quando implementar simulador
    
    # def collect_query_performance(...):
    #     """Coleta performance de queries - DESABILITADO"""
    #     pass
    
    # def collect_page_performance(...):
    #     """Coleta performance de páginas - DESABILITADO"""
    #     pass
    
    # def collect_country_performance(...):
    #     """Coleta performance por país - DESABILITADO"""
    #     pass
    
    # def collect_device_performance(...):
    #     """Coleta performance por dispositivo - DESABILITADO"""
    #     pass
    
    # def collect_date_series(...):
    #     """Coleta série temporal - DESABILITADO"""
    #     pass

# ⚠️ TODO CÓDIGO ABAIXO FOI COMENTADO - Era implementação real de coleta GSC
# Descomentar e adaptar quando implementar o simulador de dados
