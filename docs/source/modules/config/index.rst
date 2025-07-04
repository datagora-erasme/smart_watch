Modules Configuration
======================

Les modules de configuration fournissent une gestion modulaire et flexible de tous les paramètres du système.

.. toctree::
   :maxdepth: 2

   base_config
   llm_config
   database_config
   email_config
   processing_config
   markdown_filtering_config

Architecture de configuration
==============================

- **BaseConfig** : Configuration de base commune à tous les modules
- **LLMConfig** : Configuration des modèles de langage (OpenAI, Mistral)
- **DatabaseConfig** : Configuration de la base de données SQLite
- **EmailConfig** : Configuration SMTP pour l'envoi de rapports
- **ProcessingConfig** : Configuration du traitement (threads, délais)
- **MarkdownFilteringConfig** : Configuration du filtrage sémantique

Hiérarchie de configuration
============================

.. code-block:: text

   ConfigManager
   ├── LLMConfig (API keys, modèles)
   ├── DatabaseConfig (fichiers, URLs)
   ├── EmailConfig (SMTP, destinataires)
   ├── ProcessingConfig (threads, remplacements)
   └── MarkdownFilteringConfig (embeddings, seuils)
