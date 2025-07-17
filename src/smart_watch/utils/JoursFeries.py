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
def get_jours_feries(
    zone: str = "metropole", annee: int | None = None
) -> dict[str, str]:
    """
    Récupère les jours fériés pour une zone et une année données depuis l'API du gouvernement français.

    Args:
        zone (str, optional): La zone géographique ('metropole', 'alsace-moselle', etc.).
                              Par défaut, 'metropole'.
        annee (int, optional): L'année pour laquelle récupérer les jours fériés.
                               Par défaut, l'année en cours.

    Returns:
        dict[str, str]: Un dictionnaire avec les dates des jours fériés en clés (YYYY-MM-DD)
                        et les noms des jours fériés en valeurs.
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
