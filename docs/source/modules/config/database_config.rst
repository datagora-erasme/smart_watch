Database Configuration
======================

Fonctionnalités
---------------

Le module DatabaseConfig gère la configuration des sources de données et de la base de données SQLite. Il centralise les chemins des fichiers et URLs des sources CSV.

**Configuration des sources :**

- Chemins des fichiers de base de données SQLite
- URLs des sources CSV (data.grandlyon.com)
- Gestion automatique des répertoires de données
- Validation des chemins et accessibilité des fichiers

**Gestion des chemins :**

- Résolution automatique des chemins relatifs depuis la racine du projet
- Création automatique des répertoires si nécessaires
- Validation de l'existence et des permissions des fichiers

Modules
-------

.. automodule:: src.smart_watch.config.database_config
   :members:
   :undoc-members:
   :show-inheritance: