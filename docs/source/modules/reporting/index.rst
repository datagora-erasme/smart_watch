Vue d'ensemble
===============

- **ReportManager** : Orchestration de la génération et envoi des rapports
- **GenererRapportHTML** : Génération de rapports HTML avec templates Jinja2

Modules
========

Les modules Reporting gèrent la génération de rapports HTML interactifs et leur envoi par email.

.. toctree::
   :maxdepth: 1

   report_manager
   html_generator

Pipeline de reporting
====================

.. code-block:: text

   Données DB → Templates Jinja2 → HTML Interactif → Email + Pièces jointes

Fonctionnalités des rapports
============================

- **Rapports interactifs** : Tri, filtrage, recherche dans les données
- **Onglets multiples** : Vue d'ensemble + détails par statut
- **Statistiques visuelles** : Métriques de performance et classification en 4 statuts
- **Export automatique** : HTML + logs zippés par email
- **Templates Jinja2** : ReportTemplate.html (complet) + SimpleReportTemplate.html (email)

Classes de données utilisées
============================

.. autoclass:: src.smart_watch.processing.url_processor.ProcessingStats
   :members:
   :undoc-members:
