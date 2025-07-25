# Gestionnaire de configuration centralisé simplifié
# https://datagora-erasme.github.io/smart_watch/source/modules/core/config_manager.html

from pathlib import Path
from typing import Optional

from ..config.base_config import BaseConfig
from ..config.database_config import DatabaseConfigManager
from ..config.email_config import EmailConfigManager
from ..config.llm_config import LLMConfigManager
from ..config.markdown_filtering_config import MarkdownFilteringConfigManager
from ..config.processing_config import ProcessingConfigManager
from ..core.ErrorHandler import ErrorCategory, ErrorSeverity
from .Logger import create_logger

# Initialize logger for this module
logger = create_logger(
    module_name="ConfigManager",
)


class ConfigManager:
    """Gestionnaire de configuration centralisé simplifié."""

    def __init__(self, env_file: Optional[Path] = None):
        """
        Initialise le gestionnaire de configuration centralisée.

        Cette méthode configure le chemin du projet, charge le fichier d'environnement (.env),
        initialise la configuration de base et les gestionnaires de configuration satellites.
        Elle gère également les erreurs critiques lors de l'initialisation.

        Args:
            env_file (Optional[Path]): Chemin personnalisé vers le fichier d'environnement (.env).
                Si non spécifié, le fichier .env à la racine du projet sera utilisé.

        Raises:
            Exception: Toute erreur survenant lors de l'initialisation des gestionnaires de configuration
                est capturée, traitée par le gestionnaire d'erreurs, puis relancée avec une sévérité critique.
        """
        self.project_root = Path(__file__).resolve().parents[3]
        self.env_file = env_file or self.project_root / ".env"

        # Initialiser la configuration de base
        self.base_config = BaseConfig(self.env_file)
        self.error_handler = self.base_config.error_handler

        try:
            # Initialiser les gestionnaires de configuration modulaires
            self._init_config_managers()

            logger.info("Configuration centralisée initialisée")

        except Exception as e:
            context = self.error_handler.create_error_context(
                module="ConfigManager",
                function="__init__",
                operation="Initialisation de la configuration",
                user_message="Erreur lors du chargement de la configuration",
            )
            self.error_handler.handle_error(
                exception=e,
                context=context,
                reraise=True,
                severity=ErrorSeverity.CRITICAL,
                category=ErrorCategory.CONFIGURATION,
            )

    def _init_config_managers(self):
        """
        Initialise les gestionnaires de configuration modulaires et expose leurs configurations.

        Cette méthode crée et initialise les gestionnaires de configuration pour différents modules
        (LLM, base de données, email, traitement, filtrage Markdown) en utilisant le fichier d'environnement
        fourni. Les configurations de chaque gestionnaire sont exposées comme attributs de l'instance.
        Les références aux gestionnaires sont conservées pour permettre la validation ultérieure.

        Args:
            Aucun argument.

        Attributes:
            llm (dict): Configuration du gestionnaire LLM.
            database (dict): Configuration du gestionnaire de base de données.
            email (dict): Configuration du gestionnaire d'email.
            processing (dict): Configuration du gestionnaire de traitement.
            markdown_filtering (dict): Configuration du gestionnaire de filtrage Markdown.
            _managers (dict): Références aux gestionnaires de configuration pour la validation.
        """
        # Initialiser les gestionnaires modulaires
        llm_manager = LLMConfigManager(self.env_file)
        database_manager = DatabaseConfigManager(self.env_file)
        email_manager = EmailConfigManager(self.env_file)
        processing_manager = ProcessingConfigManager(self.env_file)
        markdown_manager = MarkdownFilteringConfigManager(self.env_file)

        # Exposer les configurations
        self.llm = llm_manager.config
        self.database = database_manager.config
        self.email = email_manager.config
        self.processing = processing_manager.config
        self.markdown_filtering = markdown_manager.config

        # Garder les références aux managers pour la validation
        self._managers = {
            "llm": llm_manager,
            "database": database_manager,
            "email": email_manager,
            "processing": processing_manager,
            "markdown_filtering": markdown_manager,
        }

    def validate(self) -> bool:
        """
        Valide les configurations de tous les gestionnaires modulaires.

        Parcourt chaque gestionnaire de configuration enregistré et appelle sa méthode `validate`.
        Si une configuration est invalide ou si une exception est levée lors de la validation,
        un message d'erreur est enregistré. Si toutes les configurations sont valides, un message
        d'information est enregistré.

        Cela permet de s'assurer que toutes les configurations nécessaires sont correctement
        définies avant de démarrer l'application.

        Returns:
            bool: True si toutes les configurations sont valides, False sinon.
        """
        errors = []

        # Valider chaque configuration modulaire
        for name, manager in self._managers.items():
            try:
                if not manager.validate():
                    errors.append(f"Configuration {name} invalide")
            except Exception as e:
                errors.append(f"Configuration {name} - Erreur: {e}")

        if errors:
            for error in errors:
                logger.error(f"Validation échouée: {error}")
            return False

        logger.info("Configuration validée avec succès")
        return True

    def display_summary(self):
        """
        Affiche un résumé détaillé de la configuration actuelle du système dans les logs.

        Cette méthode envoie au logger les informations principales concernant la configuration du LLM,
        des embeddings, de la base de données, du fichier CSV, de l'email et du traitement
        des threads. Les informations sont adaptées selon le fournisseur d'embeddings utilisé
        (OPENAI ou MISTRAL) et selon la présence ou non de la configuration email.

        Returns:
            None
        """
        logger.info("=== RÉSUMÉ CONFIGURATION ===")
        logger.info(f"LLM : {self.llm.fournisseur} - {self.llm.modele}")
        if self.llm.base_url:
            logger.info(f"  URL : {self.llm.base_url}")

        logger.info("---")
        logger.info(f"Embeddings : {self.markdown_filtering.embed_fournisseur}")
        logger.info(f"  Modèle : {self.markdown_filtering.embed_modele}")
        if self.markdown_filtering.embed_fournisseur in ["OPENAI", "MISTRAL"]:
            logger.info(f"  URL : {self.markdown_filtering.embed_base_url}")

        logger.info(
            f"  Seuil similarité : {self.markdown_filtering.similarity_threshold}"
        )
        logger.info(
            f"  Taille des chunks pour embeds : {self.markdown_filtering.chunk_size}"
        )
        logger.info(
            f"  Chevauchement entre les chunks : {self.markdown_filtering.chunk_overlap}"
        )
        logger.info(
            f"  Taille min contenu pour filtrer : {self.markdown_filtering.min_content_length}"
        )
        logger.info(
            f"  Phrases référence : {len(self.markdown_filtering.reference_phrases)} phrases"
        )

        logger.info("---")
        logger.info(f"Base de données: {self.database.db_file.name}")
        logger.info(f"Fichier CSV: {self.database.csv_file.name}")
        if self.email and self.email.emetteur:
            logger.info(
                f"Email: {self.email.emetteur} → {', '.join(self.email.recepteurs)}"
            )
        else:
            logger.info("Email: Non configuré")
        logger.info(f"Threads: {self.processing.nb_threads_url}")
        logger.info("=== FIN CONFIGURATION ===")
