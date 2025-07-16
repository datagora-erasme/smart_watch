Notification Manager
====================

Fonctionnalités
---------------

Le NotificationManager orchestre la génération de rapports et leur envoi par email avec pièces jointes. Il coordonne les composants de reporting et gère la création d'archives compressées.

**Orchestration des rapports :**

- Génération automatique de rapports HTML via GenererRapportHTML
- Intégration des métadonnées d'exécution (modèle LLM, statistiques)
- Compression automatique des logs en archives ZIP
- Coordination avec EmailSender pour l'envoi

**Gestion des pièces jointes :**

- Création d'archives ZIP avec logs horodatés
- Validation de l'existence des fichiers avant attachement
- Gestion des erreurs de compression avec logging
- Nettoyage automatique des fichiers temporaires

**Cycle de vie des fichiers :**

- Génération de fichiers temporaires horodatés
- Suppression automatique après envoi réussi
- Gestion des erreurs de nettoyage
- Préservation des logs permanents

**Intégration système :**

- Utilisation de la configuration centralisée
- Coordination avec DatabaseManager pour les données
- Logging détaillé des opérations
- Gestion des erreurs avec continuation du processus

Modules
-------

.. automodule:: src.smart_watch.core.NotificationManager
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__, __call__
   :inherited-members:
   :show-inheritance: