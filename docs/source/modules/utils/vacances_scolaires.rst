Vacances Scolaires
==================

.. automodule:: src.smart_watch.utils.VacancesScolaires
   :members:
   :undoc-members:
   :show-inheritance:

Fonctions principales
=====================

.. autofunction:: src.smart_watch.utils.VacancesScolaires.get_vacances_scolaires

.. autofunction:: src.smart_watch.utils.VacancesScolaires.format_date_vacances

Fonctionnalités
===============

Le module VacancesScolaires récupère les périodes de vacances scolaires officielles depuis l'API du gouvernement français :

**Source de données :**
- API data.education.gouv.fr
- Données officielles de l'Éducation Nationale
- Support des zones A, B, C et localisations spécifiques

**Paramètres de filtrage :**
- **Localisation** : Filtrage par ville (ex: "Lyon")
- **Zone scolaire** : A, B, ou C
- **Période** : Date de début et fin personnalisables
- **Population** : "Élèves" ou "Enseignants"
- **Année scolaire** : Format "YYYY-YYYY" (ex: "2024-2025")

**Format de retour :**
- DataFrame Polars avec colonnes standardisées
- Dates converties en format datetime
- Tri automatique par date de début

Exemple d'utilisation
=====================

.. code-block:: python

   from src.smart_watch.utils.VacancesScolaires import get_vacances_scolaires

   # Vacances pour Lyon en 2025
   vacances_lyon = get_vacances_scolaires(
       localisation="Lyon",
       date_debut="2025-01-01",
       date_fin="2025-12-31"
   )
   
   if vacances_lyon and not vacances_lyon.is_empty():
       for row in vacances_lyon.iter_rows(named=True):
           print(f"{row['description']}: {row['start_date']} - {row['end_date']}")
   
   # Vacances zone C pour une période spécifique
   vacances_zone_c = get_vacances_scolaires(
       zone="C",
       date_debut="2025-03-01", 
       date_fin="2025-06-30"
   )
   
   # Vacances de l'année scolaire en cours
   vacances_annee = get_vacances_scolaires(
       localisation="Lyon",
       annee_scolaire="2024-2025"
   )

API et format des données
=========================

**URL de base :** ``https://data.education.gouv.fr/api/explore/v2.1/catalog/datasets/fr-en-calendrier-scolaire/records``

**Paramètres de requête :**
- ``where`` : Conditions de filtrage SQL-like
- ``limit`` : Nombre maximum d'enregistrements (défaut: 100)

**Colonnes principales du DataFrame retourné :**
- ``start_date`` : Date de début (datetime)
- ``end_date`` : Date de fin (datetime)
- ``description`` : Description de la période (ex: "Vacances de printemps")
- ``zones`` : Zone(s) concernée(s) (ex: "Zone A")
- ``population`` : Population concernée ("Élèves", "Enseignants", "-")
- ``annee_scolaire`` : Année scolaire (ex: "2024-2025")
- ``location`` : Localisation géographique

Gestion des erreurs
===================

- **Requêtes réseau** : Gestion des timeouts et erreurs HTTP
- **Données vides** : Retour de DataFrame vide si aucune période trouvée
- **Formats de date** : Validation et conversion automatique
- **Logging** : Traçabilité complète des opérations

Le module utilise le logger SmartWatch pour tracer toutes les opérations et erreurs.
