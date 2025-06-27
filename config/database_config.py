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
            "piscines": "https://data.grandlyon.com/fr/datapusher/ws/grandlyon/adr_voie_lieu.adrequippiscinepct/all.csv?maxfeatures=-1&start=1&filename=piscines-metropole-lyon-point-interet&separator=;",
            "mairies": "https://data.grandlyon.com/fr/datapusher/ws/grandlyon/adr_voie_lieu.adrmairiepct/all.csv?maxfeatures=-1&start=1&filename=mairies-metropole-lyon-point-interet-v2&separator=;",
            "mediatheques": "https://data.grandlyon.com/fr/datapusher/ws/grandlyon/adr_voie_lieu.adrequiculturepct/all.csv?maxfeatures=-1&start=1&filename=bibliotheques-metropole-lyon-point-interet&separator=;",
        }

        # Récupérer le nom du fichier CSV
        csv_url_horaires = self.get_env_var("CSV_URL_HORAIRES", required=True)
        csv_file = data_dir / f"{csv_url_horaires}.csv"
        db_file = data_dir / f"{csv_url_horaires}.db"

        return DatabaseConfig(
            db_file=db_file,
            csv_file=csv_file,
            csv_file_ref=csv_refs,
            schema_file=self.project_root / "assets" / "opening_hours_schema.json",
        )

    def validate(self) -> bool:
        """Valide la configuration base de données."""
        if not self.config.schema_file.exists():
            return False
        return True
