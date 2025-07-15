Comparison Processor
====================

Fonctionnalités
---------------

Le ComparisonProcessor compare les horaires extraits par LLM avec les données de référence data.grandlyon.com. Il utilise une comparaison JSON normalisée avec gestion intelligente des cas particuliers.

**Sources de comparaison :**

- Référence : données data.grandlyon.com converties en JSON via OSMToCustomJson
- Extraction : horaires LLM au format JSON personnalisé
- Comparaison directe JSON vs JSON avec normalisation préalable
- Gestion des formats OSM et JSON avec conversion automatique

**Logique de comparaison :**

- Utilisation du HorairesComparator pour comparaison intelligente
- Normalisation des structures (tri, formats, occurrences)
- Détection des fermetures définitives et temporaires
- Comparaison par période (hors vacances, vacances, jours fériés)

**Types de résultats :**

- `True` : horaires identiques après normalisation
- `False` : différences détectées avec description détaillée
- `None` : impossible de comparer (erreur ou données manquantes)

**Traitement global :**

- Traite tous les enregistrements nécessitant une comparaison
- Indépendant de l'execution_id pour rattrapage automatique
- Mise à jour sélective uniquement si comparaison réussie
- Gestion des cas d'erreur avec préservation des données partielles

**Gestion des erreurs :**

- Validation des données JSON avant comparaison
- Traçabilité des erreurs dans la chaîne pipeline
- Logging détaillé des résultats et différences
- Préservation des données partielles en cas d'erreur

Modules
-------

.. automodule:: src.smart_watch.processing.comparison_processor
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__, __call__
   :inherited-members:
   :show-inheritance: