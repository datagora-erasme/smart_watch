"""
Gestionnaire d'erreurs centralisé pour le projet smart_watch.
Standardise la gestion des erreurs, la journalisation et les notifications.
"""

import functools
import traceback
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .Logger import LogLevel, create_logger


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
    PARSING = "parsing"
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

        # Les gestionnaires spécialisés sont conservés
        self.category_handlers = {
            ErrorCategory.CONFIGURATION: self._handle_configuration_error,
            ErrorCategory.DATABASE: self._handle_database_error,
            ErrorCategory.NETWORK: self._handle_network_error,
            ErrorCategory.LLM: self._handle_llm_error,
            ErrorCategory.FILE_IO: self._handle_file_io_error,
            ErrorCategory.VALIDATION: self._handle_validation_error,
            ErrorCategory.PARSING: self._handle_parsing_error,
            ErrorCategory.EMAIL: self._handle_email_error,
        }

    def handle_error(
        self,
        exception: Exception,
        context: ErrorContext,
        severity: ErrorSeverity,
        category: ErrorCategory,
        reraise: bool = False,
        default_return: Any = None,
    ) -> Any:
        """
        Traite une erreur de manière centralisée.
        La catégorie et la gravité doivent être fournies explicitement.
        """
        import datetime

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
                "LLM_API_KEY_OPENAI": "Ajoutez votre clé API OpenAI pour LLM dans le fichier .env",
                "LLM_API_KEY_MISTRAL": "Ajoutez votre clé API Mistral dans le fichier .env",
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

    def _handle_parsing_error(self, error: HandledError) -> Any:
        """Traite les erreurs de parsing."""
        error.solution_attempted = "Erreur de parsing des données"
        self.logger.info(
            "Solution: Vérifiez le format des données d'entrée. L'opération a continué avec une valeur par défaut."
        )
        # Retourne None pour que la valeur par défaut du décorateur soit utilisée
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
    category: ErrorCategory,
    severity: ErrorSeverity,
    reraise: bool = False,
    default_return: Any = None,
    user_message: Optional[str] = None,
):
    """
    Décorateur pour la gestion centralisée des erreurs dans les fonctions.
    Ce décorateur permet d'intercepter les exceptions levées lors de l'exécution d'une fonction,
    de créer un contexte d'erreur enrichi, puis de déléguer le traitement de l'erreur à un gestionnaire
    (ErrorHandler). Il offre la possibilité de relancer l'exception ou de retourner une valeur par défaut.

    Paramètres :
        category (ErrorCategory) : Catégorie de l'erreur à signaler.
        severity (ErrorSeverity) : Niveau de sévérité de l'erreur.
        reraise (bool, optionnel) : Si True, relance l'exception après traitement. Par défaut False.
        default_return (Any, optionnel) : Valeur à retourner en cas d'erreur si reraise est False.
        user_message (str, optionnel) : Message personnalisé destiné à l'utilisateur.

    Renvoie :
        Callable : La fonction décorée avec gestion des erreurs intégrée.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
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
