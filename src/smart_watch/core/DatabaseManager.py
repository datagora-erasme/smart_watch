# Module de gestion de base de données SQLite.
# https://datagora-erasme.github.io/smart_watch/source/modules/core/databasemanager.html

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import polars as pl

from .Logger import create_logger

# Initialize logger for this module
logger = create_logger(
    module_name="DatabaseManager",
)


class DatabaseManager:
    """Gestionnaire générique de base de données SQLite."""

    def __init__(self, db_file: Union[str, Path]):
        """
        Initialise le gestionnaire de base de données.

        Args:
            db_file (Union[str, Path]): chemin vers le fichier de base de données SQLite
        """
        self.db_file = Path(db_file)
        logger.debug(f"DatabaseManager initialisé avec {self.db_file}")

    def table_exists(self, table_name: str) -> bool:
        """
        Vérifie si une table existe dans la base de données.

        Args:
            table_name (str): nom de la table à vérifier

        Returns:
            bool: True si la table existe, False sinon
        """
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,),
            )
            result = cursor.fetchone()
            conn.close()

            table_exists = result is not None
            logger.debug(f"Table '{table_name}' existe: {table_exists}")
            return table_exists
        except Exception as err:
            logger.error(f"Erreur vérification table: {err}")
            return False

    def initialize(
        self, table_name: str, df_initial: pl.DataFrame, if_exists: str = "fail"
    ) -> None:
        """
        Initialise une table dans la base de données SQLite avec les données de base.

        Args:
            table_name (str): nom de la table à initialiser
            df_initial (pl.DataFrame): dataFrame initial
            if_exists (str): comportement si la table existe ("fail", "replace", "skip")

        Raises:
            Exception: en cas d'erreur lors de l'initialisation
        """
        try:
            table_exists = self.table_exists(table_name)

            if not table_exists:
                # Table n'existe pas, la créer
                logger.info(f"Création de la table: {table_name}")
                df_initial.write_database(
                    table_name=table_name,
                    connection=f"sqlite:///{self.db_file}",
                    if_table_exists="replace",
                )
                logger.info(
                    f"Table '{table_name}' créée: {len(df_initial)} enregistrements"
                )

            elif if_exists == "replace":
                # Table existe, la remplacer
                logger.info(f"Remplacement de la table: {table_name}")
                df_initial.write_database(
                    table_name=table_name,
                    connection=f"sqlite:///{self.db_file}",
                    if_table_exists="replace",
                )
                logger.info(
                    f"Table '{table_name}' remplacée: {len(df_initial)} enregistrements"
                )

            elif if_exists == "skip":
                # Table existe, l'ignorer
                logger.info(f"Table existante ignorée: {table_name}")

            else:  # if_exists == "fail"
                # Table existe, lever une erreur
                logger.error(f"Table existe déjà: {table_name}")
                raise FileExistsError(
                    f"La table '{table_name}' existe déjà dans la base '{self.db_file}'"
                )

        except Exception as err:
            logger.error(f"Erreur initialisation table '{table_name}': {err}")
            raise

    def load_data(self, table_name: str, query: Optional[str] = None) -> pl.DataFrame:
        """
        Charge les données depuis une table de la base SQLite.

        Args:
            table_name (str): nom de la table à charger
            query (Optional[str]): requête SQL personnalisée

        Returns:
            pl.DataFrame : dataFrame avec les données

        Raises:
            Exception: en cas d'erreur lors du chargement
        """
        try:
            if query is None:
                query = f"SELECT * FROM {table_name}"

            df = pl.read_database_uri(
                query=query,
                uri=f"sqlite:///{self.db_file}",
            )
            logger.info(
                f"Données chargées de '{table_name}': {len(df)} enregistrements"
            )
            return df
        except Exception as err:
            logger.error(f"Erreur chargement données de '{table_name}': {err}")
            raise

    def update_record(
        self,
        table_name: str,
        where_conditions: Dict[str, Any],
        update_values: Dict[str, Any],
    ) -> int:
        """
        Met à jour des enregistrements dans une table de la base SQLite.

        Args:
            table_name (str): nom de la table à mettre à jour
            where_conditions (Dict[str, Any]): conditions WHERE (colonne: valeur)
            update_values (Dict[str, Any]): valeurs à mettre à jour (colonne: valeur)

        Returns:
            int: nombre d'enregistrements mis à jour

        Raises:
            Exception: en cas d'erreur lors de la mise à jour
        """
        try:
            # Construire la requête UPDATE
            set_clause = ", ".join([f"{col} = ?" for col in update_values.keys()])
            where_clause = " AND ".join(
                [f"{col} = ?" for col in where_conditions.keys()]
            )

            query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
            params = list(update_values.values()) + list(where_conditions.values())

            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute(query, params)

            rows_affected = cursor.rowcount
            conn.commit()
            conn.close()

            logger.debug(
                f"Enregistrements mis à jour dans '{table_name}': {rows_affected}"
            )
            return rows_affected

        except Exception as err:
            logger.error(f"Erreur mise à jour dans '{table_name}': {err}")
            raise

    def execute_query(self, query: str, params: tuple = None) -> List[tuple]:
        """
        Exécute une requête SQL personnalisée.

        Args:
            query (str): requête SQL à exécuter
            params (Optional[tuple]): paramètres pour la requête (optionnel)

        Returns:
            List[tuple]: résultats de la requête
        """
        try:
            logger.debug(f"Exécution requête: {query[:50]}...")

            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            results = cursor.fetchall()
            conn.close()

            logger.debug(f"Résultats: {len(results)} lignes")
            return results
        except Exception as err:
            logger.error(f"Erreur exécution requête: {err}")
            raise
