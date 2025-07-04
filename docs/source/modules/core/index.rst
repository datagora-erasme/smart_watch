Vue d'ensemble
===============

- **ConfigManager** : Configuration centralisée modulaire agrégant toutes les configurations
- **Logger** : Système de logs unifié avec support fichier/console et rotation
- **ErrorHandler** : Gestion centralisée des erreurs avec traçabilité et catégorisation
- **MarkdownProcessor** : Filtrage sémantique par embeddings pour extraire les sections horaires
- **ComparateurHoraires** : Comparaison intelligente d'horaires JSON avec normalisation
- **LLMClient** : Abstraction pour APIs LLM (OpenAI, Mistral, compatibles)
- **EmailSender** : Envoi d'emails avec pièces jointes et templates

Modules
========

Les modules Core constituent le cœur du système SmartWatch, fournissant les fonctionnalités essentielles pour la configuration, les logs, la gestion d'erreurs et les interactions avec les LLM.

.. toctree::
   :maxdepth: 1

   config_manager
   logger
   error_handler
   markdown_processor
   comparateur_horaires
   llm_client
   email_sender
