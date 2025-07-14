"""
Gestionnaire de configuration centralisé pour le projet smart_watch.
Point d'entrée simplifié qui agrège les configurations modulaires.
"""

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
        Initialise le gestionnaire de configuration.

        Args:
            env_file: Chemin vers le fichier .env (optionnel)
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
        """Initialise tous les gestionnaires de configuration."""
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
        """Valide la configuration complète."""
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
        """Affiche un résumé de la configuration."""
        logger.info("=== RÉSUMÉ CONFIGURATION ===")
        logger.info(f"LLM: {self.llm.fournisseur} - {self.llm.modele}")
        if self.llm.base_url:
            logger.info(f"  URL: {self.llm.base_url}")

        logger.info("---")
        logger.info(f"Embeddings: {self.markdown_filtering.embed_fournisseur}")
        if self.markdown_filtering.embed_fournisseur == "OPENAI":
            logger.info(f"  Modèle: {self.markdown_filtering.embed_modele_openai}")
            logger.info(f"  URL: {self.markdown_filtering.embed_base_url_openai}")
        else:  # MISTRAL
            logger.info(f"  Modèle: {self.markdown_filtering.embed_modele_mistral}")

        logger.info(
            f"  Seuil similarité: {self.markdown_filtering.similarity_threshold}"
        )
        logger.info(f"  Fenêtre contexte: {self.markdown_filtering.context_window}")
        logger.info(
            f"  Taille min contenu: {self.markdown_filtering.min_content_length}"
        )
        logger.info(
            f"  Phrases référence: {len(self.markdown_filtering.reference_phrases)} phrases"
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
