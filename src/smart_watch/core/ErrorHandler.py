# Documentation :
# https://datagora-erasme.github.io/smart_watch/source/modules/core/error_handler.html

import datetime
import functools
import traceback
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from .Logger import LogLevel, create_logger


class ErrorSeverity(Enum):
    """
    Enumération représentant le niveau de gravité d'une erreur.

    Attributes:
        LOW (str): Erreur mineure, le traitement peut continuer.
        MEDIUM (str): Erreur modérée, le traitement peut continuer avec une dégradation des fonctionnalités.
        HIGH (str): Erreur grave, il est recommandé d'arrêter le traitement.
        CRITICAL (str): Erreur critique, le traitement ne peut pas continuer.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """
    Enumération d'erreurs utilisées pour classifier les exceptions dans l'application.

    Attributes:
        CONFIGURATION (ErrorCategory): Erreur liée à la configuration de l'application.
        DATABASE (ErrorCategory): Erreur en lien avec la base de données.
        NETWORK (ErrorCategory): Erreur de connexion ou de communication réseau.
        LLM (ErrorCategory): Erreur liée au modèle de langage (LLM).
        FILE_IO (ErrorCategory): Erreur lors des opérations d'entrée/sortie sur les fichiers.
        VALIDATION (ErrorCategory): Erreur de validation des données ou des paramètres.
        CONVERSION (ErrorCategory): Erreur lors de la conversion de données ou de formats.
        PARSING (ErrorCategory): Erreur lors de l'analyse ou du parsing de données.
        EMAIL (ErrorCategory): Erreur lors de l'envoi ou de la réception d'emails.
        EMBEDDINGS (ErrorCategory): Erreur lors de l'utilisation des embeddings.
        UNKNOWN (ErrorCategory): Erreur non catégorisée.
    """

    CONFIGURATION = "configuration"
    DATABASE = "database"
    NETWORK = "network"
    LLM = "llm"
    FILE_IO = "file_io"
    VALIDATION = "validation"
    CONVERSION = "conversion"
    PARSING = "parsing"
    EMAIL = "email"
    EMBEDDINGS = "embeddings"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """
    Classe représentant le contexte d'une erreur survenue dans l'application.

    Attributes:
        module (str): Nom du module où l'erreur s'est produite.
        function (str): Nom de la fonction où l'erreur s'est produite.
        operation (str): Description de l'opération en cours lors de l'erreur.
        data (Optional[Dict[str, Any]]): Données supplémentaires liées à l'erreur (optionnel).
        user_message (Optional[str]): Message destiné à l'utilisateur concernant l'erreur (optionnel).
    """

    module: str
    function: str
    operation: str
    data: Optional[Dict[str, Any]] = None
    user_message: Optional[str] = None


@dataclass
class HandledError:
    """
    Classe représentant une erreur gérée.

    Attributes:
        category (ErrorCategory): catégorie de l'erreur.
        severity (ErrorSeverity): niveau de sévérité.
        exception (Exception): exception associée à l'erreur.
        context (ErrorContext): contexte dans lequel l'erreur s'est produite.
        timestamp (str): date et heure de l'occurrence de l'erreur.
        traceback (str): trace complète de l'erreur.
        resolved (bool): Indique si l'erreur a été résolue.
        solution_attempted (Optional[str]): Description de la solution tentée, si applicable.
    """

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

    def __init__(self):
        """
        Initialise le gestionnaire d'erreurs.

        Ce constructeur configure le logger pour le module ErrorHandler, initialise le registre des erreurs traitées,
        et prépare les gestionnaires spécialisés pour chaque catégorie d'erreur.

        Attributes:
            logger: Logger dédié au module ErrorHandler.
            error_registry: Liste des erreurs traitées par le gestionnaire.
            category_handlers: Dictionnaire associant chaque catégorie d'erreur à sa méthode de gestion spécialisée.
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
            ErrorCategory.EMBEDDINGS: self._handle_embeddings_error,
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
        Traite une exception de manière centralisée, en enregistrant l'erreur, en la journalisant,
        et en appliquant un traitement spécialisé selon la catégorie et la gravité.

        Peut relancer l'exception ou retourner une valeur par défaut.

        Args:
            exception (Exception): L'exception à traiter.
            context (ErrorContext): Contexte additionnel lié à l'erreur.
            severity (ErrorSeverity): Gravité de l'erreur.
            category (ErrorCategory): Catégorie de l'erreur.
            reraise (bool, optionnel): Si True, relance l'exception après traitement. Par défaut à False.
            default_return (Any, optionnel): Valeur à retourner si aucun résultat n'est produit par le traitement spécialisé.

        Returns:
            Any: Résultat du traitement spécialisé, ou la valeur par défaut si aucun résultat n'est produit.

        Raises:
            Exception: Relance l'exception d'origine si `reraise` est True.
        """

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
        """
        Enregistre une erreur gérée dans le système de logs avec différents niveaux de gravité.

        Cette méthode construit un message d'erreur détaillé incluant la catégorie, le contexte,
        l'opération, l'exception, un message utilisateur optionnel et des données contextuelles.

        Le niveau de log est déterminé en fonction de la gravité de l'erreur. Pour les erreurs
        graves (HIGH ou CRITICAL), la trace complète est également enregistrée en debug.

        Args:
            handled_error (HandledError): L'objet représentant l'erreur gérée, contenant toutes
                les informations nécessaires pour le logging (catégorie, contexte, exception,
                gravité, message utilisateur, données, traceback).
        """

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
        """
        Applique un traitement spécialisé à une erreur gérée selon sa catégorie.

        Cette méthode tente de récupérer un gestionnaire spécialisé pour la catégorie
        de l'erreur fournie. Si un gestionnaire est trouvé, il est exécuté avec l'erreur
        en paramètre. En cas d'exception lors de l'exécution du gestionnaire, une erreur
        est enregistrée dans le logger. Si aucun gestionnaire n'est disponible ou en cas
        d'échec, la méthode retourne None.

        Args:
            handled_error (HandledError): L'erreur à traiter, encapsulée dans un objet HandledError.

        Returns:
            Any: Le résultat du gestionnaire spécialisé si disponible et sans erreur, sinon None.
        """

        handler = self.category_handlers.get(handled_error.category)
        if handler:
            try:
                return handler(handled_error)
            except Exception as e:
                self.logger.error(f"Erreur dans le gestionnaire spécialisé: {e}")

        return None

    def _handle_configuration_error(self, error: HandledError) -> Any:
        """
        Gère les erreurs de configuration spécifiques et propose des solutions adaptées.

        Cette méthode analyse l'exception contenue dans l'objet `HandledError` et, selon le type d'erreur (KeyError ou ValueError),
        elle renseigne une tentative de solution et suggère des actions correctives via le logger.

        Args:
            error (HandledError): L'objet d'erreur contenant l'exception à traiter.

        Returns:
            Any: Toujours None, cette méthode est utilisée pour ses effets de bord (journalisation et modification de l'objet d'erreur).
        """

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
        """
        Gère les erreurs spécifiques liées à la base de données et propose des solutions.

        Cette méthode analyse le message d'exception pour détecter des erreurs courantes
        telles que l'absence de table ou le verrouillage de la base de données. Elle
        consigne une solution adaptée dans le logger et met à jour l'attribut
        `solution_attempted` de l'objet d'erreur.

        Args:
            error (HandledError): L'objet représentant l'erreur interceptée, contenant
                l'exception et les informations associées.

        Returns:
            Any: Toujours None, cette méthode est utilisée pour ses effets de bord
            (journalisation et mise à jour de l'erreur).
        """

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
        """
        Gère les erreurs liées au réseau en analysant le type d'exception et en proposant une solution.

        Cette méthode vérifie si l'erreur est une erreur de connexion ou un timeout réseau,
        puis met à jour la tentative de solution dans l'objet `HandledError` et enregistre
        une suggestion dans le logger.

        Args:
            error (HandledError): L'objet contenant l'exception à traiter et les informations associées.

        Returns:
            Any: Toujours None, cette méthode ne retourne pas de valeur utile.
        """

        if isinstance(error.exception, ConnectionError):
            error.solution_attempted = "Problème de connexion réseau"
            self.logger.info("Solution: Vérifiez votre connexion internet")

        elif isinstance(error.exception, TimeoutError):
            error.solution_attempted = "Timeout réseau"
            self.logger.info("Solution: Augmentez le timeout ou réessayez plus tard")

        return None

    def _handle_llm_error(self, error: HandledError) -> Any:
        """
        Traite les erreurs liées au LLM et propose des solutions ou messages adaptés.

        Args:
            error (HandledError): L'erreur interceptée contenant l'exception à analyser.

        Returns:
            Any: Retourne un message d'erreur spécifique si un timeout est détecté, sinon None.

        Notes:
            - Modifie l'attribut `solution_attempted` de l'objet error selon le type d'erreur détecté.
            - Loggue une solution adaptée via le logger pour les erreurs de clé API ou de limite de taux.
            - Retourne un message d'erreur pour les timeouts afin de permettre la poursuite du traitement.
        """

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
        """
        Gère les erreurs liées aux opérations d'entrée/sortie de fichiers.

        Cette méthode analyse l'exception contenue dans l'objet `HandledError` et adapte le message de solution proposée selon le type d'erreur rencontré :
        - Si le fichier est introuvable (`FileNotFoundError`), elle précise le nom du fichier manquant.
        - Si les permissions sont insuffisantes (`PermissionError`), elle indique ce problème.

        Args:
            error (HandledError): L'objet contenant l'exception à traiter.

        Returns:
            Any: Toujours `None`, cette méthode modifie l'objet d'erreur en place.
        """

        if isinstance(error.exception, FileNotFoundError):
            missing_file = getattr(error.exception, "filename", "fichier inconnu")
            error.solution_attempted = f"Fichier manquant: {missing_file}"

        elif isinstance(error.exception, PermissionError):
            error.solution_attempted = "Permissions insuffisantes"

        return None

    def _handle_parsing_error(self, error: HandledError) -> Any:
        """
        Gère les erreurs de parsing des données d'entrée.

        Cette méthode modifie l'attribut `solution_attempted` de l'erreur pour indiquer qu'une erreur de parsing a eu lieu,
        enregistre une information dans le logger pour suggérer de vérifier le format des données d'entrée, puis retourne
        `None` afin que la valeur par défaut définie par le décorateur soit utilisée.

        Args:
            error (HandledError): L'objet représentant l'erreur de parsing rencontrée.

        Returns:
            Any: Toujours `None`, pour permettre l'utilisation d'une valeur par défaut.
        """
        error.solution_attempted = "Erreur de parsing des données"
        self.logger.info(
            "Solution: Vérifiez le format des données d'entrée. L'opération a continué avec une valeur par défaut."
        )
        # Retourne None pour que la valeur par défaut du décorateur soit utilisée
        return None

    def _handle_validation_error(self, error: HandledError) -> Any:
        """
        Traite une erreur de validation et retourne une réponse structurée.

        Cette méthode modifie l'attribut `solution_attempted` de l'objet `error` pour indiquer
        qu'une tentative de solution a été effectuée, puis retourne un dictionnaire contenant
        un message d'erreur et les détails de l'exception.

        Args:
            error (HandledError): L'objet représentant l'erreur de validation à traiter.

        Returns:
            Any: Un dictionnaire avec les clés 'error' et 'details' décrivant l'échec de la validation.
        """

        error.solution_attempted = "Données invalides"
        return {"error": "Validation failed", "details": str(error.exception)}

    def _handle_email_error(self, error: HandledError) -> Any:
        """
        Traite les erreurs liées à l'envoi d'emails et propose une solution adaptée.

        Cette méthode analyse le message d'exception associé à une erreur d'email,
        puis définit une tentative de solution en fonction du type d'erreur détectée
        (authentification ou connexion SMTP).

        Args:
            error (HandledError): L'objet représentant l'erreur à traiter, contenant l'exception d'origine.

        Returns:
            Any: Toujours None. La solution proposée est enregistrée dans l'attribut `solution_attempted` de l'objet error.
        """

        error_str = str(error.exception).lower()

        if "authentication" in error_str:
            error.solution_attempted = "Erreur d'authentification email"

        elif "connection" in error_str:
            error.solution_attempted = "Erreur de connexion SMTP"

        return None

    def _handle_embeddings_error(self, error: HandledError) -> Any:
        """
        Gère les erreurs spécifiques aux embeddings.

        Args:
            error (HandledError): L'objet d'erreur contenant l'exception à traiter.

        Returns:
            Any: Toujours None, cette méthode est utilisée pour ses effets de bord.
        """
        error_str = str(error.exception).lower()

        if "api key" in error_str:
            error.solution_attempted = "Clé API invalide pour les embeddings"
            self.logger.info("Solution: Vérifiez votre clé API pour les embeddings")
        elif "rate limit" in error_str:
            error.solution_attempted = "Limite de taux atteinte pour les embeddings"
            self.logger.info(
                "Solution: Attendez avant de réessayer avec les embeddings"
            )
        elif "timeout" in error_str:
            error.solution_attempted = "Timeout lors de la génération des embeddings"
            self.logger.info("Solution: Augmentez le timeout ou réessayez plus tard")
        elif "mistral" in error_str:
            error.solution_attempted = "Erreur spécifique au modèle Mistral. Mistral n'accepte pas plus de 16384 tokens pour les embeddings."
            self.logger.info(
                "Solution: Vérifiez la configuration du modèle Mistral et le nombre de tokens de votre texte"
            )
        else:
            error.solution_attempted = (
                "Erreur inconnue lors de la génération des embeddings"
            )
            self.logger.info(
                "Solution: Vérifiez la configuration des embeddings / du modèle utilisé"
            )
        return None

    def create_error_context(
        self,
        module: str,
        function: str,
        operation: str,
        data: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
    ) -> ErrorContext:
        """
        Crée un contexte d'erreur pour faciliter la gestion et le suivi des erreurs dans le module.

        Args:
            module (str): Nom du module où l'erreur s'est produite.
            function (str): Nom de la fonction concernée par l'erreur.
            operation (str): Description de l'opération en cours lors de l'erreur.
            data (Optional[Dict[str, Any]]): Données supplémentaires liées à l'erreur (par défaut None).
            user_message (Optional[str]): Message destiné à l'utilisateur pour expliquer l'erreur (par défaut None).

        Returns:
            ErrorContext: Objet contenant toutes les informations contextuelles sur l'erreur.
        """

        return ErrorContext(
            module=module,
            function=function,
            operation=operation,
            data=data,
            user_message=user_message,
        )

    def get_error_summary(self) -> Dict[str, Any]:
        """
        Résume les erreurs enregistrées dans le registre d'erreurs.

        Retourne un dictionnaire contenant le nombre total d'erreurs, la répartition par catégorie et par gravité,
        ainsi que les cinq dernières erreurs enregistrées avec leurs détails.

        Returns:
            Dict[str, Any]:
                Un dictionnaire avec les clés suivantes :
                    - "total_errors" (int): Nombre total d'erreurs enregistrées.
                    - "by_category" (dict): Répartition des erreurs par catégorie.
                    - "by_severity" (dict): Répartition des erreurs par gravité.
                    - "recent_errors" (list): Liste des cinq dernières erreurs, chacune sous forme de dictionnaire contenant :
                        - "category" (str): Catégorie de l'erreur.
                        - "severity" (str): Gravité de l'erreur.
                        - "exception" (str): Description de l'exception.
                        - "module" (str): Module où l'erreur s'est produite.
                        - "timestamp" (Any): Date et heure de l'erreur.
        """

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
        """
        Efface tous les enregistrements d'erreurs du registre interne.

        Cette méthode vide le registre des erreurs, supprimant ainsi toutes les erreurs actuellement stockées.
        Elle peut être utilisée pour réinitialiser l'état des erreurs avant une nouvelle opération ou après un traitement.

        Raises:
            AttributeError: Si le registre d'erreurs n'est pas initialisé correctement.
        """
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
    Décorateur pour gérer les erreurs lors de l'exécution d'une fonction, en utilisant un gestionnaire d'erreurs centralisé.

    Ce décorateur intercepte les exceptions levées par la fonction décorée, crée un contexte d'erreur, et délègue le traitement
    au gestionnaire d'erreurs approprié. Il permet de personnaliser la catégorie et la sévérité de l'erreur, d'afficher un message
    utilisateur, et de choisir si l'exception doit être relancée ou non.

    Il utilise la fonction functools.wraps pour conserver les métadonnées de la fonction d'origine. Cela permet par exemple
    d'afficher la documentation de la fonction décorée avec Sphinx.

    Args:
        category (ErrorCategory): Catégorie de l'erreur à signaler.
        severity (ErrorSeverity): Niveau de sévérité de l'erreur.
        reraise (bool, optionnel): Si True, relance l'exception après traitement. Sinon, retourne `default_return`. Par défaut à False.
        default_return (Any, optionnel): Valeur à retourner en cas d'erreur si `reraise` est False. Par défaut à None.
        user_message (str, optionnel): Message personnalisé à afficher à l'utilisateur. Par défaut à None.

    Returns:
        Callable: Le décorateur appliqué à la fonction cible.

    Exemple d'utilisation:
        @handle_errors(
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.HIGH,
            user_message="Erreur lors de l'exécution du pipeline",
        )

        def run(self):
        ...
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
    """
    Retourne l'instance globale du gestionnaire d'erreurs.

    Cette fonction vérifie si une instance globale de `ErrorHandler` existe déjà.
    Si ce n'est pas le cas, elle en crée une nouvelle et la retourne. Cela permet
    de garantir qu'une seule instance du gestionnaire d'erreurs est utilisée
    dans toute l'application.

    Returns:
        ErrorHandler: L'instance globale du gestionnaire d'erreurs.
    """
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    return _global_error_handler


def get_error_handler() -> ErrorHandler:
    """
    Récupère l'instance globale du gestionnaire d'erreurs.

    Cette fonction permet d'obtenir le gestionnaire d'erreurs utilisé globalement dans l'application.
    Elle est utile pour centraliser la gestion des exceptions et des erreurs.

    Returns:
        ErrorHandler: L'instance globale du gestionnaire d'erreurs.
    """
    return _get_global_error_handler()
