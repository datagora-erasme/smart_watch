import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import polars as pl
import requests
from dotenv import load_dotenv

from core.Logger import LogOutput, create_logger

# Charger la variable d'environnement pour le nom du fichier log
load_dotenv()
csv_name = os.getenv("CSV_URL_HORAIRES")

# Initialize logger for this module
logger = create_logger(
    outputs=[LogOutput.CONSOLE, LogOutput.FILE],
    log_file=Path(__file__).parent.parent / "logs" / f"{csv_name}.log",
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


def main():
    """Fonction pour tester la librairie."""
    logger.section("TEST VACANCES SCOLAIRES")

    # Test 1: Vacances pour Lyon avec dates spécifiques
    logger.info("Test vacances Lyon 2025")
    vacances_lyon = get_vacances_scolaires(
        localisation="Lyon", date_debut="2025-01-01", date_fin="2025-12-31"
    )

    if vacances_lyon and not vacances_lyon.is_empty():
        logger.info(f"Résultat: {len(vacances_lyon)} périodes trouvées")
        for row in vacances_lyon.iter_rows(named=True):
            debut = format_date_vacances(row["start_date"])
            fin = format_date_vacances(row["end_date"])
            description = row["description"]
            zone = row["zones"]
            population = row["population"]
            annee_scolaire = row["annee_scolaire"]
            logger.info(
                f"  • {description} ({zone}) - {annee_scolaire} | Du {debut} au {fin} - Population: {population}"
            )
    else:
        logger.error("Impossible de récupérer les vacances scolaires")

    # Test 2: Vacances pour une période courte
    logger.info("Test vacances zone C printemps 2025")
    vacances_zone_c = get_vacances_scolaires(
        zone="C", date_debut="2025-03-01", date_fin="2025-06-30"
    )

    if vacances_zone_c and not vacances_zone_c.is_empty():
        # Traiter le DataFrame pour ne garder que les enregistrements uniques,
        # sans tenir compte de la colonne "location"
        vacances_zone_c = vacances_zone_c.unique(
            subset=pl.all().exclude(
                "location"
            ),  # On se base sur toutes les colonnes sauf "location" pour trouver les doublons
            maintain_order=True,
        )

        logger.info(f"Résultat: {len(vacances_zone_c)} périodes trouvées")
        for row in vacances_zone_c.iter_rows(named=True):
            debut = format_date_vacances(row["start_date"])
            fin = format_date_vacances(row["end_date"])
            description = row["description"]
            logger.info(f"  • {description}: {debut} au {fin}")
    else:
        logger.warning("Aucune période de vacances trouvée pour la zone C")

    # Test 3: Vacances des élèves pour l'année en cours à Lyon
    year = datetime.now().year
    logger.info(f"Test vacances élèves Lyon année {year}")
    vacances = get_vacances_scolaires(
        localisation="Lyon",
        date_debut=f"{year}-01-01",
        date_fin=f"{year}-12-31",
    )

    if vacances and not vacances.is_empty():
        # Traiter le DataFrame pour ne garder que les vacances pour élèves ou tous (exclure "Enseignants")
        vacances = vacances.filter(
            pl.col("population").is_in(["Élèves", "-"], nulls_equal=True)
        )

        logger.info(f"Résultat: {len(vacances)} périodes trouvées")
        for row in vacances.iter_rows(named=True):
            debut = format_date_vacances(row["start_date"])
            fin = format_date_vacances(row["end_date"])
            description = row["description"]
            logger.info(f"  • {description}: {debut} au {fin}")
    else:
        logger.warning("Aucune période de vacances trouvée pour les élèves")

    # Test 4: Vacances de l'année scolaire en cours à Lyon
    logger.info("Test vacances année scolaire en cours Lyon")
    # Calcul de l'année scolaire en cours
    # L'année scolaire commence en septembre et se termine en juin de l'année suivante
    # Date du jour
    auj = datetime.now()
    if auj.month >= 8 and auj.day >= 15:
        # Après le 15 août, on est dans l'année scolaire année en cours - année en cours + 1
        year = auj.year
    else:
        # Avant le 15 août, on est dans l'année scolaire année en cours - 1 - année en cours
        year = auj.year - 1

    vacances = get_vacances_scolaires(
        localisation="Lyon",
        annee_scolaire=f"{year}-{year + 1}",
    )

    if vacances and not vacances.is_empty():
        # Traiter le DataFrame pour ne garder que les vacances pour élèves ou tous (exclure "Enseignants")
        vacances = vacances.filter(
            pl.col("population").is_in(["Élèves", "-"], nulls_equal=True)
        )

        logger.info(f"Résultat: {len(vacances)} périodes trouvées")
        for row in vacances.iter_rows(named=True):
            debut = format_date_vacances(row["start_date"])
            fin = format_date_vacances(row["end_date"])
            description = row["description"]
            logger.info(f"  • {description}: {debut} au {fin}")
    else:
        logger.warning(
            "Aucune période de vacances trouvée pour l'année scolaire en cours"
        )


if __name__ == "__main__":
    main()
