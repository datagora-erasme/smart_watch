from datetime import datetime

import requests

from ..core.ErrorHandler import ErrorCategory, ErrorSeverity, handle_errors
from ..core.Logger import create_logger

# Initialize logger for this module
logger = create_logger(
    module_name="JoursFeries",
)


@handle_errors(
    category=ErrorCategory.NETWORK,
    severity=ErrorSeverity.MEDIUM,
    user_message="Impossible de récupérer les jours fériés depuis l'API.",
    reraise=True,
)
def get_jours_feries(zone="metropole", annee=None):
    """
    Récupère les jours fériés pour une zone et une année données.

    Arguments :
        zone (str): Zone géographique (par défaut: "metropole")
        annee (int): Année (par défaut: année en cours)

    Retourne :
        dict: Dictionnaire des jours fériés.

    Lève:
        requests.exceptions.RequestException: Si une erreur réseau survient.
    """
    if annee is None:
        annee = datetime.now().year

    url = f"https://calendrier.api.gouv.fr/jours-feries/{zone}/{annee}.json"

    logger.debug(f"Requête jours fériés: {zone} {annee}")
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    result = response.json()
    logger.info(f"Jours fériés récupérés: {len(result)} dates")
    return result


def get_day_name(date_str: str) -> str:
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
