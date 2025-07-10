Markdown Cleaner
================

.. automodule:: src.smart_watch.utils.MarkdownCleaner
   :members:
   :undoc-members:
   :show-inheritance:

Classes principales
===================

.. autoclass:: src.smart_watch.utils.MarkdownCleaner.MarkdownCleaner
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: src.smart_watch.utils.MarkdownCleaner.CleaningStats
   :members:
   :undoc-members:

Exemple d'utilisation
=====================

.. code-block:: python

   from src.smart_watch.utils.MarkdownCleaner import MarkdownCleaner

   # Initialisation
   cleaner = MarkdownCleaner(config, logger)
   
   # Nettoyage d'un markdown
   cleaned_markdown, stats = cleaner.clean_markdown(raw_markdown)
   
   # Traitement par lot
   cleaner.process_markdown_cleaning(db_manager, execution_id)
