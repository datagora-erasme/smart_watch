"""
Module de traitement pour l'extraction d'horaires.
Contient les processeurs modulaires pour chaque étape du pipeline.
"""

from .comparison_processor import ComparisonProcessor
from .database_processor import DatabaseProcessor
from .llm_processor import LLMProcessor
from .markdown_processor import MarkdownProcessor
from .setup_processor import SetupProcessor
from .url_processor import URLProcessor

__all__ = [
    "SetupProcessor",
    "DatabaseProcessor",
    "URLProcessor",
    "MarkdownProcessor",
    "LLMProcessor",
    "ComparisonProcessor",
]
