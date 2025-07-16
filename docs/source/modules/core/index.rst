Vue d'ensemble
==============

- **ComparateurHoraires** : Comparaison intelligente d'horaires JSON avec normalisation
- **ConfigManager** : Configuration centralisée modulaire agrégant toutes les configurations
- **EnvoyerMail** : Envoi d'emails avec pièces jointes et templates
- **ErrorHandler** : Gestion centralisée des erreurs avec traçabilité et catégorisation
- **GetPrompt** : Génération de prompts optimisés pour extraction d'horaires
- **LLMClient** : Abstraction pour APIs LLM (OpenAI, Mistral, compatibles)
- **Logger** : Système de logs unifié avec support fichier/console et rotation des fichiers
- **NotificationManager** : Orchestration des rapports et envoi par email
- **StatsManager** : Collecte, analyse et présentation des statistiques du pipeline
- **URLRetriever** : Récupération robuste de contenu web avec gestion SSL avancée

Modules
--------

Les modules Core constituent le cœur du système SmartWatch, fournissant les fonctionnalités essentielles pour la configuration, les logs, la gestion d'erreurs et les interactions avec les LLM.

.. toctree::
   :maxdepth: 1

   ComparateurHoraires
   ConfigManager
   EnvoyerEmail
   ErrorHandler
   GetPrompt
   LLMClient
   Logger
   MarkdownProcessor
   NotificationManager
   StatsManager
   URLRetriever