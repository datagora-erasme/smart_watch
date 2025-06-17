from datetime import datetime

import requests


def get_jours_feries(zone="metropole", annee=None):
    """
    Récupère les jours fériés pour une zone et une année données.

    Args:
        zone (str): Zone géographique (par défaut: "metropole")
        annee (int): Année (par défaut: année en cours)

    Returns:
        dict: Dictionnaire des jours fériés
    """
    if annee is None:
        annee = datetime.now().year

    url = f"https://calendrier.api.gouv.fr/jours-feries/{zone}/{annee}.json"

    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la récupération des données: {e}")
        return None


def get_day_name(date_str):
    """
    Retourne le nom du jour de la semaine en français pour une date donnée.

    Args:
        date_str (str): Date au format YYYY-MM-DD

    Returns:
        str: Nom du jour de la semaine
    """
    jours = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    return jours[date_obj.weekday()]


def main():
    """Fonction principale pour tester la récupération des jours fériés."""
    jours_feries = get_jours_feries()

    if jours_feries:
        print(f"Jours fériés pour la métropole en {datetime.now().year}:")
        for date, nom in jours_feries.items():
            jour_semaine = get_day_name(date)
            print(f"{date} ({jour_semaine}): {nom}")
    else:
        print("Impossible de récupérer les jours fériés")


if __name__ == "__main__":
    main()
