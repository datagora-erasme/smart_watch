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
   │   ├── config/               # Modules de configuration
   │   ├── core/                 # Modules centraux
   │   ├── processing/           # Pipeline de traitement
   │   ├── utils/                # Utilitaires
   │   ├── reporting/            # Génération de rapports
   │   ├── data_models/          # Modèles de données
   │   ├── assets/               # Ressources (templates, images)
   │   └── evaluation/           # Système d'évaluation
   ├── data/                     # Données de production
   ├── logs/                     # Fichiers de logs
   ├── docs/                     # Documentation Sphinx
   └── tests/                    # Tests unitaires

Code source (``src/smart_watch/``)
==================================

Chaque module enregistre ses résultats dans une base de données SQLite. Les tabes utilisées sont décrites dans la page suivante, :doc:`bdd`.
Les librairies tierces utilisées sont listées dans le fichier ``requirements.txt`` et documentées dans la section :doc:`stack`.

Assets (``assets/``)
-------------------

**templates/ReportTemplate.html**
    Template HTML principal pour les rapports détaillés avec graphiques et tableaux interactifs.

**templates/SimpleReportTemplate.html**
    Template HTML simplifié pour le corps des emails avec résumé exécutif.

**images/**
    Logos et captures d'écran de l'application utilisés dans la documentation et les rapports.

Configuration (``config/``)
---------------------------

**BaseConfig**
    Gère la configuration de base de l'application, y compris le chargement des variables d'environnement à partir d'un fichier ``.env``.

**DatabaseConfig**
    Gère la configuration des sources de données et de la base de données SQLite, y compris les chemins de fichiers et les URL des sources CSV.

**EmailConfig**
    Gère la configuration pour l'envoi d'e-mails, y compris les détails du serveur SMTP et les informations sur l'expéditeur/le destinataire.

**LLMConfig**
    Gère la configuration des grands modèles linguistiques (LLM), avec détection automatique pour les fournisseurs comme OpenAI et Mistral.

**MarkdownFilteringConfig**
    Gère la configuration pour le filtrage du contenu Markdown à l'aide d'embeddings sémantiques afin d'identifier les sections pertinentes.

**ProcessingConfig**
    Gère les paramètres de traitement tels que le nombre de threads, les délais et les remplacements de caractères pour optimiser les performances.

Core (``core/``)
---------------

**ComparateurHoraires**
    Moteur de comparaison des horaires extraits avec les données de référence OpenStreetMap.

**ConfigManager**
    Orchestrateur principal de la configuration qui initialise et valide tous les modules de configuration.

**DatabaseManager**
    Gestionnaire de la base de données qui s'occupe des connexions et des sessions.

**EnvoyerMail**
    Service d'envoi d'emails avec support des pièces jointes pour la distribution automatique des rapports.

**ErrorHandler**
    Gestionnaire d'erreurs centralisé avec catégorisation, niveaux de sévérité, et accumulation des erreurs pour rapport final.

**GetPrompt**
    Module pour la gestion et la création des prompts envoyés au LLM.

**LLMClient**
    Client unifié pour les interactions avec les modèles de langage. Abstrait les différences entre fournisseurs (OpenAI, Mistral) et intègre le suivi des émissions CO2 avec CodeCarbon.

**Logger**
    Système de journalisation flexible avec support fichier et/ou console, rotation automatique des logs, et niveaux configurables.

**NotificationManager**
    Gestionnaire des notifications pour informer les utilisateurs des événements importants.

**StatsManager**
    Module pour la gestion et le suivi des statistiques de l'application.

**URLRetriever**
    Utilitaire pour récupérer le contenu des URLs de manière efficace.

Data Models (``data_models/``)
-----------------------------

**opening_hours_schema.json**
    Schéma JSON décrivant le format standardisé des horaires d'ouverture pour validation des données extraites.

**schema_bdd**
    Schémas SQLAlchemy définissant la structure de la base de données pour les lieux et résultats d'extraction.

Evaluation (``evaluation/``)
---------------------------

En cours de développement.

Processing (``processing/``)
---------------------------

**ComparisonProcessor**
    Processeur de comparaison qui analyse les différences entre horaires extraits et données de référence.

**DatabaseProcessor**
    Gestionnaire de base de données SQLite avec ORM SQLAlchemy. Gère la création des tables, l'insertion des données et les requêtes.

**LLMProcessor**
    Processeur d'extraction d'horaires utilisant les modèles de langage pour interpréter le contenu Markdown filtré et enregistrer la consommation carbone.

**MarkdownProcessor**
    Processeur de filtrage sémantique du Markdown utilisant des embeddings pour extraire les sections pertinentes aux horaires, tout en mesurant la consommation carbone de l'opération.

**SetupProcessor**
    Initialise et prépare une nouvelle exécution du pipeline. Crée un enregistrement d'exécution en base de données pour suivre le traitement.

**URLProcessor**
    Processeur parallèle pour récupérer le contenu des URLs avec gestion des erreurs HTTP et conversion HTML vers Markdown.

Reporting (``reporting/``)
-------------------------

**GenererRapportHTML**
    Générateur de rapports HTML utilisant Jinja2 avec templates personnalisables et données interactives, incluant la consommation carbone.

**ReportManager**
    Orchestrateur de génération de rapports avec statistiques globales, y compris les émissions de CO2, et envoi automatique par email.

Utils (``utils/``)
-----------------

**CSVToPolars**
    Utilitaire de chargement de fichiers CSV avec détection automatique du séparateur et validation des données.

**JsonConverter** (``CustomJsonToOSM``)
    Convertisseur de format JSON vers format OpenStreetMap pour les horaires d'ouverture standardisés.

**HtmlToMarkdown**
    Convertisseur HTML vers Markdown optimisé pour préserver les informations d'horaires tout en supprimant le bruit.

**JoursFeries**
    Récupère les jours fériés pour une zone et une année données depuis l'API du gouvernement français.

**MarkdownCleaner**
    Nettoyeur de contenu Markdown avec remplacement intelligent des caractères et normalisation du texte.

**OSMConverter** (``OSMToCustomJson``)
    Convertisseur de format OpenStreetMap vers format JSON personnalisé pour les horaires d'ouverture.

**VacancesScolaires**
    Récupération des données de vacances scolaires via l'API gouvernementale française.

Répertoires de données et logs
==============================

Data (``data/``)
---------------

**SmartWatch.db**
    Base de données SQLite principale contenant les lieux, exécutions et résultats d'extraction.

**evaluation.db**
    Base de données SQLite dédiée aux évaluations et tests de performance.

Logs (``logs/``)
---------------

**SmartWatch.log**
    Fichier de log principal avec rotation automatique, contenant toutes les traces d'exécution.

Documentation (``docs/``)
========================

**Architecture**
    Documentation de l'architecture technique, des flux de données et des modules.

**Guides utilisateur**
    Guides d'installation, de configuration et d'utilisation.

**Source**
    Documentation technique générée automatiquement à partir du code source.
