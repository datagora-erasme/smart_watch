Modules Reporting
=================

Fonctionnalités
===============

Les modules Reporting orchestrent la génération de rapports HTML interactifs et sophistiqués avec envoi automatique par email. Ils transforment les données de la base SQLite en visualisations riches et exploitables.

**Génération de rapports :**
- Templates Jinja2 pour rapports HTML complets et résumés email
- Classification intelligente des résultats en 4 statuts (succès, différences, erreurs d'accès, erreurs d'extraction)
- Extraction optimisée depuis base SQLite avec jointures et agrégations
- Intégration des métadonnées d'exécution (modèle LLM, émissions CO2, statistiques)

**Interactivité avancée :**
- Tri et filtrage dynamique par JavaScript intégré
- Modals pour visualisation des données JSON/OSM complètes
- Recherche dans les URLs et noms d'établissements
- Onglets multiples avec vue d'ensemble et détails par statut

**Archivage et diffusion :**
- Compression automatique des logs en archives ZIP horodatées
- Envoi par email avec pièces jointes multiples
- Gestion des fichiers temporaires avec nettoyage automatique
- Coordination avec EmailSender pour protocoles SMTP multiples

**Traçabilité complète :**
- Chaîne de traitement markdown_brut → markdown_nettoye → markdown_filtre
- Métriques de performance et émissions CO2 par requête
- Statistiques consolidées par type de lieu et code HTTP
- Historique des erreurs avec timestamps et catégorisation

Vue d'ensemble
===============

- **ReportManager** : Orchestration de la génération et envoi des rapports
- **GenererRapportHTML** : Génération de rapports HTML avec templates Jinja2

Modules
========

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
