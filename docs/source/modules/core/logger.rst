Logger
======

Fonctionnalités
---------------

Le module Logger fournit un système de logging unifié pour SmartWatch avec support des sorties multiples, formatage avancé et gestion des sections. Il utilise une approche modulaire avec des loggers nommés et une configuration flexible.

**Système de logging avancé :**
- Loggers nommés par module avec hiérarchie
- Support des sorties multiples (fichier, console, ou les deux)
- Formatage personnalisé avec timestamps et niveaux colorés
- Rotation automatique des fichiers de log avec conservation

**Niveaux de log :**
- Support des niveaux standard (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Méthode section() pour délimiter les étapes importantes
- Formatage spécial pour les sections avec séparateurs visuels
- Gestion des logs par module avec filtrage possible

**Configuration flexible :**
- Choix des sorties via paramètre (file, console, both)
- Répertoire de logs configurable avec création automatique
- Formatage des messages avec module, niveau et timestamp
- Gestion des encodages pour compatibilité multiplateforme

Classes principales
-------------------

.. automodule:: src.smart_watch.core.Logger
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__, __call__
   :inherited-members:
   :show-inheritance: