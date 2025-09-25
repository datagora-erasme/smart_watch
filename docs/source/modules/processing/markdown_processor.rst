Markdown Processor
==================

Le ``MarkdownProcessor`` est une étape d'optimisation cruciale dans le pipeline. Son rôle est de filtrer le Markdown brut pour n'en conserver que les parties sémantiquement liées aux horaires d'ouverture, afin de réduire la taille et le coût des requêtes envoyées au LLM.

Fonctionnalités
---------------

- **Découpage du Texte** : Le texte peut être découpé en chunks de taille fixe ou en phrases en utilisant le sentencizer de NLTK, selon la configuration.
- **Filtrage Sémantique par Embeddings** : Le processeur utilise des modèles d'embeddings (locaux ou via une API comme Mistral/OpenAI) pour convertir des phrases de référence (ex: "nos horaires") et les segments du texte en vecteurs numériques.
- **Calcul de Similarité** : Il calcule la similarité cosinus entre les vecteurs de référence et ceux du texte pour identifier les segments les plus pertinents.
- **Sélection de Contenu** : Les segments de texte (chunks ou phrases) dont la similarité dépasse un seuil configurable sont conservés. Les segments adjacents (définis par la fenêtre de contexte) sont également inclus pour préserver le sens.
- **Mise à Jour de la Base de Données** : Le contenu filtré et réduit est sauvegardé dans la colonne ``markdown_filtre`` de la base de données via le :doc:`DatabaseProcessor <database_processor>`.
- **Suivi des Émissions CO2** : Il enregistre et accumule les émissions de CO2 estimées lors des appels aux APIs d'embeddings.

.. admonition:: Usage

   Ce processeur s'exécute après la récupération des URLs. Il prend en entrée le ``markdown_nettoye``, le filtre, et produit le ``markdown_filtre`` qui sera utilisé par le :doc:`LLMProcessor <llm_processor>` suivant.

Modules
-------

.. automodule:: src.smart_watch.processing.markdownprocessor
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__
   :show-inheritance:
