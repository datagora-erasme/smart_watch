Database Manager
================

Le module ``DatabaseManager`` fournit une interface générique pour interagir avec une base de données SQLite.

.. admonition:: Usage

   Le ``DatabaseManager`` est utilisé par les modules de traitement, comme le :doc:`DatabaseProcessor <../processing/database_processor>`, pour stocker et récupérer les données en base.

Fonctionnalités
---------------

- Gère la connexion et la déconnexion à la base de données.
- Initialise le schéma de la base de données si nécessaire.
- Fournit des méthodes pour les opérations CRUD (Create, Read, Update, Delete).
- Permet l'exécution de requêtes SQL personnalisées.

Modules
-------

.. automodule:: src.smart_watch.core.DatabaseManager
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__, __call__
   :inherited-members:
   :show-inheritance:
