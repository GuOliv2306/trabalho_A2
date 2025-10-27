"""
Módulo de limpeza e validação de dados GA4 e GSC.

Disponibiliza classes para:
- Limpeza de valores nulos e inconsistentes
- Remoção de duplicatas
- Validação de integridade
"""

from .data_cleaner import (
    DataCleaner,
    GA4DataCleaner,
    GSCDataCleaner,
    JSONCleaner,
)
from .deduplicator import DeduplicateData
from .validators import (
    DataValidator,
    GA4Validator,
    GSCValidator,
    ValidationReport,
)

__all__ = [
    # Cleaners
    "DataCleaner",
    "GA4DataCleaner",
    "GSCDataCleaner",
    "JSONCleaner",
    
    # Deduplication
    "DeduplicateData",
    
    # Validators
    "DataValidator",
    "GA4Validator",
    "GSCValidator",
    "ValidationReport",
]
