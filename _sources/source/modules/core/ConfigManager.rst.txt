Configuration Manager
=====================

Le module ``ConfigManager`` centralise la gestion de toutes les configurations de l'application.

.. admonition:: Usage

   Le ``ConfigManager`` est initialisé au démarrage de l'application pour charger et valider l'ensemble des paramètres nécessaires à son fonctionnement.

Fonctionnalités
---------------

- Agrège les configurations modulaires (LLM, base de données, email, etc.).
- Fournit une interface unifiée pour valider et accéder aux paramètres.
- Intègre un système de validation et de gestion d'erreurs.

Modules
-------

.. automodule:: src.smart_watch.core.ConfigManager
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__, __call__
   :inherited-members:
   :show-inheritance:
