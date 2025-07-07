=============
Configuration
=============

La configuration de **SmartWatch** s'effectue via un fichier ``.env`` situé à la racine du projet. Ce fichier centralise toutes les variables nécessaires au bon fonctionnement de l'application.

Création du fichier .env
------------------------

La méthode recommandée est de copier le modèle fourni :

.. code-block:: bash

   cp .env.model .env

Ensuite, ouvrez le fichier ``.env`` dans un éditeur de texte et modifiez les valeurs selon vos besoins.

Détail des variables
--------------------

Les variables sont regroupées par fonctionnalité.

Fichiers CSV
~~~~~~~~~~~~

Ces URLs pointent vers les fichiers de données utilisés par l'application.

*   ``CSV_URL_HORAIRES``: (Requis) URL du fichier CSV principal listant les établissements à vérifier. Format attendu : ``type_lieu;identifiant;nom;url``.
*   ``CSV_URL_PISCINES``, ``CSV_URL_MAIRIES``, ``CSV_URL_MEDIATHEQUES``: (Requis) URLs vers les fichiers de référence de data.grandlyon.com pour la comparaison des données.

Paramètres de traitement
~~~~~~~~~~~~~~~~~~~~~~~~

*   ``NB_THREADS_URL``: Nombre de threads pour télécharger le contenu des URLs en parallèle. (Défaut: 20)
*   ``LOG_LEVEL``: Niveau de verbosité des logs (DEBUG, INFO, WARNING, ERROR). (Défaut: DEBUG)

Filtrage sémantique du Markdown
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Ces paramètres contrôlent la manière dont le contenu HTML (converti en Markdown) est filtré pour n'en garder que les parties pertinentes.

*   ``SIMILARITY_THRESHOLD``: Seuil de similarité (entre 0.0 et 1.0) pour qu'une phrase soit considérée comme pertinente. (Défaut: 0.5)
*   ``CONTEXT_WINDOW``: Nombre de phrases de contexte à inclure avant et après une phrase pertinente. (Défaut: 1)
*   ``MIN_CONTENT_LENGTH``: Longueur minimale (en caractères) du Markdown pour que le filtrage soit appliqué. (Défaut: 1000)
*   ``REFERENCE_PHRASES``: Phrases de référence (séparées par ``;;``) utilisées pour trouver les sections d'horaires. (Défaut: "horaires d'ouverture et de fermeture")
*   ``EMBEDDING_MODEL``: Modèle d'embedding à utiliser. (Défaut: "nomic-embed-text")

Configuration du LLM
~~~~~~~~~~~~~~~~~~~~

Configurez ici le modèle de langage qui extraira les horaires.

*   ``LLM_TIMEOUT``: Temps maximum d'attente (en secondes) pour une réponse du LLM. (Défaut: 600)

**Pour un LLM compatible OpenAI (LM Studio, etc.) :**

*   ``API_KEY_OPENAI``: Votre clé d'API.
*   ``BASE_URL_OPENAI``: L'URL de base de l'API (ex: ``http://localhost:1234/v1``).
*   ``MODELE_OPENAI``: Le nom/identifiant du modèle à utiliser.

**Pour Mistral AI :**

*   ``API_KEY_MISTRAL``: Votre clé d'API Mistral.
*   ``MODELE_MISTRAL``: Le nom du modèle (ex: ``mistral-large-latest``).

.. note::
   Vous devez définir la clé API pour **un seul** fournisseur. Si les deux sont définies, la configuration OpenAI sera prioritaire.

Envoi de rapport par email
~~~~~~~~~~~~~~~~~~~~~~~~~~

Pour permettre l'envoi du rapport par email, complétez ces variables.

*   ``MAIL_EMETTEUR``: Adresse email de l'expéditeur.
*   ``MAIL_RECEPTEUR``: Adresse email du destinataire.
*   ``SMTP_SERVER``: Adresse du serveur SMTP.
*   ``SMTP_PORT``: Port du serveur SMTP (ex: 465 pour SSL, 587 pour TLS).
*   ``SMTP_LOGIN``: Votre nom d'utilisateur SMTP.
*   ``SMTP_PASSWORD``: Votre mot de passe SMTP.
