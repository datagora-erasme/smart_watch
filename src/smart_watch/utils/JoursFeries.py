from datetime import datetime

import requests

from ..core.Logger import create_logger

# Initialize logger for this module
logger = create_logger(
    module_name="JoursFeries",
)


def get_jours_feries(zone="metropole", annee=None):
    """
    Récupère les jours fériés pour une zone et une année données.

    Arguments :
        zone (str): Zone géographique (par défaut: "metropole")
        annee (int): Année (par défaut: année en cours)

    Retourne :
        dict: Dictionnaire des jours fériés
    """
    if annee is None:
        annee = datetime.now().year

    url = f"https://calendrier.api.gouv.fr/jours-feries/{zone}/{annee}.json"

    try:
        logger.debug(f"Requête jours fériés: {zone} {annee}")
        response = requests.get(url)
        response.raise_for_status()
        result = response.json()
        logger.info(f"Jours fériés récupérés: {len(result)} dates")
        return result
    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur API jours fériés: {e}")
        return None


def get_day_name(date_str):
    """
    Retourne le nom du jour de la semaine en français pour une date donnée.

    Argument :
        date_str (str): Date au format YYYY-MM-DD

    retourne :
        str: Nom du jour de la semaine
    """
    jours = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    return jours[date_obj.weekday()]


def main():
    """Fonction pour tester la librairie."""
    logger.section("TEST JOURS FÉRIÉS")

    jours_feries = get_jours_feries()

    if jours_feries:
        logger.info(f"Jours fériés pour la métropole en {datetime.now().year}:")
        for date, nom in jours_feries.items():
            jour_semaine = get_day_name(date)
            logger.info(f"{jour_semaine} {date} : {nom}")
    else:
        logger.error("Impossible de récupérer les jours fériés")


if __name__ == "__main__":
    main()
