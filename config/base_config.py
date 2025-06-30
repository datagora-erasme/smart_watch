"""
Configuration de base commune à tous les modules.
"""

import os
from pathlib import Path

from dotenv import dotenv_values, load_dotenv

from core.ErrorHandler import ErrorCategory, ErrorHandler, ErrorSeverity
from core.Logger import create_logger

logger = create_logger(
    module_name="BaseConfig",
)


class BaseConfig:
    """Configuration de base pour tous les modules."""

    def __init__(self, env_file: Path = None):
        """
        Initialise la configuration de base.

        Args:
            env_file: Chemin vers le fichier .env
        """
        self.project_root = Path(__file__).parent.parent
        self.env_file = env_file or self.project_root / ".env"

        # Initialiser le gestionnaire d'erreurs
        self.error_handler = ErrorHandler(
            log_file=self.project_root / "logs" / "errors.log"
        )

        # Charger les variables d'environnement
        self._load_environment()

    def _reset_environment(self):
        """Remet à zéro les variables d'environnement pour éviter les conflits."""
        # Variables LLM
        for key in ["API_KEY_OPENAI", "API_KEY_MISTRAL", "BASE_URL_OPENAI"]:
            os.environ.pop(key, None)

        # Variables du fichier .env
        if self.env_file.exists():
            dotenv_vars = dotenv_values(self.env_file)
            for key in dotenv_vars.keys():
                os.environ.pop(key, None)

    def _load_environment(self):
        """Charge les variables d'environnement."""
        self._reset_environment()

        if self.env_file.exists():
            load_dotenv(self.env_file)
            logger.debug(
                f"Variables d'environnement chargées depuis: {self.env_file.name}"
            )
        else:
            logger.warning(f"Fichier .env non trouvé: {self.env_file}")

    def get_env_var(self, key: str, default: str = None, required: bool = False):
        """
        Récupère une variable d'environnement avec gestion d'erreurs.

        Args:
            key: Nom de la variable
            default: Valeur par défaut
            required: Si True, lève une erreur si manquante

        Returns:
            Valeur de la variable

        Raises:
            ValueError: Si la variable est requise mais manquante
        """
        value = os.getenv(key, default)

        if required and not value:
            context = self.error_handler.create_error_context(
                module="BaseConfig",
                function="get_env_var",
                operation=f"Récupération variable {key}",
                user_message=f"Variable d'environnement {key} requise mais manquante",
            )

            self.error_handler.handle_error(
                exception=ValueError(f"Variable d'environnement {key} manquante"),
                context=context,
                category=ErrorCategory.CONFIGURATION,
                severity=ErrorSeverity.HIGH,
                reraise=True,
            )

        return value
