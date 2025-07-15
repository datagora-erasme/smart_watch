Modules Processing
==================

Fonctionnalités
===============

Les modules Processing constituent le pipeline central de traitement des données SmartWatch. Ils orchestrent l'extraction, la transformation et la comparaison des horaires d'ouverture selon un flux séquentiel optimisé.

**Pipeline de traitement :**

- Extraction parallèle du contenu web avec conversion HTML → Markdown
- Traitement LLM avec structured outputs et enrichissement automatique
- Comparaison intelligente avec les données de référence
- Gestion de base de données relationnelle avec traçabilité complète

**Architecture modulaire :**

- Chaque processeur gère une étape spécifique du pipeline
- Interfaces communes avec classes ProcessingStats unifiées
- Gestion d'erreurs intégrée avec continuation du traitement
- Logging détaillé et métriques de performance

**Gestion des données :**

- Base SQLite relationnelle (lieux, executions, resultats_extraction)
- Traçabilité complète de markdown_brut → markdown_nettoye → markdown_filtre
- Chaîne d'erreurs avec timestamps et types détaillés
- Reprise intelligente des exécutions incomplètes

**Optimisations :**

- Traitement parallèle configurable pour les URLs
- Mises à jour par batch pour optimiser les performances base
- Structured outputs JSON pour fiabiliser l'extraction LLM
- Comparaison normalisée avec gestion des cas particuliers

Vue d'ensemble
===============

- **SetupProcessor** : Initialisation du pipeline avec chargement des données CSV et configuration de la base
- **DatabaseProcessor** : Gestion de la base SQLite avec 3 tables relationnelles (lieux, executions, resultats_extraction)
- **URLProcessor** : Extraction et conversion HTML → markdown brut avec gestion parallèle
- **LLMProcessor** : Extraction d'horaires via LLM avec structured outputs JSON + conversion OSM
- **ComparisonProcessor** : Comparaison intelligente des horaires extraits vs données de référence

Modules
========

.. toctree::
   :maxdepth: 1

   database_processor
   url_processor
   llm_processor
   comparison_processor