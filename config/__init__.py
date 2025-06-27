"""
Package de configuration modulaire pour smart_watch.
"""

from .database_config import DatabaseConfig
from .email_config import EmailConfig
from .llm_config import LLMConfig
from .markdown_filtering_config import MarkdownFilteringConfig
from .processing_config import ProcessingConfig

__all__ = [
    "LLMConfig",
    "DatabaseConfig",
    "EmailConfig",
    "ProcessingConfig",
    "MarkdownFilteringConfig",
]
