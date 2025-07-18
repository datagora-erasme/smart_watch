Base Configuration
==================

Fonctionnalités
---------------

Le module BaseConfig fournit la couche de base pour la gestion des configurations dans SmartWatch.
Il centralise le chargement des variables d'environnement depuis le fichier .env ou les variables système, et tient compte d'une éventuelle exécution dans un environnement conteneurisé.


La classe ``BaseConfig`` est utilisée dans `ConfigManager.py <https://datagora-erasme.github.io/smart_watch/source/modules/config/base_config.html>`__, `database_config.py <https://datagora-erasme.github.io/smart_watch/source/modules/config/database_config.html>`__, `email_config.py <https://datagora-erasme.github.io/smart_watch/source/modules/config/email_config.html>`__, `llm_config.py <https://datagora-erasme.github.io/smart_watch/source/modules/config/llm_config.html>`__, `markdown_filtering.py <https://datagora-erasme.github.io/smart_watch/source/modules/config/markdown_filtering.html>`__, `processing_config.py <https://datagora-erasme.github.io/smart_watch/source/modules/config/processing_config.html>`__.

**Chargement des variables :**

- Support des fichiers .env avec fallback vers les variables système
- Validation des variables requises vs optionnelles
- Gestion des erreurs de configuration
- Détection automatique des environnements Docker/Kubernetes
- Messages d'erreur explicites pour les variables manquantes

Modules
-------

.. automodule:: src.smart_watch.config.base_config
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__, __call__
   :inherited-members:
   :show-inheritance:
