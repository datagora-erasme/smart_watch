import csv
from pathlib import Path
from tempfile import NamedTemporaryFile

import polars as pl
import requests

from ..core.Logger import create_logger

# Initialize logger for this module
logger = create_logger(
    module_name="CSVToPolars",
)


class CSVToPolars:
    def __init__(
        self,
        source: str = None,
        separator: str = "auto",
        has_header: bool = True,
    ):
        """
        Initialise la classe CSVToPolars.

        Arguments:
            source (str) : URL ou chemin du fichier CSV à charger
            separator (str, optionnel) : Séparateur utilisé dans le fichier CSV. "auto" pour détection automatique. Par défaut "auto".
            has_header (bool, optionnel) : Indique si le fichier CSV contient une ligne d'en-tête. Par défaut True.
        """
        self.source = source
        self.separator = separator
        self.df: pl.DataFrame | None = None
        self.has_header = has_header

    def _is_url(self, source: str) -> bool:
        """Vérifie si la source est une URL."""
        return source.startswith(("http://", "https://"))

    def _detect_separator(self, sample: str) -> str:
        """Détecte le séparateur CSV en utilisant csv.Sniffer."""
        try:
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample)
            logger.info(f"Séparateur détecté: '{dialect.delimiter}'")
            return dialect.delimiter
        except csv.Error:
            logger.warning("Impossible de détecter le séparateur, utilisation de ';'")
            return ";"

    def _download_to_temp_file(self, url: str) -> Path:
        """Télécharge l'URL vers un fichier temporaire et retourne le chemin."""
        try:
            logger.info(f"Téléchargement CSV depuis: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Créer un fichier temporaire
            temp_file = NamedTemporaryFile(mode="wb", suffix=".csv", delete=False)
            temp_file.write(response.content)
            temp_file.close()

            temp_path = Path(temp_file.name)
            logger.info(
                f"CSV téléchargé vers fichier temporaire: {len(response.content)} bytes"
            )
            return temp_path

        except Exception as e:
            logger.error(f"Erreur téléchargement CSV: {e}")
            raise

    def _process_local_file(
        self, file_path: Path, cleanup_temp: bool = False
    ) -> pl.DataFrame:
        """Traite un fichier local."""
        try:
            # Détection automatique du séparateur si nécessaire
            if self.separator == "auto":
                with file_path.open("r", encoding="utf-8") as f:
                    sample = "".join([next(f) for _ in range(5)])
                self.separator = self._detect_separator(sample)

            logger.info(f"Lecture CSV: {file_path.name}")

            # Lecture avec Polars
            df = pl.read_csv(
                file_path,
                has_header=self.has_header,
                separator=self.separator,
                truncate_ragged_lines=True,
            ).filter(~pl.all_horizontal(pl.all().is_null()))

            return df

        finally:
            # Nettoyage du fichier temporaire si nécessaire
            if cleanup_temp and file_path.exists():
                file_path.unlink()
                logger.debug(f"Fichier temporaire supprimé: {file_path}")

    def load_csv(self) -> pl.DataFrame | str:
        """
        Charge un fichier CSV depuis une URL ou un chemin local.

        Renvoie :
            pl.DataFrame : Le DataFrame Polars résultant si le fichier est accessible.
            str : Message d'erreur si le fichier n'est pas accessible.
        """
        if not self.source:
            error_msg = "Aucune source spécifiée"
            logger.error(error_msg)
            return error_msg

        try:
            if self._is_url(self.source):
                # Télécharger vers fichier temporaire puis traiter
                temp_file_path = self._download_to_temp_file(self.source)
                self.df = self._process_local_file(temp_file_path, cleanup_temp=True)
            else:
                # Fichier local - vérifier existence puis traiter
                file_path = Path(self.source)
                if not file_path.exists():
                    error_msg = f"Fichier {file_path} non trouvé"
                    logger.error(error_msg)
                    return error_msg

                self.df = self._process_local_file(file_path, cleanup_temp=False)

            logger.info(
                f"CSV chargé: {len(self.df)} lignes, {len(self.df.columns)} colonnes"
            )
            return self.df

        except Exception as e:
            error_msg = f"Erreur lors du chargement: {e}"
            logger.error(error_msg)
            return error_msg
