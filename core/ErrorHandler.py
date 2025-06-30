"""
Gestionnaire d'erreurs centralisé pour le projet smart_watch.
Standardise la gestion des erreurs, la journalisation et les notifications.
"""

import traceback
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from core.Logger import LogLevel, create_logger


class ErrorSeverity(Enum):
    """Niveaux de gravité des erreurs."""

    LOW = "low"  # Erreur mineure, traitement continue
    MEDIUM = "medium"  # Erreur modérée, traitement peut continuer avec dégradation
    HIGH = "high"  # Erreur grave, arrêt du traitement recommandé
    CRITICAL = "critical"  # Erreur critique, arrêt immédiat requis


class ErrorCategory(Enum):
    """Catégories d'erreurs pour classification."""

    CONFIGURATION = "configuration"
    DATABASE = "database"
    NETWORK = "network"
    LLM = "llm"
    FILE_IO = "file_io"
    VALIDATION = "validation"
    CONVERSION = "conversion"
    EMAIL = "email"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """Contexte d'une erreur pour enrichir les informations."""

    module: str
    function: str
    operation: str
    data: Optional[Dict[str, Any]] = None
    user_message: Optional[str] = None


@dataclass
class HandledError:
    """Représente une erreur traitée par le gestionnaire."""

    category: ErrorCategory
    severity: ErrorSeverity
    exception: Exception
    context: ErrorContext
    timestamp: str
    traceback: str
    resolved: bool = False
    solution_attempted: Optional[str] = None


