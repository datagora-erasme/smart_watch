import os
from pathlib import Path

import polars as pl
from dotenv import load_dotenv

from core.Logger import LogOutput, create_logger

# Charger la variable d'environnement pour le nom du fichier log
load_dotenv()
csv_name = os.getenv("CSV_URL_HORAIRES")

# Initialize logger for this module
logger = create_logger(
    outputs=[LogOutput.CONSOLE, LogOutput.FILE],
    log_file=Path(__file__).parent.parent / "data" / "logs" / f"{csv_name}.log",
    module_name="CSVToPolars",
)


class CSVToPolars:
    def __init__(
        self, file_path: str = None, separator: str = ";", has_header: bool = True
    ):
        """
        Initialise la classe CSVToPolars.

        Arguments:
            file_path (str, optionnel) : Chemin du fichier CSV à charger. Si None, un chemin par défaut est utilisé.
            separator (str, optionnel) : Séparateur utilisé dans le fichier CSV. Par défaut ";"
            has_header (bool, optionnel) : Indique si le fichier CSV contient une ligne d'en-tête. Par défaut True.
        """
        self.separator = separator
        self.df: pl.DataFrame | None = None
        self.has_header = has_header

        if file_path:
            self.file_path = Path(file_path)
        else:
            # Utilise le chemin par défaut
            script_dir = Path(__file__).parent.resolve()
            data_dir = script_dir / "data"
            self.file_path = data_dir / "alerte_modif_horaire_lieu.csv"

    def load_csv(self) -> pl.DataFrame | str:
        """
        Charge un fichier CSV et le transforme en DataFrame Polars.

        Renvoie :
            pl.DataFrame : Le DataFrame Polars résultant si le fichier est trouvé.
            str : Message d'erreur si le fichier n'est pas trouvé.
        """
        if self.file_path.exists():
            logger.info(f"Chargement CSV: {self.file_path.name}")

            try:
                self.df = pl.read_csv(
                    self.file_path, has_header=self.has_header, separator=self.separator
                )
                logger.info(
                    f"CSV chargé: {len(self.df)} lignes, {len(self.df.columns)} colonnes"
                )
                return self.df
            except Exception as e:
                logger.error(f"Erreur lecture CSV: {e}")
                return f"Erreur lors de la lecture du fichier: {e}"
        else:
            logger.error(f"Fichier CSV introuvable: {self.file_path}")
            return f"Fichier {self.file_path} non trouvé"

    def print_info(self) -> None:
        """
        Affiche des informations sur le DataFrame chargé, telles que le nom du fichier,
        le nombre de lignes et de colonnes, et les premières lignes du DataFrame.
        """
        if self.df is not None:
            logger.info(
                f"Fichier: {self.file_path.name} - {self.df.shape[0]} lignes, {self.df.shape[1]} colonnes"
            )
            logger.debug(f"Premières lignes:\n{self.df.head()}")
        else:
            logger.warning("Aucun fichier chargé")
