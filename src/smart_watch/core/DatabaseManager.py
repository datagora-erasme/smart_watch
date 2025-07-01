"""
Module de gestion de base de données SQLite.
Classe générique réutilisable pour différents projets.
"""

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

    def __init__(self, db_file: Union[str, Path], table_name: str):
        """
        Initialise le gestionnaire de base de données.

        Args:
            db_file: Chemin vers le fichier de base de données SQLite
            table_name: Nom de la table principale
        """
        self.db_file = Path(db_file)
        self.table_name = table_name
        logger.debug(f"DatabaseManager initialisé: {self.db_file.name} / {table_name}")

    def exists(self) -> bool:
        """
        Vérifie si la base de données existe.

        Returns:
            True si la base existe, False sinon
        """
        exists = self.db_file.exists()
        logger.debug(f"Base existe: {exists}")
        return exists

    def initialize(self, df_initial: pl.DataFrame, if_exists: str = "fail") -> None:
        """
        Initialise la base de données SQLite avec les données de base.

        Args:
            df_initial: DataFrame initial
            if_exists: Comportement si la base existe ("fail", "replace", "skip")

        Raises:
            Exception: En cas d'erreur lors de l'initialisation
        """
        try:
            if not self.exists() or if_exists == "replace":
                action = "Création" if not self.exists() else "Remplacement"
                logger.info(f"{action} base de données: {self.db_file.name}")

                df_initial.write_database(
                    table_name=self.table_name,
                    connection=f"sqlite:///{self.db_file}",
                    if_table_exists="replace",
                )
                logger.info(f"Base initialisée: {len(df_initial)} enregistrements")
            elif if_exists == "skip":
                logger.info(f"Base existante ignorée: {self.db_file.name}")
            else:
                logger.error(f"Base existe déjà: {self.db_file.name}")
                raise FileExistsError(
                    f"La base de données '{self.db_file}' existe déjà"
                )
        except Exception as err:
            logger.error(f"Erreur initialisation base: {err}")
            raise

    def load_data(self, query: Optional[str] = None) -> pl.DataFrame:
        """
        Charge les données depuis la base SQLite.

        Args:
            query: Requête SQL personnalisée (optionnel)

        Returns:
            DataFrame avec les données

        Raises:
            Exception: En cas d'erreur lors du chargement
        """
        try:
            if query is None:
                query = f"SELECT * FROM {self.table_name}"

            df = pl.read_database_uri(
                query=query,
                uri=f"sqlite:///{self.db_file}",
            )
            logger.info(f"Données chargées: {len(df)} enregistrements")
            return df
        except Exception as err:
            logger.error(f"Erreur chargement données: {err}")
            raise

    def update_record(
        self, where_conditions: Dict[str, Any], update_values: Dict[str, Any]
    ) -> int:
        """
        Met à jour des enregistrements dans la base SQLite.

        Args:
            where_conditions: Conditions WHERE (colonne: valeur)
            update_values: Valeurs à mettre à jour (colonne: valeur)

        Returns:
            Nombre d'enregistrements mis à jour

        Raises:
            Exception: En cas d'erreur lors de la mise à jour
        """
        try:
            # Construire la requête UPDATE
            set_clause = ", ".join([f"{col} = ?" for col in update_values.keys()])
            where_clause = " AND ".join(
                [f"{col} = ?" for col in where_conditions.keys()]
            )

            query = f"UPDATE {self.table_name} SET {set_clause} WHERE {where_clause}"
            params = list(update_values.values()) + list(where_conditions.values())

            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute(query, params)

            rows_affected = cursor.rowcount
            conn.commit()
            conn.close()

            logger.debug(f"Enregistrements mis à jour: {rows_affected}")
            return rows_affected

        except Exception as err:
            logger.error(f"Erreur mise à jour: {err}")
            raise

    def execute_query(self, query: str, params: tuple = None) -> List[tuple]:
        """
        Exécute une requête SQL personnalisée.

        Args:
            query: Requête SQL à exécuter
            params: Paramètres pour la requête (optionnel)

        Returns:
            Résultats de la requête
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