class ErrorHandler:
    """Gestionnaire centralisé des erreurs."""

    def __init__(self, log_file: Optional[Path] = None):
        """
        Initialise le gestionnaire d'erreurs.

        Args:
            log_file: Fichier de log (optionnel)
        """
        self.logger = create_logger(
            module_name="ErrorHandler",
        )

        # Registre des erreurs traitées
        self.error_registry: List[HandledError] = []

        # Mapping des exceptions vers les catégories
        self.exception_mapping = {
            # Configuration
            ValueError: ErrorCategory.CONFIGURATION,
            KeyError: ErrorCategory.CONFIGURATION,
            AttributeError: ErrorCategory.CONFIGURATION,
            # Base de données
            Exception: ErrorCategory.DATABASE,  # Sera affiné par le nom du module
            # Réseau
            ConnectionError: ErrorCategory.NETWORK,
            TimeoutError: ErrorCategory.NETWORK,
            # Fichiers
            FileNotFoundError: ErrorCategory.FILE_IO,
            PermissionError: ErrorCategory.FILE_IO,
            OSError: ErrorCategory.FILE_IO,
        }

        # Gestionnaires spécialisés par catégorie
        self.category_handlers = {
            ErrorCategory.CONFIGURATION: self._handle_configuration_error,
            ErrorCategory.DATABASE: self._handle_database_error,
            ErrorCategory.NETWORK: self._handle_network_error,
            ErrorCategory.LLM: self._handle_llm_error,
            ErrorCategory.FILE_IO: self._handle_file_io_error,
            ErrorCategory.VALIDATION: self._handle_validation_error,
            ErrorCategory.EMAIL: self._handle_email_error,
        }

    def handle_error(
        self,
        exception: Exception,
        context: ErrorContext,
        severity: Optional[ErrorSeverity] = None,
        category: Optional[ErrorCategory] = None,
        reraise: bool = False,
        default_return: Any = None,
    ) -> Any:
        """
        Traite une erreur de manière centralisée.

        Args:
            exception: L'exception à traiter
            context: Contexte de l'erreur
            severity: Gravité de l'erreur (auto-déterminée si None)
            category: Catégorie de l'erreur (auto-déterminée si None)
            reraise: Si True, relance l'exception après traitement
            default_return: Valeur de retour par défaut

        Returns:
            default_return ou résultat du gestionnaire spécialisé

        Raises:
            Exception: Si reraise=True
        """
        import datetime

        # Auto-détermination de la catégorie
        if category is None:
            category = self._determine_category(exception, context)

        # Auto-détermination de la gravité
        if severity is None:
            severity = self._determine_severity(exception, context, category)

        # Création de l'erreur traitée
        handled_error = HandledError(
            category=category,
            severity=severity,
            exception=exception,
            context=context,
            timestamp=datetime.datetime.now().isoformat(),
            traceback=traceback.format_exc(),
        )

        # Enregistrement de l'erreur
        self.error_registry.append(handled_error)

        # Logging selon la gravité
        self._log_error(handled_error)

        # Traitement spécialisé
        result = self._apply_specialized_handling(handled_error)

        # Relancer si demandé
        if reraise:
            raise exception

        return result if result is not None else default_return

    def _determine_category(
        self, exception: Exception, context: ErrorContext
    ) -> ErrorCategory:
        """Détermine automatiquement la catégorie de l'erreur."""

        # Mapping basé sur le type d'exception
        exc_type = type(exception)
        if exc_type in self.exception_mapping:
            base_category = self.exception_mapping[exc_type]
        else:
            base_category = ErrorCategory.UNKNOWN

        # Affinement basé sur le contexte
        module_name = context.module.lower()

        if "llm" in module_name or "llm" in context.operation.lower():
            return ErrorCategory.LLM
        elif "database" in module_name or "db" in module_name:
            return ErrorCategory.DATABASE
        elif "mail" in module_name or "email" in module_name:
            return ErrorCategory.EMAIL
        elif "url" in module_name or "network" in module_name:
            return ErrorCategory.NETWORK
        elif "config" in module_name:
            return ErrorCategory.CONFIGURATION
        elif "convert" in module_name or "osm" in module_name:
            return ErrorCategory.CONVERSION

        return base_category

    def _determine_severity(
        self, exception: Exception, context: ErrorContext, category: ErrorCategory
    ) -> ErrorSeverity:
        """Détermine automatiquement la gravité de l'erreur."""

        # Erreurs critiques par type
        critical_exceptions = (
            FileNotFoundError,  # Fichiers de configuration manquants
            PermissionError,  # Problèmes d'accès
        )

        if isinstance(exception, critical_exceptions):
            return ErrorSeverity.CRITICAL

        # Gravité par catégorie
        severity_mapping = {
            ErrorCategory.CONFIGURATION: ErrorSeverity.HIGH,
            ErrorCategory.DATABASE: ErrorSeverity.HIGH,
            ErrorCategory.LLM: ErrorSeverity.MEDIUM,
            ErrorCategory.NETWORK: ErrorSeverity.MEDIUM,
            ErrorCategory.EMAIL: ErrorSeverity.LOW,
            ErrorCategory.FILE_IO: ErrorSeverity.MEDIUM,
            ErrorCategory.VALIDATION: ErrorSeverity.MEDIUM,
            ErrorCategory.CONVERSION: ErrorSeverity.LOW,
        }

        return severity_mapping.get(category, ErrorSeverity.MEDIUM)

    def _log_error(self, handled_error: HandledError):
        """Journalise l'erreur selon sa gravité."""

        # Message de base
        base_message = (
            f"[{handled_error.category.value.upper()}] "
            f"{handled_error.context.module}.{handled_error.context.function}: "
            f"{handled_error.context.operation}"
        )

        # Message d'erreur
        error_message = f"{base_message} - {str(handled_error.exception)}"

        # Message utilisateur si disponible
        if handled_error.context.user_message:
            error_message += f" ({handled_error.context.user_message})"

        # Données contextuelles
        if handled_error.context.data:
            error_message += f" | Data: {handled_error.context.data}"

        # Mapping gravité -> niveau de log
        log_level_mapping = {
            ErrorSeverity.LOW: LogLevel.WARNING,
            ErrorSeverity.MEDIUM: LogLevel.ERROR,
            ErrorSeverity.HIGH: LogLevel.ERROR,
            ErrorSeverity.CRITICAL: LogLevel.CRITICAL,
        }

        log_level = log_level_mapping[handled_error.severity]
        self.logger.log(log_level, error_message)

        # Traceback pour les erreurs graves
        if handled_error.severity in (ErrorSeverity.HIGH, ErrorSeverity.CRITICAL):
            self.logger.debug(f"Traceback: {handled_error.traceback}")

    def _apply_specialized_handling(self, handled_error: HandledError) -> Any:
        """Applique un traitement spécialisé selon la catégorie."""

        handler = self.category_handlers.get(handled_error.category)
        if handler:
            try:
                return handler(handled_error)
            except Exception as e:
                self.logger.error(f"Erreur dans le gestionnaire spécialisé: {e}")

        return None

    def _handle_configuration_error(self, error: HandledError) -> Any:
        """Traite les erreurs de configuration."""

        if isinstance(error.exception, KeyError):
            missing_key = str(error.exception).strip("'\"")
            error.solution_attempted = f"Variable manquante: {missing_key}"

            # Suggestions de solutions
            config_suggestions = {
                "API_KEY_OPENAI": "Ajoutez votre clé API OpenAI dans le fichier .env",
                "API_KEY_MISTRAL": "Ajoutez votre clé API Mistral dans le fichier .env",
                "DB_FILE": "Vérifiez le chemin de la base de données",
            }

            if missing_key in config_suggestions:
                self.logger.info(
                    f"Solution suggérée: {config_suggestions[missing_key]}"
                )

        elif isinstance(error.exception, ValueError):
            error.solution_attempted = "Valeur de configuration invalide"

        return None

    def _handle_database_error(self, error: HandledError) -> Any:
        """Traite les erreurs de base de données."""

        if "no such table" in str(error.exception).lower():
            error.solution_attempted = "Table manquante - initialisation requise"
            self.logger.info(
                "Solution: Exécutez l'initialisation de la base de données"
            )

        elif "database is locked" in str(error.exception).lower():
            error.solution_attempted = "Base de données verrouillée"
            self.logger.info("Solution: Fermez les autres connexions à la base")

        return None

    def _handle_network_error(self, error: HandledError) -> Any:
        """Traite les erreurs réseau."""

        if isinstance(error.exception, ConnectionError):
            error.solution_attempted = "Problème de connexion réseau"
            self.logger.info("Solution: Vérifiez votre connexion internet")

        elif isinstance(error.exception, TimeoutError):
            error.solution_attempted = "Timeout réseau"
            self.logger.info("Solution: Augmentez le timeout ou réessayez plus tard")

        return None

    def _handle_llm_error(self, error: HandledError) -> Any:
        """Traite les erreurs LLM."""

        error_str = str(error.exception).lower()

        if "api key" in error_str:
            error.solution_attempted = "Clé API invalide"
            self.logger.info("Solution: Vérifiez votre clé API LLM")

        elif "rate limit" in error_str:
            error.solution_attempted = "Limite de taux atteinte"
            self.logger.info("Solution: Attendez avant de réessayer")

        elif "timeout" in error_str:
            error.solution_attempted = "Timeout LLM"
            return "Erreur Timeout LLM"  # Valeur de retour pour continuer

        return None

    def _handle_file_io_error(self, error: HandledError) -> Any:
        """Traite les erreurs de fichiers."""

        if isinstance(error.exception, FileNotFoundError):
            missing_file = getattr(error.exception, "filename", "fichier inconnu")
            error.solution_attempted = f"Fichier manquant: {missing_file}"

        elif isinstance(error.exception, PermissionError):
            error.solution_attempted = "Permissions insuffisantes"

        return None

    def _handle_validation_error(self, error: HandledError) -> Any:
        """Traite les erreurs de validation."""

        error.solution_attempted = "Données invalides"
        return {"error": "Validation failed", "details": str(error.exception)}

    def _handle_email_error(self, error: HandledError) -> Any:
        """Traite les erreurs d'email."""

        error_str = str(error.exception).lower()

        if "authentication" in error_str:
            error.solution_attempted = "Erreur d'authentification email"

        elif "connection" in error_str:
            error.solution_attempted = "Erreur de connexion SMTP"

        return None

    def create_error_context(
        self,
        module: str,
        function: str,
        operation: str,
        data: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
    ) -> ErrorContext:
        """Créé un contexte d'erreur."""

        return ErrorContext(
            module=module,
            function=function,
            operation=operation,
            data=data,
            user_message=user_message,
        )

    def get_error_summary(self) -> Dict[str, Any]:
        """Retourne un résumé des erreurs traitées."""

        if not self.error_registry:
            return {"total_errors": 0, "by_category": {}, "by_severity": {}}

        # Comptage par catégorie
        by_category = {}
        for error in self.error_registry:
            category = error.category.value
            by_category[category] = by_category.get(category, 0) + 1

        # Comptage par gravité
        by_severity = {}
        for error in self.error_registry:
            severity = error.severity.value
            by_severity[severity] = by_severity.get(severity, 0) + 1

        return {
            "total_errors": len(self.error_registry),
            "by_category": by_category,
            "by_severity": by_severity,
            "recent_errors": [
                {
                    "category": e.category.value,
                    "severity": e.severity.value,
                    "exception": str(e.exception),
                    "module": e.context.module,
                    "timestamp": e.timestamp,
                }
                for e in self.error_registry[-5:]  # 5 dernières erreurs
            ],
        }

    def clear_error_registry(self):
        """Vide le registre des erreurs."""
        self.error_registry.clear()


