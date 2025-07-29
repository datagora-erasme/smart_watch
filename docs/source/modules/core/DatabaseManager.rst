Database Manager
================

Le module ``DatabaseManager`` fournit une interface générique pour interagir avec une base de données SQLite.

Fonctionnalités
---------------

- Gère la connexion et la déconnexion à la base de données.
- Initialise le schéma de la base de données si nécessaire.
- Fournit des méthodes pour les opérations CRUD (Create, Read, Update, Delete).
- Permet l'exécution de requêtes SQL personnalisées.

.. admonition:: Usage

   Le ``DatabaseManager`` est utilisé par les modules de traitement, comme le :doc:`DatabaseProcessor <../processing/database_processor>`, pour stocker et récupérer les données sur les horaires.

Modules
-------

.. automodule:: src.smart_watch.core.DatabaseManager
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__, __call__
   :inherited-members:
   :show-inheritance:
