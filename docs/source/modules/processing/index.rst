Vue d'ensemble
===============

- **DatabaseManager** : Gestion de la base SQLite avec 3 tables relationnelles (lieux, executions, resultats_extraction)
- **URLProcessor** : Extraction et conversion HTML → markdown brut avec gestion parallèle
- **LLMProcessor** : Extraction d'horaires via LLM avec structured outputs JSON + conversion OSM
- **ComparisonProcessor** : Comparaison intelligente des horaires extraits vs données de référence

Modules
========

Les modules Processing constituent le pipeline de traitement des données, depuis l'extraction des URLs jusqu'à la comparaison des résultats.

.. toctree::
   :maxdepth: 1

   database_manager
   url_processor
   llm_processor
   comparison_processor


Classes de statistiques
=======================

.. autoclass:: src.smart_watch.processing.url_processor.ProcessingStats
   :members:
   :undoc-members:
