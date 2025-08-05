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

Ces paramètres contrôlent la manière dont le contenu HTML (converti en Markdown) est filtré par embeddings pour n'en garder que les parties pertinentes.

*   ``SIMILARITY_THRESHOLD``: Seuil de similarité (entre 0.0 et 1.0) pour qu'une phrase soit considérée comme pertinente. (Défaut: 0.5)
*   ``CHUNK_SIZE``: Taille des chunks de texte pour le découpage du Markdown. (Défaut: 100)
*   ``CHUNK_OVERLAP``: Nombre de phrases qui se chevauchent entre les chunks. Cela permet de conserver le contexte entre les phrases. (Défaut: 15)
*   ``CONTEXT_WINDOW_SIZE``: Nombre de chunks de contexte à inclure avant et après une phrase pertinente. Cela permet de conserver le contexte autour des phrases extraites. (Défaut: 1)
*   ``MIN_CONTENT_LENGTH``: Longueur minimale (en caractères) du Markdown pour que le filtrage soit appliqué. Cela permet d'éviter de traiter des contenus déjà suffisamment courts. (Défaut: 1000)
*   ``REFERENCE_PHRASES``: Phrases de référence (séparées par ``;;``) utilisées pour identifier les sections pertinentes du Markdown. Ces phrases servent de guide pour le filtrage sémantique. 

Configuration des modèles d'embeddings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Configurez ici le modèle à utiliser pour le filtrage sémantique du contenu. Vous pouvez utiliser soit une API compatible OpenAI, soit l'API Mistral, indépendamment du LLM principal.

**Pour embeddings via API compatible OpenAI :**

*   ``EMBED_API_KEY_OPENAI``: Votre clé d'API pour les embeddings.
*   ``EMBED_BASE_URL_OPENAI``: L'URL de base de l'API (ex: ``http://localhost:1234/v1``).
*   ``EMBED_MODELE_OPENAI``: Le nom/identifiant du modèle à utiliser (ex: ``nomic-embed-text``).

**Pour embeddings via API Mistral :**

*   ``EMBED_API_KEY_MISTRAL``: Votre clé d'API Mistral pour les embeddings.
*   ``EMBED_MODELE_MISTRAL``: Le nom du modèle (ex: ``nomic-embed-text``).

**Pour embeddings locaux avec sentence-transformers :**

*   ``EMBED_MODELE_LOCAL``: Le nom du modèle à utiliser (ex: ``paraphrase-multilingual-MiniLM-L12-v2``).

Configuration du LLM
~~~~~~~~~~~~~~~~~~~~

Configurez ici le modèle de langage qui extraira les horaires.

*   ``LLM_TIMEOUT``: Temps maximum d'attente (en secondes) pour une réponse du LLM. (Défaut: 600)

**Pour un LLM compatible OpenAI (LM Studio, etc.) :**

*   ``LLM_API_KEY_OPENAI``: Votre clé d'API.
*   ``LLM_BASE_URL_OPENAI``: L'URL de base de l'API (ex: ``http://localhost:1234/v1``).
*   ``LLM_MODELE_OPENAI``: Le nom/identifiant du modèle à utiliser.

**Pour Mistral AI :**

*   ``LLM_API_KEY_MISTRAL``: Votre clé d'API Mistral.
*   ``LLM_MODELE_MISTRAL``: Le nom du modèle (ex: ``mistral-large-latest``).

.. note::
   Vous devez définir la clé API pour **un seul** fournisseur LLM. Si les deux sont définies, la configuration OpenAI sera prioritaire (cf. :py:meth:`smart_watch.processing.markdown_processor.MarkdownProcessor._init_embedding_client`)

Envoi de rapport par email
~~~~~~~~~~~~~~~~~~~~~~~~~~

Pour permettre l'envoi du rapport par email, complétez ces variables.

*   ``MAIL_EMETTEUR``: Adresse email de l'expéditeur.
*   ``MAIL_RECEPTEUR``: Adresse(s) email du ou des destinataires (séparées par une virgule si plusieurs).
*   ``SMTP_SERVER``: Adresse du serveur SMTP.
*   ``SMTP_PORT``: Port du serveur SMTP (ex: 465 pour SSL, 587 pour TLS).
*   ``SMTP_LOGIN``: Votre nom d'utilisateur SMTP.
*   ``SMTP_PASSWORD``: Votre mot de passe SMTP.
