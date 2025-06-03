from pathlib import Path

import polars as pl


class csv_to_polars:
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
            print(f"Fichier {self.file_path} trouvé")

            # Transformer ce fichier csv en dataframe Polars
            print(f"Transformation du fichier {self.file_path} en dataframe Polars")
            self.df = pl.read_csv(
                self.file_path, has_header=self.has_header, separator=self.separator
            )

            print("Fichier transformé en dataframe Polars")
            return self.df
        else:
            return f"Fichier {self.file_path} non trouvé"

    def print_info(self) -> None:
        """
        Affiche des informations sur le DataFrame chargé, telles que le nom du fichier,
        le nombre de lignes et de colonnes, et les premières lignes du DataFrame.
        """
        if self.df is not None:
            print(f"Fichier: {self.file_path.name}")
            print(f"{self.df.shape[0]} lignes, {self.df.shape[1]} colonnes")
            print(self.df.head())
        else:
            print("Aucun fichier chargé")
