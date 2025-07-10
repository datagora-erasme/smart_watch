.. SmartWatch documentation master file, created by
   sphinx-quickstart on Fri Jun 27 09:38:32 2025.

SmartWatch : extracteur d'horaires intelligent
===============================================

.. image:: ../src/smart_watch/assets/images/logo_app.jpg
   :alt: Logo SmartWatch
   :align: center
|
**SmartWatch** est un pipeline d'extraction de données conçu pour extraire, analyser, et comparer les horaires d'ouverture de divers établissements publics de la Métropole de Lyon (mairies, piscines, médiathèques), à partir de leurs sites web. Il utilise des modèles de langage pour interpréter le contenu et comparer les horaires d'ouverture extraits à des données de référence (issues de data.grandlyon.com), puis génère et envoie par mail des rapports HTML interactifs pour visualiser les résultats.

.. toctree::
   :maxdepth: 1
   :caption: Présentation du projet

   architecture/introduction
   architecture/stack
   architecture/diagramme
   architecture/modules

.. toctree::
   :maxdepth: 1
   :caption: Démarrage

   guide/installation
   guide/configuration
   guide/utilisation_docker

Architecture
=============

.. toctree::
   :maxdepth: 1
   :caption: Vue d'ensemble


   
.. toctree::
   :maxdepth: 1
   :caption: Modules Configuration
   
   source/modules/config/index

.. toctree::
   :maxdepth: 1
   :caption: Modules Core
   
   source/modules/core/index

.. toctree::
   :maxdepth: 1
   :caption: Modules Processing
   
   source/modules/processing/index

.. toctree::
   :maxdepth: 1
   :caption: Modules Utils
   
   source/modules/utils/index

.. toctree::
   :maxdepth: 1
   :caption: Reporting
   
   source/modules/reporting/index

.. toctree::
   :maxdepth: 1
   :caption: Modèles de données

   schemas/database
   schemas/json_formats
   schemas/osm_formats

Indices et tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. note::
   **Version actuelle :** 2025-06 | **Licence :** GNU GPL v3.0