# Documentation
# https://datagora-erasme.github.io/smart_watch/source/modules/config/base_config.html

import os
from pathlib import Path
from typing import Optional

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


def _is_containerized() -> bool:
    """
    Détecte si l'application s'exécute dans un conteneur (Docker/Kubernetes).

    Returns:
        bool: True si dans un conteneur, sinon False.
    """
    # Vérifie les variables d'environnement classiques
    if os.getenv("DOCKER_CONTAINER") or os.getenv("KUBERNETES_SERVICE_HOST"):
        return True
    # Vérifie le cgroup
    cgroup_path = "/proc/1/cgroup"
    if os.path.exists(cgroup_path):
        try:
            with open(cgroup_path, "rt") as f:
                content = f.read()
            return (
                "docker" in content or "kubepods" in content or "containerd" in content
            )
        except Exception:
            pass  # Ignorer les erreurs de lecture
    return False


class BaseConfig:
    """
    Gère la configuration de base de l'application.

    d'environnement depuis un fichier .env, et fournit un accès sécurisé
    à ces variables.
    """

    def __init__(self, env_file: Optional[Path] = None):
        """
        Initialise une instance de BaseConfig.

        Args:
        Args:
            env_file (Path, optional): Chemin vers le fichier .env.
                Si non fourni, sera recherché à la racine du projet.
        """
        # Définir la racine du projet et le fichier .env
        self.project_root = Path(__file__).resolve().parents[3]
        self.env_file = env_file or self.project_root / ".env"

        # Initialiser le gestionnaire d'erreurs
        self.error_handler = ErrorHandler(
            log_file=self.project_root / "logs" / "errors.log"
        )

        # Charger les variables d'environnement
        self._load_environment()

    def _reset_environment(self):
        """
        Réinitialise les variables d'environnement du fichier .env.

        Supprime les variables chargées depuis le fichier .env pour éviter
        les conflits avec les variables système ou conteneurisées.
        Ne s'exécute pas dans un environnement conteneurisé.
        """
        # Ne supprimer que les variables provenant du fichier .env pour ne pas
        # affecter l'environnement système ou conteneurisé.
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
        """
        Charge les variables d'environnement depuis le fichier .env.

        Réinitialise d'abord les variables (sauf en environnement conteneurisé)
        puis charge celles du fichier .env. Si le fichier n'existe pas,
        utilise les variables système existantes.
        """
        if not _is_containerized():
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
    def get_env_var(
        self, key: str, default: Optional[str] = None, required: bool = False
    ) -> Optional[str]:
        """
        Récupère une variable d'environnement de manière sécurisée.

        Args:
            required (bool): Si True, lève une exception si manquante.

        Returns:
            Optional[str]: La valeur de la variable d'environnement, ou None.

        Raises:
            ValueError: Si la variable est requise mais non définie.
        Raises:
            ValueError: Si la variable est requise mais non définie.
        """
        value = os.getenv(key, default)

        if required and (value is None or value == ""):
            raise ValueError(f"Variable d'environnement {key} manquante")

        return value
