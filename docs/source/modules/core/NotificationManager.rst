Gestionnaire de Notifications
=============================

Le module ``NotificationManager`` orchestre la génération de rapports et leur envoi par email.

Fonctionnalités
---------------

- Coordonne la génération des rapports d'analyse au format HTML.
- Compresse les fichiers de log dans une archive ZIP.
- Utilise le module `EnvoyerMail` pour expédier le rapport avec les logs en pièce jointe.
- Gère le cycle de vie des fichiers temporaires (création, nettoyage).

.. admonition:: Usage

   Le ``NotificationManager`` est appelé à la fin du pipeline de traitement pour notifier les utilisateurs des résultats.

Modules
-------

.. automodule:: src.smart_watch.core.NotificationManager
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__, __call__
   :inherited-members:
   :show-inheritance:
