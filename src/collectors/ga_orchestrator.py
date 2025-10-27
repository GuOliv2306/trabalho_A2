"""
Orchestrator para coleta de dados do Google Analytics 4.

Coordena a coleta, armazenamento em JSON local e preparação para banco de dados.

⚠️ CONEXÃO COM GA4 REMOVIDA - AGUARDANDO DADOS SIMULADOS
Este orquestrador dependia do GA4DataCollector que foi desabilitado.
Adapte para usar dados simulados no futuro.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# ⚠️ IMPORT DESABILITADO - GA4DataCollector não funciona mais
# from ..ga.collectors import GA4DataCollector


class GA4Orchestrator:
    """
    Orquestra processo completo de coleta de dados GA4.
    
    ⚠️ ATENÇÃO: Classe desabilitada - requer adaptação para dados simulados!
    """

    def __init__(
        self,
        property_id: str,
        credentials_path: Optional[str] = None,
        output_dir: str = "data/raw",
    ):
        """
        ⚠️ DESABILITADO - Aguardando dados simulados.
        """
        # ⚠️ CONEXÃO DESABILITADA
        # self.collector = GA4DataCollector(property_id, credentials_path)
        # self.output_dir = Path(output_dir)
        # self.output_dir.mkdir(parents=True, exist_ok=True)
        
        raise NotImplementedError(
            "⚠️ GA4Orchestrator desabilitado. "
            "Implemente um simulador de dados antes de usar esta classe."
        )

    # ⚠️ MÉTODOS DESABILITADOS - Requeriam GA4DataCollector funcional
    # Descomentar e adaptar quando implementar simulador
    
    # def collect_and_save(...):
    #     """Coleta dados e salva em JSONs - DESABILITADO"""
    #     pass

# ⚠️ TODO CÓDIGO ABAIXO FOI COMENTADO - Era implementação real do orchestrator GA4
# Descomentar e adaptar quando implementar o simulador de dados
