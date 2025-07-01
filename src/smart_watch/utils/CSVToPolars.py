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
        separator: str = ";",
        has_header: bool = True,
        cache_dir: str = None,
    ):
        """
        Initialise la classe CSVToPolars.

        Arguments:
            source (str) : URL ou chemin du fichier CSV à charger
            separator (str, optionnel) : Séparateur utilisé dans le fichier CSV. Par défaut ";"
            has_header (bool, optionnel) : Indique si le fichier CSV contient une ligne d'en-tête. Par défaut True.
            cache_dir (str, optionnel) : Répertoire pour mettre en cache les fichiers téléchargés
        """
        self.source = source
        self.separator = separator
        self.df: pl.DataFrame | None = None
        self.has_header = has_header
        self.cache_dir = (
            Path(cache_dir) if cache_dir else Path(__file__).parent.parent / "data"
        )

        # Créer le répertoire de cache s'il n'existe pas
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _is_url(self, source: str) -> bool:
        """Vérifie si la source est une URL."""
        return source.startswith(("http://", "https://"))

    def _download_csv(self, url: str) -> Path:
        """Télécharge un CSV depuis une URL et le met en cache."""
        try:
            logger.info(f"Téléchargement CSV depuis: {url}")

            # Extraire le nom du fichier depuis l'URL
            import urllib.parse

            parsed_url = urllib.parse.urlparse(url)
            filename = parsed_url.path.split("/")[-1] or "downloaded.csv"

            # Chemin du fichier de cache
            cache_file = self.cache_dir / filename

            # Télécharger le fichier
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Sauvegarder en cache
            with open(cache_file, "wb") as f:
                f.write(response.content)

            logger.info(f"CSV téléchargé et mis en cache: {cache_file.name}")
            return cache_file

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
            # Déterminer si c'est une URL ou un fichier local
            if self._is_url(self.source):
                file_path = self._download_csv(self.source)
            else:
                file_path = Path(self.source)
                if not file_path.exists():
                    error_msg = f"Fichier {file_path} non trouvé"
                    logger.error(error_msg)
                    return error_msg

            logger.info(f"Chargement CSV: {file_path.name}")

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

    def print_info(self) -> None:
        """
        Affiche des informations sur le DataFrame chargé.
        """
        if self.df is not None:
            source_name = (
                self.source.split("/")[-1]
                if self._is_url(self.source)
                else Path(self.source).name
            )
            logger.info(
                f"Source: {source_name} - {self.df.shape[0]} lignes, {self.df.shape[1]} colonnes"
            )
            logger.debug(f"Premières lignes:\n{self.df.head()}")
        else:
            logger.warning("Aucun fichier chargé")
