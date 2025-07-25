================
Base de données
================

Tables
=======

La base de données comporte trois tables :

1.  **lieux**: Contient les informations de référence sur chaque lieu (piscine, mairie, médiathèque) issues de data.grandlyon.com.

2.  **executions**: Journalise chaque exécution du script principal. Elle permet de savoir quand le programme a tourné, avec quelle configuration de modèle de langage (LLM), et de suivre la consommation totale de CO2 pour chaque lot.

3.  **resultats_extraction**: C'est la table transactionnelle principale. Elle fait le lien entre un lieu et une exécution spécifique. Pour chaque URL traitée lors d'une exécution, cette table stocke toutes les données du pipeline : le statut de l'URL, les différentes étapes du traitement du markdown (brut, nettoyé, filtré), la sortie du LLM (JSON et OSM), le résultat de la comparaison avec les données de référence, et les éventuelles erreurs.

Diagramme
=========

.. code-block:: text

   +---------------------------+      +-------------------------------+      +------------------------------+
   |           lieux           |      |     resultats_extraction      |      |          executions          |
   +---------------------------+ 1--* +-------------------------------+ *--1 +------------------------------+
   | identifiant (PK)          |      | id_resultats_extraction (PK)  |      | id_executions (PK)           |
   | nom                       |      | lieu_id (FK)                  |      | date_execution               |
   | type_lieu                 |      | id_execution (FK)             |      | llm_modele                   |
   | url                       |      | statut_url                    |      | llm_fournisseur              |
   | horaires_data_gl          |      | code_http                     |      | llm_url                      |
   | horaires_data_gl_json     |      | message_url                   |      | llm_consommation_execution   |
   +---------------------------+      | markdown_brut                 |      +------------------------------+
                                      | markdown_nettoye              |
                                      | markdown_filtre               |
                                      | prompt_message                |
                                      | llm_consommation_requete      |
                                      | llm_horaires_json             |
                                      | llm_horaires_osm              |
                                      | horaires_identiques           |
                                      | differences_horaires          |
                                      | erreurs_pipeline              |
                                      +-------------------------------+

Détail des champs
=================

Table `lieux`
-------------

.. list-table::
   :widths: 25 15 60
   :header-rows: 1

   * - Champ
     - Type SQL
     - Description
   * - **identifiant** (PK)
     - TEXT
     - Identifiant unique du lieu (ex: "S1360"), issu de data.grandlyon.com.
   * - nom
     - TEXT
     - Nom complet du lieu (ex: "Piscine Garibaldi").
   * - type_lieu
     - TEXT
     - Catégorie du lieu (ex: "piscine", "mairie").
   * - url
     - TEXT
     - URL de la page web contenant les horaires à vérifier.
   * - horaires_data_gl
     - TEXT
     - Horaires de référence au format OSM `opening_hours` issus de data.grandlyon.com.
   * - horaires_data_gl_json
     - TEXT
     - Version JSON des horaires de référence, convertis par SmartWatch.

Table `executions`
------------------

.. list-table::
   :widths: 25 15 60
   :header-rows: 1

   * - Champ
     - Type SQL
     - Description
   * - **id_executions** (PK auto-increment)
     - INTEGER
     - Identifiant unique de l'exécution.
   * - date_execution
     - DATETIME
     - Date et heure du début de l'exécution.
   * - llm_modele
     - TEXT
     - Nom du modèle de langage utilisé (ex: "devstral").
   * - llm_fournisseur
     - TEXT
     - Fournisseur du LLM ("OPENAI", "MISTRAL").
   * - llm_url
     - TEXT
     - URL de base de l'API du LLM.
   * - llm_consommation_execution
     - FLOAT
     - Estimation totale des émissions de CO2 (en kg) pour l'ensemble des appels LLM de cette exécution.

Table `resultats_extraction`
----------------------------

.. list-table::
   :widths: 25 15 60
   :header-rows: 1

   * - Champ
     - Type SQL
     - Description
   * - **id_resultats_extraction** (PK auto-increment)
     - INTEGER
     - Identifiant unique du résultat.
   * - lieu_id (FK)
     - TEXT
     - Clé étrangère liant ce résultat à un lieu dans la table `lieux`.
   * - id_execution (FK)
     - INTEGER
     - Clé étrangère liant ce résultat à une exécution dans la table `executions`.
   * - statut_url
     - TEXT
     - Statut final du traitement de l'URL.
   * - code_http
     - INTEGER
     - Code de statut HTTP retourné par la requête sur l'URL (ex: 200, 404).
   * - message_url
     - TEXT
     - Message d'erreur associé au statut de l'URL.
   * - markdown_brut
     - TEXT
     - Contenu Markdown brut extrait de la page web.
   * - markdown_nettoye
     - TEXT
     - Markdown après une première passe de nettoyage (suppression des liens, etc.).
   * - markdown_filtre
     - TEXT
     - Markdown après filtrage sémantique pour ne garder que les parties pertinentes.
   * - prompt_message
     - TEXT
     - Le prompt complet envoyé au LLM.
   * - llm_consommation_requete
     - FLOAT
     - Estimation des émissions de CO2 (en kg) pour l'appel LLM de ce résultat.
   * - llm_horaires_json
     - TEXT
     - Les horaires extraits par le LLM, au format JSON.
   * - llm_horaires_osm
     - TEXT
     - Les horaires extraits par le LLM, convertis au format OSM `opening_hours`.
   * - horaires_identiques
     - BOOLEAN
     - `True` si les horaires extraits correspondent à ceux de référence, `False` sinon.
   * - differences_horaires
     - TEXT
     - Description textuelle des différences trouvées lors de la comparaison.
   * - erreurs_pipeline
     - TEXT
     - Journal des erreurs survenues à différentes étapes du pipeline pour ce résultat.
