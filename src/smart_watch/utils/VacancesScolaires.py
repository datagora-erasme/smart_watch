from datetime import datetime
from typing import Optional

import polars as pl
import requests

from ..core.Logger import create_logger

# Initialize logger for this module
logger = create_logger(
    module_name="VacancesScolaires",
)


def get_vacances_scolaires(
    localisation: Optional[str] = None,
    zone: Optional[str] = None,
    date_debut: Optional[str] = None,
    date_fin: Optional[str] = None,
    population: Optional[str] = None,
    annee_scolaire: Optional[str] = None,
) -> Optional[pl.DataFrame]:
    """
    Récupère les vacances scolaires pour une localisation et une période données.

    Argument :
        localisation (str, optional): Localisation (par défaut: "Lyon")
        zone (str, optional): Zone scolaire (A, B, C). Si None, toutes les zones
        date_debut (str, optional): Date de début au format YYYY-MM-DD (par défaut: début année courante)
        date_fin (str, optional): Date de fin au format YYYY-MM-DD (par défaut: fin année courante + 2)
        population (str, optional): Population concernée ("Élèves", "Enseignants"). Si None, toutes
        annee_scolaire (str, optional): Année scolaire au format YYYY-YYYY (ex: "2024-2025")

    Retourne :
        pl.DataFrame: DataFrame Polars des périodes de vacances ou None en cas d'erreur
    """
    if date_debut is None:
        date_debut = f"{datetime.now().year}-01-01"
    if date_fin is None:
        date_fin = f"{datetime.now().year + 2}-12-31"

    # Construction de l'URL avec les paramètres
    base_url = "https://data.education.gouv.fr/api/explore/v2.1/catalog/datasets/fr-en-calendrier-scolaire/records"

    # Construction des conditions WHERE
    where_conditions = [
        f"start_date>='{date_debut}'",
        f"end_date<='{date_fin}'",
    ]

    if localisation:
        where_conditions.append(f"location like '{localisation}'")

    if zone:
        where_conditions.append(f"zones like 'Zone {zone}'")

    if population:
        where_conditions.append(f"population like '{population}'")

    if annee_scolaire:
        where_conditions.append(f"annee_scolaire like '{annee_scolaire}'")

    where_clause = " and ".join(where_conditions)
    params = {"where": where_clause, "limit": 100}

    try:
        logger.debug(f"Requête vacances scolaires: {localisation or 'toutes zones'}")
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        # Conversion en DataFrame Polars
        df = pl.DataFrame(data.get("results", []))

        # Convertir les dates en datetime si le DataFrame n'est pas vide
        if not df.is_empty():
            df = df.with_columns(
                [
                    pl.col("start_date").str.to_datetime(),
                    pl.col("end_date").str.to_datetime(),
                ]
            )

        if not df.is_empty():
            logger.info(f"Vacances trouvées: {len(df)} périodes")
        else:
            logger.warning("Aucune période de vacances trouvée")

        # On retourne le dataframe Polars trié par date de début et de fin
        return df.sort(["start_date", "end_date"])
    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur API vacances scolaires: {e}")
        return None


def format_date_vacances(date_str: str) -> str:
    """
    Formate une date de vacances au format lisible.

    Argument :
        date_str (str): Date au format ISO avec timezone

    Retourne :
        str: Date formatée (YYYY-MM-DD)
    """
    try:
        return date_str.strftime("%Y-%m-%d")
    except ValueError:
        return date_str
