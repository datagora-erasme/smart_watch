Report Manager
==============

Le ``ReportManager`` est l'orchestrateur central du processus de reporting. Il coordonne la génération du rapport, l'archivage des logs et l'envoi final par e-mail.

Fonctionnalités
---------------

- **Orchestration Complète** : Sa méthode principale, ``generate_and_send_report``, exécute l'ensemble du pipeline de reporting.
- **Génération de Rapport** : Fait appel au module :doc:`html_generator` pour créer le rapport HTML détaillé ainsi qu'un résumé pour l'e-mail.
- **Archivage des Logs** : Crée une archive ``.zip`` contenant le fichier de log de l'application et la base de données SQLite pour faciliter le débogage et l'archivage.
- **Envoi par E-mail** : Utilise le module ``EmailSender`` pour envoyer un e-mail contenant le résumé du rapport, avec le rapport HTML complet et l'archive des logs en pièces jointes.
- **Nettoyage Automatique** : Supprime les fichiers temporaires (rapport HTML et archive zip) après leur envoi pour maintenir un environnement propre.

.. admonition:: Usage

   Une instance de ``ReportManager`` est créée dans le script principal de l'application. Elle est initialisée avec l'instance de ``ConfigManager`` pour accéder à toutes les configurations nécessaires (chemins, e-mail, etc.).

Modules
-------

.. automodule:: src.smart_watch.reporting.report_manager
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__
   :show-inheritance:
