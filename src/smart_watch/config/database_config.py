"""
Configuration base de données centralisée.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from .base_config import BaseConfig


@dataclass
class DatabaseConfig:
    """Configuration base de données."""

    db_file: Path
    csv_file: Path
    csv_file_ref: Dict[str, str]
    schema_file: Path
    csv_url: str  # Nouvelle propriété pour l'URL du CSV principal


class DatabaseConfigManager(BaseConfig):
    """Gestionnaire de configuration base de données."""

    def __init__(self, env_file=None):
        super().__init__(env_file)
        self.config = self._init_database_config()

    def _init_database_config(self) -> DatabaseConfig:
        """Initialise la configuration base de données."""
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
        import urllib.parse

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

    def validate(self) -> bool:
        """Valide la configuration base de données."""
        if not self.config.schema_file.exists():
            return False
        return True
