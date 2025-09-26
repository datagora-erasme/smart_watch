===============
Stack technique
===============

Voici un aperçu des technologies employées.

Langage du projet
=================

`Python <https://www.python.org/>`__
    Langage unique du projet.

Framework et bibliothèques principales
======================================

Traitement de données
---------------------

`Polars <https://www.pola.rs/>`__
    Pour le chargement et la manipulation de données tabulaires.

`SQLAlchemy <https://www.sqlalchemy.org/>`__
    Pour la gestion de la base de données SQLite.

`SQLite <https://www.sqlite.org/>`__
    Pour stocker les résultats d'extraction et les métadonnées.

Web scraping et traitement HTML
-------------------------------

`Inscriptis <https://github.com/weblyzard/inscriptis>`__
    Une bibliothèque Python de conversion HTML vers texte, avec un client en ligne de commande et un service Web.

`Requests <https://requests.readthedocs.io/>`__
    Bibliothèque HTTP pour récupérer le contenu des pages web.

`html2text <https://github.com/Alir3z4/html2text>`__
    Conversion du HTML en Markdown pour faciliter le traitement par les modèles de langage.

Intelligence artificielle
-------------------------

`OpenAI API <https://platform.openai.com/docs/api-reference>`__
    Interface standardisée pour communiquer avec les modèles de langage.

`Mistral AI <https://docs.mistral.ai/>`__
    Proposé en tant qu'alternative aux interfaces compatibles OpenAI. Utilise la librairie `mistralai` native.

`Embeddings <https://platform.openai.com/docs/guides/embeddings>`__
    Les embeddings sont utilisés pour filtrer le contenu Markdown de manière sémantique. L'application peut fonctionner avec un modèle local via ``fast-embed``, ou avec un modèle distant via une API (compatible OpenAI ou Mistral). Pour un guide détaillé sur le choix du modèle le plus adapté, consultez la page :doc:`/guide/choosing_embeddings`.

Configuration et environnement
------------------------------

`python-dotenv <https://pypi.org/project/python-dotenv/>`__
    Gestion des variables d'environnement via fichiers ``.env`` pour une configuration flexible.

`Pydantic <https://docs.pydantic.dev/>`__
`Dataclasses <https://docs.python.org/3/library/dataclasses.html>`__
    Validation et typage des données.

Parallélisme et performance
---------------------------

`ThreadPoolExecutor <https://docs.python.org/3/library/concurrent.futures.html>`__
    Traitement parallèle des URLs pour accélérer la récupération du contenu web.

Logging et monitoring
---------------------

`Logging standard Python <https://docs.python.org/3/library/logging.html>`__
    Système de journalisation centralisé avec rotation automatique des fichiers.

Gestion d'erreurs centralisée
    Capture et traitement uniforme des exceptions avec contexte détaillé.

`CodeCarbon <https://mlco2.github.io/codecarbon/>`__
    Mesure les émissions de CO2 des appels aux modèles de langage pour un suivi de l'impact environnemental.

Communication
-------------

`SMTP (smtplib) <https://docs.python.org/3/library/smtplib.html>`__
    Envoi automatique des rapports par email avec support SSL/TLS.

`Jinja2 <https://jinja.palletsprojects.com/>`__
    Moteur de templates pour la génération de rapports HTML personnalisés.

Déploiement
===========

`Docker <https://www.docker.com/>`__
    Conteneurisation pour un déploiement simplifié et reproductible.

`GitHub Actions <https://github.com/features/actions>`__
    CI/CD pour le déploiement Docker et de la documentation.

`Sphinx <https://www.sphinx-doc.org/>`__
`Read the Docs Theme <https://sphinx-rtd-theme.readthedocs.io/>`__
    Génération automatique de documentation technique à partir du code.

Formats de données
==================

`CSV <https://fr.wikipedia.org/wiki/Comma-separated_values>`__
    Format d'entrée pour les listes d'établissements et données de référence.

`JSON <https://www.json.org/json-fr.html>`__
    Format intermédiaire pour les horaires extraits par les LLMs.

`OSM (OpenStreetMap) <https://wiki.openstreetmap.org/wiki/Key:opening_hours>`__
    Format de sortie standardisé pour les horaires d'ouverture.

`HTML <https://developer.mozilla.org/fr/docs/Web/HTML>`__
    Format de rapport final avec visualisations interactives.
