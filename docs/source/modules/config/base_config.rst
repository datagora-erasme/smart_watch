Base Configuration
==================

Fonctionnalités
---------------

Le module BaseConfig fournit la couche de base pour la gestion des configurations dans SmartWatch.
Il centralise le chargement des variables d'environnement depuis le fichier .env ou les variables système, et tient compte d'une éventuelle exécution dans un environnement conteneurisé.

**Chargement des variables :**

* Support des fichiers .env avec fallback vers les variables système
* Validation des variables requises vs optionnelles
* Gestion des erreurs de configuration
* Détection automatique des environnements Docker/Kubernetes
* Messages d'erreur explicites pour les variables manquantes

Module
------

.. automodule:: src.smart_watch.config.base_config
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: Module
