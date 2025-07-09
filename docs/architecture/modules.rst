========
Modules
========

SmartWatch est organisé en modules spécialisés qui collaborent pour former un pipeline de traitement complet.

Architecture modulaire
======================

Le projet SmartWatch suit une architecture en couches :

Configuration (``config/``)
---------------------------

**BaseConfig**
    Configuration de base commune à tous les modules. Gère le chargement des variables d'environnement depuis le fichier ``.env`` avec validation et gestion d'erreurs centralisée.

**ConfigManager**
    Point d'entrée unifié pour toute la configuration. Agrège les configurations spécialisées et expose une interface simple pour accéder aux paramètres.

**LLMConfig**
    Configuration spécifique aux modèles de langage. Supporte OpenAI, Mistral et autres fournisseurs compatibles avec détection automatique du fournisseur.

**DatabaseConfig**
    Configuration de la base de données SQLite et des fichiers CSV de référence. Gère les chemins et URLs des sources de données.

**EmailConfig**
    Configuration optionnelle pour l'envoi de rapports par email. Supporte SMTP avec authentification SSL/TLS.

**ProcessingConfig**
    Paramètres de traitement (threads, délais, remplacements de caractères) pour optimiser les performances.

**MarkdownFilteringConfig**
    Configuration du filtrage sémantique du contenu Markdown utilisant des embeddings pour identifier les sections pertinentes.

Core (``core/``)
---------------

**Logger**
    Système de journalisation flexible avec support fichier et/ou console, rotation automatique des logs, et niveaux configurables.

**ErrorHandler**
    Gestionnaire d'erreurs centralisé avec catégorisation, niveaux de sévérité, et accumulation des erreurs pour rapport final.

**ConfigManager**
    Orchestrateur principal de la configuration qui initialise et valide tous les modules de configuration.

**LLMClient**
    Client unifié pour les interactions avec les modèles de langage. Abstrait les différences entre fournisseurs (OpenAI, Mistral) et intègre le suivi des émissions CO2 avec CodeCarbon.

**MarkdownProcessor**
    Processeur de filtrage sémantique du Markdown utilisant des embeddings pour extraire les sections pertinentes aux horaires, tout en mesurant la consommation carbone de l'opération.

**ComparateurHoraires**
    Moteur de comparaison des horaires extraits avec les données de référence OpenStreetMap.

**EmailSender**
    Service d'envoi d'emails avec support des pièces jointes pour la distribution automatique des rapports.

Processing (``processing/``)
---------------------------

**DatabaseManager**
    Gestionnaire de base de données SQLite avec ORM SQLAlchemy. Gère la création des tables, l'insertion des données et les requêtes.

**URLProcessor**
    Processeur parallèle pour récupérer le contenu des URLs avec gestion des erreurs HTTP et conversion HTML vers Markdown.

**LLMProcessor**
    Processeur d'extraction d'horaires utilisant les modèles de langage pour interpréter le contenu Markdown filtré et enregistrer la consommation carbone.

**ComparisonProcessor**
    Processeur de comparaison qui analyse les différences entre horaires extraits et données de référence.

**ReportManager**
    Gestionnaire de génération et d'envoi des rapports HTML avec statistiques détaillées et visualisations.

Utils (``utils/``)
-----------------

**CSVToPolars**
    Utilitaire de chargement de fichiers CSV avec détection automatique du séparateur et validation des données.

**HtmlToMarkdown**
    Convertisseur HTML vers Markdown optimisé pour préserver les informations d'horaires tout en supprimant le bruit.

**MarkdownCleaner**
    Nettoyeur de contenu Markdown avec remplacement intelligent des caractères et normalisation du texte.

**CustomJsonToOSM**
    Convertisseur de format JSON vers format OpenStreetMap pour les horaires d'ouverture standardisés.

Reporting (``reporting/``)
-------------------------

**ReportManager**
    Orchestrateur de génération de rapports avec statistiques globales, y compris les émissions de CO2, et envoi automatique par email.

**GenererRapportHTML**
    Générateur de rapports HTML utilisant Jinja2 avec templates personnalisables et données interactives, incluant la consommation carbone.

Data Models (``data_models/``)
-----------------------------

**schema_bdd**
    Schémas SQLAlchemy définissant la structure de la base de données pour les lieux et résultats d'extraction.

**opening_hours_schema.json**
    Schéma JSON décrivant le format standardisé des horaires d'ouverture pour validation des données extraites.

Assets (``assets/``)
-------------------

**templates/ReportTemplate.html**
    Template HTML principal pour les rapports détaillés avec graphiques et tableaux interactifs.

**templates/SimpleReportTemplate.html**
    Template HTML simplifié pour le corps des emails avec résumé exécutif.

**images/**
    Logos et captures d'écran de l'application utilisé dans la documentation et les rapports.
