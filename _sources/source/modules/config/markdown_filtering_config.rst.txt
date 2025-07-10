Markdown Filtering Configuration
================================

.. automodule:: src.smart_watch.config.markdown_filtering_config
   :members:
   :undoc-members:
   :show-inheritance:

Classes principales
===================

.. autoclass:: src.smart_watch.config.markdown_filtering_config.MarkdownFilteringConfig
   :members:
   :undoc-members:

.. autoclass:: src.smart_watch.config.markdown_filtering_config.MarkdownFilteringConfigManager
   :members:
   :undoc-members:
   :show-inheritance:

Fonctionnalités
===============

- Configuration du modèle d'embeddings (nomic-embed-text)
- Seuil de similarité pour le filtrage sémantique
- Fenêtre de contexte autour des phrases pertinentes
- Phrases de référence pour identifier les sections d'horaires

Exemple d'utilisation
=====================

.. code-block:: python

   from src.smart_watch.config.markdown_filtering_config import MarkdownFilteringConfigManager

   # Initialisation
   md_config = MarkdownFilteringConfigManager()
   
   print(f"Modèle: {md_config.config.embedding_model}")
   print(f"Seuil: {md_config.config.similarity_threshold}")
   print(f"Phrases: {md_config.config.reference_phrases}")
