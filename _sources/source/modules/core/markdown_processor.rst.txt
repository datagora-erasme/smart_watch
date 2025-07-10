Markdown Processor
==================

.. automodule:: src.smart_watch.core.MarkdownProcessor
   :members:
   :undoc-members:
   :show-inheritance:

Classes principales
===================

.. autoclass:: src.smart_watch.core.MarkdownProcessor.MarkdownProcessor
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: src.smart_watch.core.MarkdownProcessor.ProcessingStats
   :members:
   :undoc-members:

Fonctionnalités
===============

Le MarkdownProcessor utilise des embeddings sémantiques pour filtrer intelligemment le contenu markdown et extraire uniquement les sections pertinentes aux horaires d'ouverture.

**Pipeline de filtrage :**

1. **Segmentation** : Division du contenu en phrases
2. **Embeddings** : Calcul des vecteurs sémantiques via API
3. **Similarité** : Comparaison avec phrases de référence  
4. **Filtrage** : Sélection des sections au-dessus du seuil
5. **Contexte** : Ajout de phrases adjacentes pour préserver le sens

**Configuration :**

- Modèle d'embeddings : `nomic-embed-text` via API compatible OpenAI
- Seuil de similarité configurable (0.0 à 1.0)
- Fenêtre de contexte autour des phrases pertinentes
- Phrases de référence personnalisables

Exemple d'utilisation
=====================

.. code-block:: python

   from src.smart_watch.core.MarkdownProcessor import MarkdownProcessor
   from src.smart_watch.core.ConfigManager import ConfigManager

   # Initialisation
   config = ConfigManager()
   processor = MarkdownProcessor(config, logger)
   
   # Traitement par lot
   stats = processor.process_markdown_filtering(db_manager, execution_id)
   
   # Traitement d'un contenu spécifique
   markdown_filtre = processor._filter_single_markdown(
       markdown_content="Contenu à filtrer...",
       nom="Piscine Municipale",
       type_lieu="piscine"
   )
