Logger
======

Le module ``Logger`` fournit un système de logging unifié pour l'application.

.. admonition:: Usage

   Un logger est créé pour chaque module nécessitant de journaliser des informations, ce qui permet un suivi détaillé de l'exécution de l'application.

Fonctionnalités
---------------

- Gère des loggers nommés pour chaque module.
- Supporte les sorties vers la console et/ou des fichiers.
- Inclut la rotation automatique des fichiers de log pour éviter qu'ils ne deviennent trop volumineux.
- Propose différents niveaux de log (DEBUG, INFO, WARNING, ERROR, CRITICAL).

Modules
-------

.. automodule:: src.smart_watch.core.Logger
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__, __call__
   :inherited-members:
   :show-inheritance:
