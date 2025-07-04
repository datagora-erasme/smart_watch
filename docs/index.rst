.. SmartWatch documentation master file, created by
   sphinx-quickstart on Fri Jun 27 09:38:32 2025.

SmartWatch : Extracteur d'Horaires Intelligent
===============================================

.. image:: ../src/smart_watch/assets/images/logo_app.jpg
   :alt: Logo SmartWatch
   :align: center

**SmartWatch** est un pipeline de données complet conçu pour extraire, analyser et comparer les horaires d'ouverture de divers établissements (mairies, piscines, médiathèques) à partir de leurs sites web. Il utilise des modèles de langage pour interpréter le contenu et le comparer à des données de référence, puis génère et envoie par mail des rapports HTML interactifs.

.. note::
   **Version actuelle :** 2025-06 | **Licence :** GNU GPL v3.0

Vue d'ensemble
==============

.. toctree::
   :maxdepth: 1
   :caption: Guide utilisateur

   guide/installation
   guide/configuration
   guide/utilisation_docker
   guide/troubleshooting

Architecture et API
===================

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

Architecture du système
========================

.. automodule:: main
   :members: HoraireExtractor
   :show-inheritance:

Installation rapide
====================

.. code-block:: bash

   git clone https://github.com/datagora-erasme/smart_watch
   cd smart_watch
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt

Configuration minimale
=======================

Variables d'environnement dans ``.env`` :

.. code-block:: bash

   CSV_URL_HORAIRES="https://monsite.org/lieux.csv"
   API_KEY_OPENAI="sk-..."
   BASE_URL_OPENAI="https://api.openai.com/v1"
   MODELE_OPENAI="gpt-4"

Exemples d'utilisation
=======================

Pipeline complet
----------------

.. code-block:: python

   from main import HoraireExtractor

   # Initialisation et exécution
   extractor = HoraireExtractor()
   extractor.run()

Convertisseurs
--------------

.. code-block:: python

   from src.smart_watch.utils.CustomJsonToOSM import OSMConverter
   from src.smart_watch.utils.OSMToCustomJson import OSMToCustomConverter

   # JSON vers OSM
   converter = OSMConverter()
   osm_result = converter.convert_to_osm(json_data)

   # OSM vers JSON
   converter = OSMToCustomConverter()
   json_result = converter.convert_osm_string(osm_string, metadata)

Configuration
-------------

.. code-block:: python

   from src.smart_watch.core.ConfigManager import ConfigManager

   # Chargement de la configuration
   config = ConfigManager()
   if config.validate():
       print(f"LLM: {config.llm.fournisseur} - {config.llm.modele}")

Docker
------

.. code-block:: bash

   docker build -t smartwatch .
   docker run --env-file .env -v $(pwd)/data:/app/data smartwatch

Indices et tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
