Base Configuration
==================

Le module ``BaseConfig`` est le socle du système de configuration de l'application. Il fournit les fonctionnalités fondamentales pour charger et valider les variables d'environnement, servant de classe de base à tous les gestionnaires de configuration spécialisés.

Fonctionnalités
---------------

- **Chargement d'Environnement** : Charge les variables depuis un fichier ``.env`` ou directement depuis l'environnement système.
- **Détection de Conteneur** : Identifie si l'application s'exécute dans un environnement conteneurisé (Docker, Kubernetes) pour adapter son comportement.
- **Gestion d'Erreurs** : Intègre un gestionnaire d'erreurs pour capturer et signaler les problèmes de configuration de manière centralisée.
- **Accès Sécurisé aux Variables** : Fournit la méthode ``get_env_var`` pour récupérer des variables, en spécifiant si elles sont requises ou en fournissant une valeur par défaut.

.. admonition:: Usage

   ``BaseConfig`` n'est pas instanciée directement. Elle est héritée par les gestionnaires de configuration spécifiques (comme :doc:`DatabaseConfigManager <database_config>`, :doc:`LLMConfigManager <llm_config>`, etc.) qui s'appuient sur ses fonctionnalités pour construire leur propre configuration.

Modules
-------

.. automodule:: src.smart_watch.config.base_config
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__
   :show-inheritance:
