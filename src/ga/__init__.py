"""
Módulo Google Analytics 4.

Implementa coleta de dados usando google-analytics-data API oficial.
"""

from .ga_client import GA4Client
from .collectors import GA4DataCollector

__all__ = ["GA4Client", "GA4DataCollector"]