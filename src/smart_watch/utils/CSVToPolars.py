"""Utilitaire pour charger des fichiers CSV dans des DataFrames Polars.

Ce module fournit la classe `CSVToPolars` pour charger des données CSV
depuis une URL ou un chemin de fichier local dans un DataFrame Polars,
avec détection automatique du séparateur.
"""

import csv
from pathlib import Path
from tempfile import NamedTemporaryFile

import polars as pl
import requests

from ..core.ErrorHandler import ErrorCategory, ErrorSeverity, handle_errors
from ..core.Logger import create_logger

# Initialize logger for this module
logger = create_logger(
    module_name="CSVToPolars",
)


class CSVToPolars:
    """Charge des données CSV depuis une source dans un DataFrame Polars."""

    def __init__(
        self,
        source: str = None,
        separator: str = "auto",
        has_header: bool = True,
    ):
        """Initialise la classe CSVToPolars.

        :param source: URL ou chemin du fichier CSV à charger.
        :type source: str, optional
        :param separator: Séparateur du CSV. "auto" pour une détection automatique.
                          Par défaut, "auto".
        :type separator: str, optional
        :param has_header: Indique si le CSV a une ligne d'en-tête. Par défaut, True.
        :type has_header: bool, optional
        """
        self.source = source
        self.separator = separator
        self.df: pl.DataFrame | None = None
        self.has_header = has_header

    def _is_url(self, source: str) -> bool:
        """Vérifie si la chaîne de caractères source est une URL.

        :param source: La chaîne de caractères à vérifier.
        :type source: str
        :return: ``True`` si la source est une URL, sinon ``False``.
        :rtype: bool
        """
        return source.startswith(("http://", "https://"))

    def _detect_separator(self, sample: str) -> str:
        """Détecte le séparateur d'un échantillon de données CSV.

        Utilise `csv.Sniffer` pour deviner le délimiteur. Si la détection échoue,
        retourne un point-virgule (';') par défaut.

        :param sample: Un échantillon de lignes du fichier CSV.
        :type sample: str
        :return: Le séparateur détecté.
        :rtype: str
        """
        try:
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample)
            logger.info(f"Séparateur détecté: '{dialect.delimiter}'")
            return dialect.delimiter
        except csv.Error:
            logger.warning("Impossible de détecter le séparateur, utilisation de ';'")
            return ";"

    def _download_to_temp_file(self, url: str) -> Path:
        """Télécharge le contenu d'une URL dans un fichier temporaire.

        :param url: L'URL du fichier CSV à télécharger.
        :type url: str
        :raises requests.exceptions.RequestException: En cas d'erreur de téléchargement.
        :return: Le chemin vers le fichier temporaire créé.
        :rtype: pathlib.Path
        """
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
        """Traite un fichier CSV local et le charge dans un DataFrame Polars.

        :param file_path: Le chemin du fichier CSV local.
        :type file_path: pathlib.Path
        :param cleanup_temp: Si ``True``, supprime le fichier après traitement.
        :type cleanup_temp: bool
        :return: Un DataFrame Polars contenant les données du CSV.
        :rtype: polars.DataFrame
        """
        try:
            # Détection automatique du séparateur si nécessaire
            if self.separator == "auto":
                with file_path.open("r", encoding="utf-8") as f:
                    if self.has_header:
                        # Détecter sur l'en-tête uniquement
                        try:
                            sample = next(f)
                        except StopIteration:
                            sample = ""
                    else:
                        # Détecter sur un échantillon de 50 lignes max
                        sample_lines = []
                        for _ in range(50):
                            try:
                                sample_lines.append(next(f))
                            except StopIteration:
                                break
                        sample = "".join(sample_lines)

                if sample:
                    self.separator = self._detect_separator(sample)
                else:
                    logger.warning(
                        "Fichier CSV vide ou échantillon vide, impossible de détecter le séparateur."
                    )
                    self.separator = ";"  # Valeur par défaut

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

    def _load_from_url(self) -> pl.DataFrame:
        """Charge et traite un fichier CSV depuis une URL.

        Télécharge le fichier dans un emplacement temporaire, puis le traite.

        :return: Un DataFrame Polars contenant les données du CSV.
        :rtype: polars.DataFrame
        """
        temp_file_path = self._download_to_temp_file(self.source)
        return self._process_local_file(temp_file_path, cleanup_temp=True)

    def _load_from_path(self) -> pl.DataFrame:
        """Charge et traite un fichier CSV depuis un chemin local.

        :raises FileNotFoundError: Si le fichier local n'est pas trouvé.
        :return: Un DataFrame Polars contenant les données du CSV.
        :rtype: polars.DataFrame
        """
        file_path = Path(self.source)
        if not file_path.exists():
            raise FileNotFoundError(f"Fichier CSV local non trouvé: {file_path}")
        return self._process_local_file(file_path, cleanup_temp=False)

    @handle_errors(
        category=ErrorCategory.FILE_IO,
        severity=ErrorSeverity.HIGH,
        user_message="Impossible de charger ou traiter le fichier CSV source.",
        reraise=True,
    )
    def load_csv(self) -> pl.DataFrame:
        """Charge un fichier CSV depuis une URL ou un chemin local dans un DataFrame.

        Cette méthode est le point d'entrée principal pour charger les données.
        Elle détermine si la source est une URL ou un chemin de fichier et appelle
        la méthode de chargement appropriée.

        :raises ValueError: Si aucune source n'est spécifiée.
        :raises FileNotFoundError: Si le fichier local n'est pas trouvé.
        :raises requests.exceptions.RequestException: Pour les erreurs de téléchargement.
        :return: Le DataFrame Polars résultant.
        :rtype: polars.DataFrame
        """
        if not self.source:
            raise ValueError("Aucune source de fichier CSV n'a été spécifiée.")

        if self._is_url(self.source):
            self.df = self._load_from_url()
        else:
            self.df = self._load_from_path()

        logger.info(
            f"CSV chargé avec succès: {len(self.df)} lignes, {len(self.df.columns)} colonnes"
        )
        return self.df
