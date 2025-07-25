StatsManager
============

Le module ``StatsManager`` gère la collecte, l'analyse et la présentation des statistiques du pipeline SmartWatch. Il s'appuie sur des requêtes SQL pour extraire des indicateurs clés depuis la base de données, et propose des méthodes pour afficher, personnaliser ou exposer ces statistiques via une API.

Architecture
------------

Le module est composé des classes suivantes :

- **StatItem** : Représente un indicateur statistique (valeur, libellé, unité, format).
- **StatsSection** : Regroupe plusieurs StatItem sous un même thème/statistique.
- **StatsManager** : Orchestrateur principal, interroge la base, structure les résultats, propose des méthodes d'affichage et d'export.

Principales fonctionnalités
---------------------------

- **get_pipeline_stats** : Retourne toutes les sections statistiques du pipeline (URLs, Markdown, LLM, Comparaisons, Global).
- **display_stats** : Affiche les statistiques formatées dans les logs.
- **generate_custom_text** : Génère un texte personnalisé à partir d'un template et des statistiques calculées.
- **get_stats_for_api** : Retourne les statistiques dans un format structuré pour une API.

Sections de statistiques
------------------------

Les statistiques sont regroupées par section :

- **header** : Informations d'exécution (ID, timestamp)
- **urls** : Statistiques sur le traitement des URLs (total, réussies, échouées, taux de réussite, erreurs HTTP, timeouts, taille moyenne du contenu)
- **markdown** : Statistiques sur le traitement Markdown (documents traités, nettoyés, filtrés, taille moyenne, caractères supprimés)
- **llm** : Statistiques sur les extractions LLM (tentatives, réussites JSON/OSM, taux de réussite, taille moyenne, émissions CO2)
- **comparisons** : Statistiques de comparaison des horaires (total, identiques, différents, non comparés, taux de précision)
- **global** : Statistiques globales d'exécution (date, modèle/fournisseur LLM, total enregistrements, erreurs, émissions CO2)

Modules
--------

.. automodule:: src.smart_watch.core.StatsManager
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__, __call__
   :inherited-members:
   :show-inheritance: