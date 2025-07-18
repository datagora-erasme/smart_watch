Configuration Manager
=====================

Fonctionnalités
---------------

Le ConfigManager fournit un point d'entrée centralisé pour toutes les configurations du système SmartWatch. Il agrège les configurations modulaires et propose une interface unifiée pour la validation et l'accès aux paramètres.

**Agrégation modulaire :**

- Initialisation et coordination de tous les gestionnaires de configuration
- Accès unifié aux configurations LLM, database, email, processing et markdown filtering
- Validation globale avec consolidation des erreurs de tous les modules

**Interface simplifiée :**

- Propriétés directes pour accéder aux configurations (config.llm, config.database, etc.)
- Méthode validate() globale pour vérifier toutes les configurations
- Affichage de résumé avec les paramètres principaux

**Gestion d'erreurs :**

- Intégration avec ErrorHandler pour traçabilité complète
- Messages d'erreur consolidés de tous les modules
- Validation en cascade avec arrêt sur première erreur critique

Modules
-------

.. automodule:: src.smart_watch.core.ConfigManager
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__, __call__
   :inherited-members:
   :show-inheritance: