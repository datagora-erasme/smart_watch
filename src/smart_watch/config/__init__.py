# Package de configuration modulaire pour SmartWatch.
# Documentation : https://datagora-erasme.github.io/smart_watch/source/modules/config/index.html

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
