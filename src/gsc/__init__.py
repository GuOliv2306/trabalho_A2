"""
Módulo Google Search Console.

Implementa coleta de dados usando Google Search Console API oficial.
"""

from .gsc_client import GSCClient
from .collectors import GSCDataCollector

__all__ = ["GSCClient", "GSCDataCollector"]
