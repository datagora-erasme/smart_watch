Database Configuration
======================

.. automodule:: src.smart_watch.config.database_config
   :members:
   :undoc-members:
   :show-inheritance:

Classes principales
===================

.. autoclass:: src.smart_watch.config.database_config.DatabaseConfig
   :members:
   :undoc-members:

.. autoclass:: src.smart_watch.config.database_config.DatabaseConfigManager
   :members:
   :undoc-members:
   :show-inheritance:

Fonctionnalités
================

- Configuration des fichiers de base de données SQLite
- URLs des sources CSV de données
- Gestion automatique des chemins relatifs et absolus

Exemple d'utilisation
=====================

.. code-block:: python

   from src.smart_watch.config.database_config import DatabaseConfigManager

   # Initialisation
   db_config = DatabaseConfigManager()
   
   # Accès aux chemins
   print(f"Base de données: {db_config.config.db_file}")
   print(f"CSV principal: {db_config.config.csv_url}")
