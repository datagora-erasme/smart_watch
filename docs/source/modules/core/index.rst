Vue d'ensemble
==============

- **ConfigManager** : Configuration centralisée modulaire agrégant toutes les configurations
- **Logger** : Système de logs unifié avec support fichier/console et rotation des fichiers
- **ErrorHandler** : Gestion centralisée des erreurs avec traçabilité et catégorisation
- **MarkdownProcessor** : Filtrage sémantique par embeddings pour extraire les sections horaires
- **ComparateurHoraires** : Comparaison intelligente d'horaires JSON avec normalisation
- **LLMClient** : Abstraction pour APIs LLM (OpenAI, Mistral, compatibles)
- **EmailSender** : Envoi d'emails avec pièces jointes et templates
- **GetPrompt** : Génération de prompts optimisés pour extraction d'horaires
- **URLRetriever** : Récupération robuste de contenu web avec gestion SSL avancée
- **NotificationManager** : Orchestration des rapports et envoi par email

Modules
--------

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
   get_prompt
   url_retriever
   notification_manager