# Décorateur pour simplifier l'usage
def handle_errors(
    category: Optional[ErrorCategory] = None,
    severity: Optional[ErrorSeverity] = None,
    reraise: bool = False,
    default_return: Any = None,
    user_message: Optional[str] = None,
):
    """
    Décorateur pour gérer automatiquement les erreurs d'une fonction.

    Args:
        category: Catégorie de l'erreur
        severity: Gravité de l'erreur
        reraise: Si True, relance l'exception
        default_return: Valeur de retour par défaut
        user_message: Message utilisateur personnalisé
    """

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Récupérer l'instance ErrorHandler depuis les arguments ou créer une instance globale
                error_handler = (
                    getattr(args[0], "error_handler", None) if args else None
                )
                if not error_handler:
                    error_handler = _get_global_error_handler()

                # Créer le contexte
                context = error_handler.create_error_context(
                    module=func.__module__ or "unknown",
                    function=func.__name__,
                    operation=f"Exécution de {func.__name__}",
                    user_message=user_message,
                )

                # Traiter l'erreur
                return error_handler.handle_error(
                    exception=e,
                    context=context,
                    category=category,
                    severity=severity,
                    reraise=reraise,
                    default_return=default_return,
                )

        return wrapper

    return decorator


# Instance globale pour les cas simples
_global_error_handler: Optional[ErrorHandler] = None


def _get_global_error_handler() -> ErrorHandler:
    """Récupère ou créé l'instance globale du gestionnaire d'erreurs."""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    return _global_error_handler


def get_error_handler() -> ErrorHandler:
    """Récupère l'instance globale du gestionnaire d'erreurs."""
    return _get_global_error_handler()
