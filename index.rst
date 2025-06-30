.. SmartWatch documentation master file, created by
   sphinx-quickstart on Fri Jun 27 09:38:32 2025.

SmartWatch documentation
========================

Bienvenue dans la documentation du projet **SmartWatch**.

Ce projet permet l'extraction, la comparaison et la génération de rapports sur les horaires d'ouverture de lieux à partir de données issues de différentes sources (CSV, LLM, OSM, etc.).


Présentation
============

SmartWatch automatise :
- Le téléchargement et la normalisation de données d'horaires de lieux publics.
- L'extraction d'horaires via LLM (OpenAI/Mistral).
- La comparaison avec des horaires de référence (OSM/data.grandlyon.com).
- La génération de rapports HTML interactifs.
- L'envoi automatique de rapports par email.

.. toctree::
   :maxdepth: 2
   :caption: Guide utilisateur

   installation
   usage

.. toctree::
   :maxdepth: 2
   :caption: Référence API

   modules
   core
   assets
   utils

.. toctree::
   :maxdepth: 1
   :caption: Annexes

   schema_bdd
   model

Utilisation avec Docker
======================

Pour lancer le projet dans un conteneur Docker :

.. code-block:: bash

   docker build -t smartwatch .
   docker run --env-file .env -v $(pwd)/data:/app/data smartwatch

- Place ton fichier `.env` à la racine du projet.
- Les résultats et données seront accessibles dans le dossier `data/` du projet.

Indices et tables
=================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

