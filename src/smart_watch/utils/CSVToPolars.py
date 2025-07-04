import csv
import io
from pathlib import Path

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

    def _download_csv_content(self, url: str) -> bytes:
        """Télécharge le contenu CSV depuis une URL."""
        try:
            logger.info(f"Téléchargement CSV depuis: {url}")

            response = requests.get(url, timeout=30)
            response.raise_for_status()

            logger.info(f"CSV téléchargé: {len(response.content)} bytes")
            return response.content

        except Exception as e:
            logger.error(f"Erreur téléchargement CSV: {e}")
            raise

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
                # Télécharger et lire directement depuis la mémoire
                csv_content = self._download_csv_content(self.source)

                if self.separator == "auto":
                    # Détecter le séparateur à partir d'un échantillon
                    sample = csv_content.splitlines(keepends=True)[100].decode("utf-8")
                    self.separator = self._detect_separator(sample)

                csv_stream = io.BytesIO(csv_content)

                logger.info("Lecture CSV directe depuis la mémoire")
                self.df = pl.read_csv(
                    csv_stream,
                    has_header=self.has_header,
                    separator=self.separator,
                ).filter(~pl.all_horizontal(pl.all().is_null()))
            else:
                # Lire fichier local
                file_path = Path(self.source)
                if not file_path.exists():
                    error_msg = f"Fichier {file_path} non trouvé"
                    logger.error(error_msg)
                    return error_msg

                if self.separator == "auto":
                    # Détecter le séparateur à partir d'un échantillon
                    with file_path.open("r", encoding="utf-8") as f:
                        sample = "".join([next(f) for _ in range(100)])
                    self.separator = self._detect_separator(sample)

                logger.info(f"Chargement CSV local: {file_path.name}")
                self.df = pl.read_csv(
                    file_path, has_header=self.has_header, separator=self.separator
                )

            logger.info(
                f"CSV chargé: {len(self.df)} lignes, {len(self.df.columns)} colonnes"
            )
            return self.df

        except Exception as e:
            error_msg = f"Erreur lors du chargement: {e}"
            logger.error(error_msg)
            return error_msg
