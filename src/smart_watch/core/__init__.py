# Modules centraux de SmartWatch.
# Documentation : https://datagora-erasme.github.io/smart_watch/source/modules/core/index.html

from .ComparateurHoraires import (
    ComparisonResult,
    HorairesComparator,
    ScheduleNormalizer,
)
from .ConfigManager import ConfigManager
from .DatabaseManager import DatabaseManager
from .EnvoyerMail import EmailSender
from .ErrorHandler import (
    ErrorCategory,
    ErrorContext,
    ErrorHandler,
    ErrorSeverity,
    HandledError,
    get_error_handler,
    handle_errors,
)
from .GetPrompt import get_prompt
from .LLMClient import (
    BaseLLMClient,
    LLMMessage,
    LLMResponse,
    MistralAPIClient,
    OpenAICompatibleClient,
    get_mistral_tool_format,
    get_structured_response_format,
)
from .Logger import LogLevel, LogOutput, SmartWatchLogger, create_logger
from .NotificationManager import NotificationManager
from .StatsManager import StatItem, StatsManager, StatsSection
from .URLRetriever import retrieve_url

__all__ = [
    # ComparateurHoraires
    "ComparisonResult",
    "HorairesComparator",
    "ScheduleNormalizer",
    # ConfigManager
    "ConfigManager",
    # DatabaseManager
    "DatabaseManager",
    # EnvoyerMail
    "EmailSender",
    # ErrorHandler
    "ErrorCategory",
    "ErrorContext",
    "ErrorHandler",
    "ErrorSeverity",
    "HandledError",
    "get_error_handler",
    "handle_errors",
    # GetPrompt
    "get_prompt",
    # LLMClient
    "BaseLLMClient",
    "LLMMessage",
    "LLMResponse",
    "MistralAPIClient",
    "OpenAICompatibleClient",
    "get_mistral_tool_format",
    "get_structured_response_format",
    # Logger
    "LogLevel",
    "LogOutput",
    "SmartWatchLogger",
    "create_logger",
    # NotificationManager
    "NotificationManager",
    # StatsManager
    "StatItem",
    "StatsManager",
    "StatsSection",
    # URLRetriever
    "retrieve_url",
]
