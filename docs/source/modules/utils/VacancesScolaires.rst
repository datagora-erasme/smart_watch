Vacances Scolaires
==================

Le module VacancesScolaires récupère les périodes de vacances scolaires officielles depuis l'API du gouvernement français. Il fournit des fonctions de filtrage par localisation, zone scolaire et période avec retour de DataFrame Polars.

Fonctionnalités
---------------

- Récupération des vacances scolaires via l'API officielle du gouvernement
- Filtrage par zone (A, B, C), localisation, période, population et année scolaire
- Conversion automatique des dates, tri optimisé, gestion des DataFrame vides

.. admonition:: Usage

   La fonction ``get_vacances_scolaires`` n'est pour l'instant pas exploité dans le projet SmartWatch.


API et format des données
-------------------------

Le module interroge l'API `data.education.gouv.fr` pour récupérer les données sur le calendrier scolaire.

**Endpoint**

- **URL :** ``https://data.education.gouv.fr/api/explore/v2.1/catalog/datasets/fr-en-calendrier-scolaire/records``
- **Méthode :** ``GET``

**Paramètres de la fonction `get_vacances_scolaires`**

Tous les paramètres sont optionnels et permettent de construire une clause ``where`` pour filtrer les résultats de l'API.

- ``localisation`` (str, optionnel): Filtre par localisation géographique (ex: "Lyon", "Académie de Lyon").
- ``zone`` (str, optionnel): Filtre par zone scolaire (ex: "A", "B", "C").
- ``date_debut`` (str, optionnel): Date de début au format 'YYYY-MM-DD'. Par défaut, le 1er janvier de l'année en cours.
- ``date_fin`` (str, optionnel): Date de fin au format 'YYYY-MM-DD'. Par défaut, le 31 décembre de l'année en cours + 2 ans.
- ``population`` (str, optionnel): Filtre par type de population (ex: "Élèves", "Enseignants").
- ``annee_scolaire`` (str, optionnel): Filtre par année scolaire (ex: "2023-2024").

**Format des données en sortie**

La fonction retourne un **DataFrame Polars** contenant les enregistrements qui correspondent aux filtres. Les colonnes principales sont :

- ``description`` (str): Nom de la période de vacances (ex: "Vacances de la Toussaint").
- ``start_date`` (datetime): Date et heure de début de la période.
- ``end_date`` (datetime): Date et heure de fin de la période.
- ``zones`` (str): La ou les zones concernées (ex: "Zone A").
- ``location`` (str): La ou les localisations concernées (ex: "Besançon", "Bordeaux", "Clermont-Ferrand"...).
- ``annee_scolaire`` (str): L'année scolaire de la période.
- ``population`` (str): La population concernée.

Modules
-------

.. automodule:: src.smart_watch.utils.VacancesScolaires
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__, __call__
   :inherited-members:
   :show-inheritance:
