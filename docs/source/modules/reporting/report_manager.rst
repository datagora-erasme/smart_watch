Report Manager
==============

.. automodule:: src.smart_watch.reporting.report_manager
   :members:
   :undoc-members:
   :show-inheritance:

Fonctionnalités
---------------

Le ReportManager orchestre la génération et l'envoi de rapports HTML avec création automatique d'archives ZIP contenant les logs. Il coordonne les différents composants de reporting et gère la configuration email.

**Génération de rapports :**
- Coordination avec GenererRapportHTML pour création des rapports
- Génération simultanée du rapport complet et du résumé email
- Intégration des métadonnées d'exécution et statistiques
- Gestion des informations du modèle LLM utilisé

**Création d'archives :**
- Création automatique de fichiers ZIP contenant les logs
- Inclusion des rapports HTML dans les archives
- Gestion des fichiers temporaires avec nettoyage automatique
- Compression optimisée pour l'envoi par email

**Envoi par email :**
- Utilisation du EmailSender pour l'envoi des rapports
- Pièces jointes automatiques (ZIP + HTML)
- Template email avec résumé intégré
- Gestion des erreurs d'envoi avec logging détaillé

**Nettoyage automatique :**
- Suppression des fichiers temporaires après envoi
- Gestion des erreurs de nettoyage
- Préservation des logs permanents
- Optimisation de l'espace disque

Classes principales
-------------------

.. autoclass:: src.smart_watch.reporting.report_manager.ReportManager
   :members:
   :undoc-members:
   :show-inheritance:
