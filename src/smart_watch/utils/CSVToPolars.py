# Documentation :
# https://datagora-erasme.github.io/smart_watch/source/modules/utils/CSVToPolars.html

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
    def __init__(
        self,
        source: str,
        separator: str = "auto",
        has_header: bool = True,
    ):
        """
        Initialise une instance de la classe pour charger et traiter un fichier CSV avec Polars.

        Args:
            source (str, obligatoire): Chemin vers le fichier CSV à charger.
            separator (str, optionnel): Séparateur utilisé dans le fichier CSV. Par défaut "auto" pour une détection automatique.
            has_header (bool, optionnel): Indique si le fichier CSV contient une ligne d'en-tête. True par défaut.

        Attributes:
            source (str): Chemin du fichier source CSV.
            separator (str): Séparateur utilisé pour lire le CSV.
            df (pl.DataFrame | None): DataFrame Polars résultant du chargement du CSV.
            has_header (bool): Indique la présence d'une ligne d'en-tête dans le CSV.
        """
        self.source = source
        self.separator = separator
        self.df: pl.DataFrame | None = (
            None  # indique que l’attribut df peut être soit un objet pl.DataFrame, soit None. "= None" initialise self.df à None au départ.
        )
        self.has_header = has_header

    def _is_url(self, source: str) -> bool:
        """
        Vérifie si la source fournie est une URL.

        Args:
            source (str): La chaîne de caractères à vérifier.

        Returns:
            bool: True si la source commence par 'http://' ou 'https://', sinon False.
        """
        return source.startswith(("http://", "https://"))

    def _detect_separator(self, sample: str) -> str:
        """
        Détecte le séparateur de colonnes dans un échantillon de texte CSV.

        Utilise la classe `csv.Sniffer` pour analyser l'échantillon et déterminer le séparateur utilisé.
        Si la détection échoue, le séparateur par défaut ';' est utilisé.

        Args:
            sample (str): Un échantillon de texte représentant le contenu d'un fichier CSV.

        Returns:
            str: Le séparateur détecté ou ';' si la détection échoue.
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
        """
        Télécharge un fichier CSV depuis une URL et le sauvegarde dans un fichier temporaire.

        Cette méthode effectue une requête HTTP GET vers l'URL spécifiée, vérifie le succès de la réponse,
        puis écrit le contenu du fichier CSV dans un fichier temporaire sur le disque. Le chemin vers ce
        fichier temporaire est ensuite retourné.

        Args:
            url (str): L'URL du fichier CSV à télécharger.

        Returns:
            Path: Le chemin vers le fichier temporaire contenant le CSV téléchargé.

        Raises:
            Exception: Si une erreur survient lors du téléchargement ou de la sauvegarde du fichier.
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
        """
        Traite un fichier CSV local et le convertit en DataFrame Polars. Est appelé par _load_from_url et _load_from_path.

        Cette méthode détecte automatiquement le séparateur si nécessaire, lit le fichier CSV en utilisant Polars,
        et effectue si nécessaire un nettoyage du fichier temporaire après traitement.

        Args:
            file_path (Path): Chemin vers le fichier CSV à traiter.
            cleanup_temp (bool, optionnel): Indique si le fichier temporaire doit être supprimé après traitement.
                Défaut à False.

        Returns:
            pl.DataFrame: DataFrame Polars contenant les données du fichier CSV.

        Note:
            - Le séparateur est détecté automatiquement si `self.separator` vaut "auto".
            - Les lignes entièrement vides sont filtrées du DataFrame résultant.
        """
        try:
            # Détection automatique du séparateur si nécessaire
            if self.separator == "auto":
                with file_path.open("r", encoding="utf-8") as f:
                    if self.has_header:
                        # Si en-tête, on détecte sur elle uniquement
                        try:
                            sample = next(f)
                        except StopIteration:
                            sample = ""
                    else:
                        # Si pas d'en-tête, on détecte sur un échantillon de 50 lignes max
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
            try:
                df = pl.read_csv(
                    file_path,
                    has_header=self.has_header,
                    separator=self.separator,
                    truncate_ragged_lines=True,
                ).filter(~pl.all_horizontal(pl.all().is_null()))
            except pl.exceptions.NoDataError:
                logger.warning(f"Le fichier CSV {file_path.name} est vide.")
                return pl.DataFrame()

            return df

        finally:
            # Nettoyage du fichier temporaire si nécessaire
            if cleanup_temp and file_path.exists():
                file_path.unlink()
                logger.debug(f"Fichier temporaire supprimé: {file_path}")

    def _load_from_url(self) -> pl.DataFrame:
        """
        Charge un fichier CSV depuis une URL et le convertit en DataFrame Polars.

        Cette méthode télécharge le fichier CSV depuis l'URL spécifiée dans `self.source`,
        le sauvegarde dans un fichier temporaire, puis le traite pour le convertir en un DataFrame Polars.
        Le fichier temporaire est supprimé après le traitement.

        Returns:
            pl.DataFrame: Le DataFrame Polars résultant du fichier CSV téléchargé.
        """
        temp_file_path = self._download_to_temp_file(self.source)
        return self._process_local_file(temp_file_path, cleanup_temp=True)

    def _load_from_path(self) -> pl.DataFrame:
        """
        Charge un fichier CSV local et le convertit en DataFrame Polars.

        Cette méthode vérifie l'existence du fichier CSV à partir du chemin spécifié dans `self.source`.
        Si le fichier existe, il est traité et converti en DataFrame Polars via la méthode `_process_local_file`.
        Si le fichier n'est pas trouvé, une exception `FileNotFoundError` est levée.

        Returns:
            pl.DataFrame: Le contenu du fichier CSV sous forme de DataFrame Polars.

        Raises:
            FileNotFoundError: Si le fichier CSV local n'est pas trouvé au chemin spécifié.
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
        """
        Charge un fichier CSV en tant que DataFrame Polars.

        Cette méthode vérifie si la source du fichier CSV est une URL ou un chemin local,
        puis charge le fichier en conséquence. Elle lève une exception si aucune source n'est spécifiée.
        Un message d'information est enregistré après le chargement du fichier.

        Returns:
            pl.DataFrame: Le DataFrame Polars contenant les données du fichier CSV.

        Raises:
            ValueError: Si aucune source de fichier CSV n'a été spécifiée.
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
