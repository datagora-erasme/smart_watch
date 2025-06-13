"""
Module de gestion générique de base de données SQLite.
Classe générique réutilisable pour différents projets.
"""

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import polars as pl


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

    def exists(self) -> bool:
        """
        Vérifie si la base de données existe.

        Returns:
            True si la base existe, False sinon
        """
        return self.db_file.exists()

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
                print(f"{action} de la base de données SQLite '{self.db_file}'")

                df_initial.write_database(
                    table_name=self.table_name,
                    connection=f"sqlite:///{self.db_file}",
                    if_table_exists="replace",
                )
                print(
                    f"Base de données initialisée avec {len(df_initial)} enregistrements"
                )
            elif if_exists == "skip":
                print(f"Base de données existante trouvée : '{self.db_file}' - Ignorée")
            else:
                raise FileExistsError(
                    f"La base de données '{self.db_file}' existe déjà"
                )
        except Exception as err:
            print(
                f"Erreur lors de l'initialisation de la base de données '{self.db_file}': '{err}'"
            )
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
            print(f"Chargement de {len(df)} enregistrements depuis la base")
            return df
        except Exception as err:
            print(
                f"Erreur lors du chargement depuis la base de données '{self.db_file}': '{err}'"
            )
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

            return rows_affected

        except Exception as err:
            print(f"Erreur lors de la mise à jour : {err}")
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
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            results = cursor.fetchall()
            conn.close()

            return results
        except Exception as err:
            print(f"Erreur lors de l'exécution de la requête : {err}")
            raise
