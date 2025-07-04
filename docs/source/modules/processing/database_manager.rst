Database Manager
================

.. automodule:: src.smart_watch.processing.database_manager
   :members:
   :undoc-members:
   :show-inheritance:

Classes principales
===================

.. autoclass:: src.smart_watch.processing.database_manager.DatabaseManager
   :members:
   :undoc-members:
   :show-inheritance:

Fonctions utilitaires
=====================

.. autofunction:: src.smart_watch.processing.database_manager.download_csv

Structure de la base
====================

La base SQLite contient 3 tables principales avec relations :

**Table `lieux` :**
- `identifiant` (PK) : Identifiant unique du lieu
- `nom` : Nom de l'établissement
- `type_lieu` : Type (piscine, mairie, bibliotheque)
- `url` : URL vers la page des horaires
- `horaires_data_gl` : Horaires OSM de référence (data.grandlyon.com)
- `horaires_data_gl_json` : Conversion JSON des horaires de référence

**Table `executions` :**
- `id_executions` (PK) : ID auto-incrémenté
- `date_execution` : Timestamp de l'exécution
- `llm_modele` : Modèle LLM utilisé
- `llm_fournisseur` : Fournisseur (OPENAI, MISTRAL)
- `llm_url` : URL de base de l'API LLM

**Table `resultats_extraction` :**
- `id_resultats_extraction` (PK) : ID auto-incrémenté
- `lieu_id` (FK) : Référence vers `lieux.identifiant`
- `id_execution` (FK) : Référence vers `executions.id_executions`
- Colonnes de traçabilité markdown : `markdown_brut`, `markdown_nettoye`, `markdown_filtre`
- Colonnes LLM : `prompt_message`, `llm_horaires_json`, `llm_horaires_osm`
- Colonnes comparaison : `horaires_identiques`, `differences_horaires`
- Colonnes erreurs : `erreurs_pipeline` (chaîne avec timestamps)

Fonctionnalités avancées
========================

**Gestion des reprises :**
- Détection automatique des exécutions incomplètes
- Reprise intelligente selon l'étape échouée (URL/LLM/OSM)
- Classification et réassignation à la nouvelle exécution

**Traçabilité des erreurs :**
- Chaîne d'erreurs avec timestamps : `[HH:MM:SS] TYPE: message`
- Types : URL, NETTOYAGE, FILTRAGE, LLM, OSM, COMPARAISON
- Accumulation des erreurs par étape du pipeline

**Optimisations :**
- Mises à jour par batch pour l'insertion des lieux
- Requêtes optimisées avec jointures
- Gestion des timeouts et erreurs réseau

Exemple d'utilisation
=====================

.. code-block:: python

   from src.smart_watch.processing.database_manager import DatabaseManager
   from src.smart_watch.core.ConfigManager import ConfigManager

   # Initialisation
   config = ConfigManager()
   db_manager = DatabaseManager(config, logger)
   
   # Setup d'une nouvelle exécution
   execution_id = db_manager.setup_execution(df_csv)
   
   # Récupération des URLs en attente
   pending_urls = db_manager.get_pending_urls(execution_id)
   
   # Mise à jour d'un résultat
   db_manager.update_url_result(resultat_id, result_data)
