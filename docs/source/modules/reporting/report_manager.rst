Report Manager
==============

.. automodule:: src.smart_watch.reporting.report_manager
   :members:
   :undoc-members:
   :show-inheritance:

Classes principales
===================

.. autoclass:: src.smart_watch.reporting.report_manager.ReportManager
   :members:
   :undoc-members:
   :show-inheritance:

Fonctionnalités
===============

- Génération de rapports HTML avec statistiques complètes
- Création automatique de fichiers ZIP contenant les logs
- Envoi par email avec pièces jointes
- Nettoyage automatique des fichiers temporaires

Exemple d'utilisation
=====================

.. code-block:: python

   from src.smart_watch.reporting.report_manager import ReportManager

   # Initialisation
   report_manager = ReportManager(config, logger)
   
   # Génération et envoi
   report_manager.generate_and_send_report(processing_stats)
