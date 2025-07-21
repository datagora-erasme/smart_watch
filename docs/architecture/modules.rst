========
Modules
========

SmartWatch est organisé en modules spécialisés qui collaborent pour former un pipeline de traitement complet.

Structure du projet
===================

Le projet SmartWatch suit une architecture en couches organisée dans les répertoires suivants :

.. code-block:: text

   smart_watch/
   ├── src/smart_watch/          # Code source principal
   │   ├── assets/               # Ressources (templates, images)
   │   ├── config/               # Modules de configuration
   │   ├── core/                 # Modules centraux
   │   ├── data_models/          # Modèles de données
   │   ├── evaluation/           # Système d'évaluation
   │   ├── processing/           # Pipeline de traitement
   │   ├── reporting/            # Génération de rapports
   │   └── utils/                # Utilitaires
   ├── data/                     # Données de production
   ├── logs/                     # Fichiers de logs
   ├── docs/                     # Documentation Sphinx
   └── tests/                    # Tests unitaires

Code source (``src/smart_watch/``)
==================================

Chaque module enregistre ses résultats dans une base de données SQLite. Les tabes utilisées sont décrites dans la page suivante, :doc:`bdd`.
Les librairies tierces utilisées sont listées dans le fichier ``requirements.txt`` et documentées dans la section :doc:`stack`.

Assets (``assets/``)
--------------------
Ce module contient les ressources statiques telles que les modèles de rapport et les images.

**templates/ReportTemplate.html** : template HTML pour rapports détaillés.

**templates/SimpleReportTemplate.html** : template HTML pour corps d'emails.

**images/** : logos et captures d'écran.

Configuration (``config/``)
---------------------------
Ce module gère tous les aspects de la configuration de l'application.

:doc:`../source/modules/config/base_config` gère la configuration de base.

:doc:`../source/modules/config/database_config` configure les sources de données.

:doc:`../source/modules/config/email_config` configure l'envoi d'e-mails.

:doc:`../source/modules/config/llm_config` configure les grands modèles linguistiques.

:doc:`../source/modules/config/markdown_filtering_config` configure le filtrage de contenu Markdown.

:doc:`../source/modules/config/processing_config` gère les paramètres de traitement.

Core (``core/``)
----------------
Ce module contient les composants fondamentaux et la logique métier de l'application.

:doc:`../source/modules/core/ComparateurHoraires` compare les horaires extraits/référence.

:doc:`../source/modules/core/ConfigManager` orchestre la configuration globale.

:doc:`../source/modules/core/DatabaseManager` gère les connexions à la BDD.

:doc:`../source/modules/core/EnvoyerMail` envoie des emails avec pièces jointes.

:doc:`../source/modules/core/ErrorHandler` centralise la gestion des erreurs.

:doc:`../source/modules/core/GetPrompt` gère et crée les prompts.

:doc:`../source/modules/core/LLMClient` : client unifié pour les LLMs.

:doc:`../source/modules/core/Logger` : système de journalisation flexible.

:doc:`../source/modules/core/NotificationManager` gère les notifications utilisateurs.

:doc:`../source/modules/core/StatsManager` suit les statistiques d'application.

:doc:`../source/modules/core/URLRetriever` récupère le contenu des URLs.

Data Models (``data_models/``)
------------------------------
Ce module définit la structure des données utilisées dans l'application.

**opening_hours_schema.json** : schéma JSON pour horaires d'ouverture.

**schema_bdd** : schémas SQLAlchemy pour la BDD.

Evaluation (``evaluation/``)
----------------------------
Ce module est dédié à l'évaluation des performances du système.

En cours de développement.

Processing (``processing/``)
----------------------------
Ce module correspond au pipeline de traitement des données, de la récupération à l'analyse.

:doc:`../source/modules/processing/comparison_processor` analyse les différences d'horaires.

:doc:`../source/modules/processing/database_processor` gère la base de données.

:doc:`../source/modules/processing/llm_processor` extrait les horaires via LLM.

:doc:`../source/modules/processing/markdown_processor` filtre le Markdown par sémantique.

:doc:`../source/modules/processing/setup_processor` initialise les exécutions du pipeline.

:doc:`../source/modules/processing/url_processor` récupère le contenu des URLs.

Reporting (``reporting/``)
--------------------------
Ce module est responsable de la génération et de la distribution des rapports.

:doc:`../source/modules/reporting/html_generator` génère des rapports HTML interactifs.

:doc:`../source/modules/reporting/report_manager` orchestre la génération des rapports.

Utils (``utils/``)
------------------
Ce module fournit des fonctions et des classes utilitaires réutilisables.

:doc:`../source/modules/utils/CSVToPolars` charge les fichiers CSV.

:doc:`../source/modules/utils/CustomJsonToOSM` convertit JSON vers format OSM.

:doc:`../source/modules/utils/HtmlToMarkdown` convertit du HTML en Markdown.

:doc:`../source/modules/utils/JoursFeries` récupère les jours fériés.

:doc:`../source/modules/utils/MarkdownCleaner` nettoie le contenu Markdown.

:doc:`../source/modules/utils/OSMToCustomJson` convertit OSM vers format JSON.

:doc:`../source/modules/utils/VacancesScolaires` récupère les vacances scolaires.

Data (``data/``)
----------------
Ce répertoire contient les bases de données utilisées par l'application pour stocker les données de production et d'évaluation.

**SmartWatch.db** : base de données principale (lieux, exécutions et résultats d'extraction).

**evaluation.db** : base de données pour l'évaluation des performances.

Logs (``logs/``)
----------------
Ce répertoire archive les journaux d'événements générés par l'application.

**SmartWatch.log** : journal principal des traces d'exécution.

Documentation (``docs/``)
-------------------------
Ce répertoire rassemble toute la documentation du projet, y compris les guides et les spécifications techniques.

**Architecture** : description de l'architecture et des modules.

**Guides utilisateur** : guides d'installation et d'utilisation.

**Source** : documentation technique générée depuis le code.
