Processing Configuration
========================

.. automodule:: src.smart_watch.config.processing_config
   :members:
   :undoc-members:
   :show-inheritance:

Classes principales
===================

.. autoclass:: src.smart_watch.config.processing_config.ProcessingConfig
   :members:
   :undoc-members:

.. autoclass:: src.smart_watch.config.processing_config.ProcessingConfigManager
   :members:
   :undoc-members:
   :show-inheritance:

Fonctionnalités
===============

- Configuration du nombre de threads pour le traitement des URLs
- Délais entre les appels et en cas d'erreur
- Remplacements de caractères pour le nettoyage markdown

Exemple d'utilisation
=====================

.. code-block:: python

   from src.smart_watch.config.processing_config import ProcessingConfigManager

   # Initialisation
   proc_config = ProcessingConfigManager()
   
   print(f"Threads: {proc_config.config.nb_threads_url}")
   print(f"Délai: {proc_config.config.delai_entre_appels}s")
