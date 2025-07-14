Vacances Scolaires
==================

.. automodule:: src.smart_watch.utils.VacancesScolaires
   :members:
   :undoc-members:
   :show-inheritance:

Fonctionnalités
---------------

Le module VacancesScolaires récupère les périodes de vacances scolaires officielles depuis l'API du gouvernement français. Il fournit des fonctions de filtrage par localisation, zone scolaire et période avec retour de DataFrame Polars optimisé.

**Source de données :**
- API data.education.gouv.fr officielle de l'Éducation Nationale
- Données certifiées et mises à jour automatiquement
- Support des zones A, B, C et localisations spécifiques
- Années scolaires avec format standardisé YYYY-YYYY

**Paramètres de filtrage avancés :**
- Localisation par ville avec recherche intelligente (LIKE)
- Zone scolaire (A, B, C) avec validation
- Période personnalisable avec dates début/fin
- Population ciblée (Élèves, Enseignants) avec filtrage
- Année scolaire complète ou plages de dates spécifiques

**Optimisations Polars :**
- Conversion automatique des dates en format datetime
- Tri optimisé par date de début et fin
- Gestion efficace des DataFrame vides
- Performance optimale pour grandes datasets

**Gestion robuste :**
- Requêtes réseau avec timeout et validation HTTP
- Construction dynamique des clauses WHERE SQL-like
- Logging détaillé des opérations et résultats
- Fallback gracieux en cas d'indisponibilité API

Fonctions principales
---------------------

.. autofunction:: src.smart_watch.utils.VacancesScolaires.get_vacances_scolaires

.. autofunction:: src.smart_watch.utils.VacancesScolaires.format_date_vacances
   # Vacances pour Lyon en 2025
   vacances_lyon - get_vacances_scolaires(
       localisation-"Lyon",
       date_debut-"2025-01-01",
       date_fin-"2025-12-31"
   )
   
   if vacances_lyon and not vacances_lyon.is_empty():
       for row in vacances_lyon.iter_rows(named-True):
           print(f"{row['description']}: {row['start_date']} - {row['end_date']}")
   
   # Vacances zone C pour une période spécifique
   vacances_zone_c - get_vacances_scolaires(
       zone-"C",
       date_debut-"2025-03-01", 
       date_fin-"2025-06-30"
   )
   
   # Vacances de l'année scolaire en cours
   vacances_annee - get_vacances_scolaires(
       localisation-"Lyon",
       annee_scolaire-"2024-2025"
   )

API et format des données
-------------------------

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
-------------------

- **Requêtes réseau** : Gestion des timeouts et erreurs HTTP
- **Données vides** : Retour de DataFrame vide si aucune période trouvée
- **Formats de date** : Validation et conversion automatique
- **Logging** : Traçabilité complète des opérations

Le module utilise le logger SmartWatch pour tracer toutes les opérations et erreurs.
