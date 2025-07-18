Logger
======

Fonctionnalités
---------------

Le module Logger fournit un système de logging unifié pour SmartWatch avec support de sorties multiples, formatage avancé et gestion des sections.  
Il propose une classe principale `SmartWatchLogger` et une fonction utilitaire `create_logger` pour instancier facilement un logger par module.

**Système de logging avancé :**

- Loggers nommés par module avec hiérarchie
- Support des sorties multiples (fichier, console, ou les deux)
- Formatage personnalisé avec timestamps et niveaux
- Rotation automatique des fichiers de log

**Niveaux de log :**

- Enumération `LogLevel` : DEBUG, INFO, WARNING, ERROR, CRITICAL
- Méthodes utilitaires : `debug()`, `info()`, `warning()`, `error()`, `critical()`
- Méthode `section()` pour délimiter les étapes importantes

**Configuration flexible :**

- Choix des sorties via paramètres (`file`, `console`)
- Répertoire de logs configurable avec création automatique
- Formatage des messages avec module, niveau et timestamp

Modules
-------

.. automodule:: src.smart_watch.core.Logger
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__, __call__
   :inherited-members:
   :show-inheritance: