Base Configuration
==================

.. automodule:: src.smart_watch.config.base_config
   :members:
   :undoc-members:
   :show-inheritance:

Classes principales
===================

.. autoclass:: src.smart_watch.config.base_config.BaseConfig
   :members:
   :undoc-members:
   :show-inheritance:

Fonctionnalités
===============

- Chargement des variables d'environnement depuis `.env` et système
- Gestion robuste pour Docker et environnements containerisés
- Validation et gestion d'erreurs centralisée
- Support des variables requises et optionnelles

Exemple d'utilisation
=====================

.. code-block:: python

   from src.smart_watch.config.base_config import BaseConfig

   # Initialisation
   config = BaseConfig()
   
   # Récupération de variables
   api_key = config.get_env_var("API_KEY_OPENAI", required=True)
   log_level = config.get_env_var("LOG_LEVEL", default="INFO")
