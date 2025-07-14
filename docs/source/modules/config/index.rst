Modules Configuration
======================

Fonctionnalités
===============

Les modules de configuration fournissent une architecture modulaire et flexible pour gérer tous les paramètres du système SmartWatch. Chaque module spécialisé hérite de BaseConfig et gère un aspect spécifique de la configuration.

**Architecture modulaire :**
- Configuration de base commune avec chargement des variables d'environnement
- Modules spécialisés pour chaque composant système
- Validation centralisée avec gestion d'erreurs intégrée
- Support des environnements Docker et containerisés

**Gestion des variables d'environnement :**
- Chargement automatique depuis fichiers .env et variables système
- Validation des variables requises vs optionnelles
- Gestion robuste des erreurs de configuration
- Support des valeurs par défaut intelligentes

**Configuration adaptative :**
- Détection automatique des fournisseurs selon les clés API disponibles
- Fallback gracieux en cas de configuration incomplète
- Validation croisée des paramètres interdépendants
- Messages d'erreur explicites pour faciliter le debugging

**Intégration système :**
- Point d'entrée unique via ConfigManager
- Accès unifié aux configurations spécialisées
- Validation globale avec consolidation des erreurs
- Affichage de résumé pour vérification visuelle

Modules
========

.. toctree::
   :maxdepth: 2

   base_config
   database_config
   processing_config
   markdown_filtering_config
   llm_config
   email_config

Architecture de configuration
=============================

- **BaseConfig** : Configuration de base commune à tous les modules
- **DatabaseConfig** : Configuration de la base de données SQLite
- **ProcessingConfig** : Configuration du traitement (threads, délais)
- **MarkdownFilteringConfig** : Configuration du filtrage sémantique
- **LLMConfig** : Configuration des modèles de langage (OpenAI, Mistral)
- **EmailConfig** : Configuration SMTP pour l'envoi de rapports

Hiérarchie de configuration
============================

.. code-block:: text

   ConfigManager
   ├── LLMConfig (API keys, modèles)
   ├── DatabaseConfig (fichiers, URLs)
   ├── EmailConfig (SMTP, destinataires)
   ├── ProcessingConfig (threads, remplacements)
   └── MarkdownFilteringConfig (embeddings, seuils)
