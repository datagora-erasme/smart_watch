.. |br| raw:: html

   <br />

.. _choosing_embeddings:

#####################
Choix des embeddings
#####################

Le choix du modèle d'embeddings est un élément crucial pour la performance et l'efficacité du filtrage sémantique dans l'application. Cette page vous guide pour sélectionner le modèle le plus adapté à votre cas d'usage, en fonction de votre environnement d'exécution (Docker ou ligne de commande) et de vos contraintes matérielles.

Tableau de compatibilité des modèles
=====================================

Le tableau ci-dessous résume les modèles d'embedding recommandés, leur compatibilité et les réglages associés.

.. list-table::
   :header-rows: 1
   :widths: 20 40 15 10 15

   * - Fournisseur
     - Modèle
     - Seuil de |br| similarité |br| conseillé
     - CLI
     - Docker
   * - **Local**
     - ``jinaai/jina-embeddings-v3``
     - 0.5
     - Recommandé
     - Consommation |br| RAM élevée
   * - 
     - ``sentence-transformers/`` |br| ``paraphrase-multilingual-mpnet-base-v2``
     - 0.6 - 0.8
     - Oui
     - Oui
   * - 
     - ``sentence-transformers/`` |br| ``paraphrase-multilingual-MiniLM-L12-v2``
     - 0.6 - 0.8
     - Oui
     - Oui
   * - **Compatible OpenAI**
     - ``nomic-embed-text``
     - 0.6 - 0.8
     - Oui
     - Oui
   * - **Mistral**
     - ``mistral-embed``
     - 0.6 - 0.8
     - Oui
     - Oui

.. note::
   Le modèle ``jinaai/jina-embeddings-v3`` est le plus performant mais aussi le plus gourmand en ressources. Il est donc recommandé de l'utiliser en local sur une machine disposant de suffisamment de mémoire RAM. Pour une utilisation avec Docker, les modèles de la série ``sentence-transformers`` sont plus adaptés.

Variables d'environnement
=========================

Activez le modèle d'embedding de votre choix en configurant les variables d'environnement appropriées dans votre fichier ``.env``. Le tableau ci-dessous récapitule les variables à définir selon le fournisseur choisi. Désactivez les variables ``EMBED_API_KEY_*`` non utilisées en les commentant ou en les supprimant.

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Fournisseur
     - Variables
   * - **Local**
     - - ``EMBED_MODELE_LOCAL``
   * - **Compatible OpenAI**
     - - ``EMBED_API_KEY_OPENAI``
       - ``EMBED_BASE_URL_OPENAI``
       - ``EMBED_MODELE_OPENAI``
   * - **Mistral**
     - - ``EMBED_API_KEY_MISTRAL``
       - ``EMBED_MODELE_MISTRAL``

Utilisation de ``fastembed`` en local
=====================================

Lorsque vous utilisez un modèle d'embedding local, l'application s'appuie sur la bibliothèque ``fastembed`` pour gérer le calcul des embeddings. Afin d'optimiser les performances sans surcharger le système, ``fastembed`` est configuré pour utiliser un quart des cœurs de processeur (CPU) disponibles, avec un minimum d'un thread.

Cette configuration permet de garantir un traitement efficace des textes tout en laissant suffisamment de ressources pour les autres processus de l'application.

Comment configurer votre modèle
================================

Pour sélectionner le modèle d'embedding que vous souhaitez utiliser, vous devez définir les variables d'environnement correspondantes dans votre fichier ``.env``. Vous trouverez des exemples et des instructions détaillées dans la section :ref:`configuration` de la documentation.
