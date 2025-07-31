# Documentation
# https://datagora-erasme.github.io/smart_watch/source/modules/config/database_config.html

import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from ..core.ErrorHandler import ErrorCategory, ErrorSeverity, handle_errors
from .base_config import BaseConfig


@dataclass
class DatabaseConfig:
    """Configuration de la base de données et des sources de données.

    Cette classe de données stocke les chemins vers les fichiers locaux, les URL de téléchargement et les schémas nécessaires à l'application.

    Attributes:
        db_file: chemin vers le fichier de base de données SQLite.
        csv_file: chemin vers le fichier CSV principal mis en cache localement.
        csv_file_ref: dictionnaire des URL des fichiers CSV de référence.
        schema_file: chemin vers le fichier de schéma JSON.
        csv_url: URL du fichier CSV principal à télécharger.
    """

    db_file: Path
    csv_file: Path
    csv_file_ref: Dict[str, str]
    schema_file: Path
    csv_url: str


class DatabaseConfigManager(BaseConfig):
    """Gère la configuration de la base de données.

    Cette classe hérite de `BaseConfig` pour charger les variables d'environnement et initialiser les paramètres spécifiques à la base de données.
    """

    def __init__(self, env_file: Path | None = None) -> None:
        """Initialise le gestionnaire de configuration de la base de données.

        Args:
            env_file: chemin optionnel vers un fichier .env personnalisé.
        """
        super().__init__(env_file)
        self.config: DatabaseConfig = self._init_database_config()

    def _init_database_config(self) -> DatabaseConfig:
        """Initialise la configuration de la base de données.

        Cette méthode lit les variables d'environnement pour construire les chemins vers les fichiers et les URL nécessaires.

        Returns:
            Une instance de `DatabaseConfig` contenant la configuration.
        """
        data_dir = self.project_root / "data"

        # Références CSV
        csv_refs = {
            "piscines": self.get_env_var("CSV_URL_PISCINES", required=True),
            "mairies": self.get_env_var("CSV_URL_MAIRIES", required=True),
            "mediatheques": self.get_env_var("CSV_URL_MEDIATHEQUES", required=True),
        }

        # Récupérer l'URL du fichier CSV principal
        csv_url = self.get_env_var("CSV_URL_HORAIRES", required=True)

        # Extraire le nom du fichier depuis l'URL pour le cache local
        parsed_url = urllib.parse.urlparse(csv_url)
        filename = parsed_url.path.split("/")[-1]

        # Fichier local pour le cache
        csv_file = data_dir / filename
        db_file = data_dir / "SmartWatch.db"

        return DatabaseConfig(
            db_file=db_file,
            csv_file=csv_file,
            csv_file_ref=csv_refs,
            schema_file=self.project_root
            / "src"
            / "smart_watch"
            / "data_models"
            / "opening_hours_schema.json",
            csv_url=csv_url,
        )

    @handle_errors(
        category=ErrorCategory.CONFIGURATION,
        severity=ErrorSeverity.HIGH,
        user_message="Erreur lors de la validation de la configuration database",
        reraise=True,
    )
    def validate(self) -> bool:
        """Valide la configuration de la base de données.

        Cette méthode vérifie que les fichiers et répertoires critiques existent et que les URL de sources de données sont valides.

        Returns:
            True si la configuration est valide.

        Raises:
            ValueError: si la validation échoue, avec une liste des erreurs.
        """
        validation_errors = []

        # Vérifier l'existence du fichier de schéma
        if not self.config.schema_file.exists():
            validation_errors.append(
                f"Fichier de schéma manquant: {self.config.schema_file}"
            )

        # Vérifier que les répertoires parent existent ou peuvent être créés
        data_dir = self.config.db_file.parent
        if not data_dir.exists():
            try:
                data_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                validation_errors.append(
                    f"Impossible de créer le répertoire data: {data_dir} - {e}"
                )

        # Vérifier la validité des URLs CSV
        import urllib.parse

        for name, url in self.config.csv_file_ref.items():
            parsed = urllib.parse.urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                validation_errors.append(f"URL invalide pour {name}: {url}")

        # Vérifier l'URL principale
        parsed_main = urllib.parse.urlparse(self.config.csv_url)
        if not parsed_main.scheme or not parsed_main.netloc:
            validation_errors.append(f"URL principale invalide: {self.config.csv_url}")

        # Si des erreurs sont trouvées, lever une exception avec les détails
        if validation_errors:
            error_message = "Validation échouée:\n" + "\n".join(
                f"  - {error}" for error in validation_errors
            )
            raise ValueError(error_message)

        return True
