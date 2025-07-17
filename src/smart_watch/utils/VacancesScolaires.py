# Utilitaire de récupération des plages de vacances scolaires depuis l'API du gouvernement français
# https://datagora-erasme.github.io/smart_watch/source/modules/utils/VacancesScolaires.html

from datetime import datetime
from typing import Optional

import polars as pl
import requests

from ..core.ErrorHandler import ErrorCategory, ErrorSeverity, handle_errors
from ..core.Logger import create_logger

# Initialize logger for this module
logger = create_logger(
    module_name="VacancesScolaires",
)

# URL de base pour l'API des vacances scolaires
BASE_URL = "https://data.education.gouv.fr/api/explore/v2.1/catalog/datasets/fr-en-calendrier-scolaire/records"


@handle_errors(
    category=ErrorCategory.NETWORK,
    severity=ErrorSeverity.MEDIUM,
    user_message="Erreur lors de la récupération des données de vacances scolaires.",
    default_return=None,
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
    Récupère les périodes de vacances scolaires selon les critères spécifiés.

    Args:
        localisation (Optional[str], optional): Localisation géographique (ville, département, etc.).
        zone (Optional[str], optional): Zone scolaire (A, B, C).
        date_debut (Optional[str], optional): Date de début au format 'YYYY-MM-DD'. Par défaut, début de l'année courante.
        date_fin (Optional[str], optional): Date de fin au format 'YYYY-MM-DD'. Par défaut, fin de l'année courante + 2 ans.
        population (Optional[str], optional): Population concernée (élèves, enseignants, etc.).
        annee_scolaire (Optional[str], optional): Année scolaire (ex: '2023-2024').

    Returns:
        Optional[pl.DataFrame]: Un DataFrame Polars contenant les périodes de vacances scolaires triées par date de début et de fin,
        ou None si aucune période n'est trouvée.
    """
    if date_debut is None:
        date_debut = f"{datetime.now().year}-01-01"
    if date_fin is None:
        date_fin = f"{datetime.now().year + 2}-12-31"

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

    logger.debug(f"Requête vacances scolaires: {localisation or 'toutes zones'}")
    response = requests.get(BASE_URL, params=params, timeout=30)
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
