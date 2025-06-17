from datetime import datetime
from typing import Optional

import polars as pl
import requests


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
        response = requests.get(base_url, params=params)
        # print(f"URL appelée: {response.url}")
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

        # On retourne le dataframe Polars trié par date de début et de fin
        return df.sort(["start_date", "end_date"])
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la récupération des vacances scolaires: {e}")
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
    print("=== Test de récupération des vacances scolaires ===")

    # Test 1: Vacances pour Lyon avec dates spécifiques
    print("\n1. Vacances scolaires pour Lyon (2024-2026):")
    vacances_lyon = get_vacances_scolaires(
        localisation="Lyon", date_debut="2025-01-01", date_fin="2025-12-31"
    )

    print(vacances_lyon)

    if not vacances_lyon.is_empty():
        print(f"Nombre de périodes trouvées: {len(vacances_lyon)}")
        for row in vacances_lyon.iter_rows(named=True):
            debut = format_date_vacances(row["start_date"])
            fin = format_date_vacances(row["end_date"])
            description = row["description"]
            zone = row["zones"]
            population = row["population"]
            annee_scolaire = row["annee_scolaire"]
            print(f"  • {description} ({zone}) - {annee_scolaire}")
            print(f"    Du {debut} au {fin} - Population: {population}")
    else:
        print("Impossible de récupérer les vacances scolaires")

    # Test 2: Vacances pour une période courte
    print("\n2. Vacances scolaires pour la zone C au printemps 2025 :")
    vacances_zone_c = get_vacances_scolaires(
        zone="C", date_debut="2025-03-01", date_fin="2025-06-30"
    )

    print(vacances_zone_c)

    if not vacances_zone_c.is_empty():
        # Traiter le DataFrame pour ne garder que les enregistrements uniques,
        # sans tenir compte de la colonne "location"
        vacances_zone_c = vacances_zone_c.unique(
            subset=pl.all().exclude(
                "location"
            ),  # On se base sur toutes les colonnes sauf "location" pour trouver les doublons
            maintain_order=True,
        )

        print(f"Nombre de périodes trouvées: {len(vacances_zone_c)}")
        for row in vacances_zone_c.iter_rows(named=True):
            debut = format_date_vacances(row["start_date"])
            fin = format_date_vacances(row["end_date"])
            description = row["description"]
            print(f"  • {description}: {debut} au {fin}")

    # Test 3: Vacances des élèves pour l'année en cours à Lyon
    year = datetime.now().year
    print(f"\n3. Vacances scolaires pour les élèves à Lyon, sur l'année {year} :")
    vacances = get_vacances_scolaires(
        localisation="Lyon",
        date_debut=f"{year}-01-01",
        date_fin=f"{year}-12-31",
    )

    # print(vacances)

    if not vacances.is_empty():
        # Traiter le DataFrame pour ne garder que les vacances pour élèves ou tous (exclure "Enseignants")
        vacances = vacances.filter(
            pl.col("population").is_in(["Élèves", "-"], nulls_equal=True)
        )

        print(f"Nombre de périodes trouvées: {len(vacances)}")
        for row in vacances.iter_rows(named=True):
            debut = format_date_vacances(row["start_date"])
            fin = format_date_vacances(row["end_date"])
            description = row["description"]
            print(f"  • {description}: {debut} au {fin}")

    # Test 4: Vacances de l'année scolaire en cours à Lyon
    print("\n4. Vacances scolaires pour l'année scolaire en cours à Lyon :")

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

    print(vacances)

    if not vacances.is_empty():
        # Traiter le DataFrame pour ne garder que les vacances pour élèves ou tous (exclure "Enseignants")
        vacances = vacances.filter(
            pl.col("population").is_in(["Élèves", "-"], nulls_equal=True)
        )

        print(f"Nombre de périodes trouvées: {len(vacances)}")
        for row in vacances.iter_rows(named=True):
            debut = format_date_vacances(row["start_date"])
            fin = format_date_vacances(row["end_date"])
            description = row["description"]
            print(f"  • {description}: {debut} au {fin}")


if __name__ == "__main__":
    main()
