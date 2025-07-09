"""
Configuration de base commune à tous les modules.
"""

import os
from pathlib import Path

from dotenv import dotenv_values, load_dotenv

from ..core.ErrorHandler import (
    ErrorCategory,
    ErrorHandler,
    ErrorSeverity,
    handle_errors,
)
from ..core.Logger import create_logger

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
        # Correction : pointer sur la racine du projet (2 parents au-dessus de config)
        self.project_root = Path(__file__).resolve().parents[3]
        self.env_file = env_file or self.project_root / ".env"

        # Initialiser le gestionnaire d'erreurs
        self.error_handler = ErrorHandler(
            log_file=self.project_root / "logs" / "errors.log"
        )

        # Charger les variables d'environnement
        self._load_environment()

    def _reset_environment(self):
        """Remet à zéro seulement les variables du fichier .env pour éviter les conflits."""
        # Ne supprimer que les variables du fichier .env, pas celles de l'environnement système/Docker
        if self.env_file.exists():
            try:
                dotenv_vars = dotenv_values(self.env_file)
                for key in dotenv_vars.keys():
                    # Ne supprimer que si la variable vient du fichier .env et pas de l'environnement
                    if key in os.environ and os.environ[key] == dotenv_vars[key]:
                        os.environ.pop(key, None)
            except Exception:
                # Si erreur de lecture du .env, ne rien supprimer
                pass

    def _load_environment(self):
        """Charge les variables d'environnement."""
        # Ne pas reset si on est dans un environnement containerisé
        if not os.getenv("DOCKER_CONTAINER") and not os.getenv(
            "KUBERNETES_SERVICE_HOST"
        ):
            self._reset_environment()

        # Charger depuis le fichier .env si présent, sinon utiliser les variables système
        if self.env_file.exists():
            try:
                load_dotenv(
                    self.env_file, override=False
                )  # Ne pas écraser les variables existantes
                logger.debug(
                    f"Variables d'environnement chargées depuis: {self.env_file.name}"
                )
            except Exception as e:
                logger.warning(f"Erreur lors du chargement du fichier .env: {e}")
        else:
            logger.info(
                f"Fichier .env non trouvé ({self.env_file.name}), utilisation des variables système"
            )

    @handle_errors(
        category=ErrorCategory.CONFIGURATION,
        severity=ErrorSeverity.HIGH,
        user_message="Erreur lors de la récupération d'une variable d'environnement",
        reraise=True,
    )
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

        if required and (value is None or value == ""):
            raise ValueError(f"Variable d'environnement {key} manquante")

        return value
