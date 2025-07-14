Processing Configuration
========================

.. automodule:: src.smart_watch.config.processing_config
   :members:
   :undoc-members:
   :show-inheritance:

Fonctionnalités
---------------

Le module ProcessingConfig configure les paramètres de traitement des URLs et du contenu markdown. Il gère la concurrence, les délais entre appels et les règles de nettoyage du contenu.

**Configuration du traitement parallèle :**
- Nombre de threads pour le traitement des URLs
- Délais entre les appels API pour éviter les limitations
- Délais d'attente en cas d'erreur avec progression géométrique
- Configuration des timeouts pour les requêtes HTTP

**Nettoyage du contenu :**
- Dictionnaire de remplacements de caractères pour le nettoyage markdown
- Patterns de suppression des éléments indésirables
- Règles de normalisation du contenu textuel

Classes principales
-------------------

.. autoclass:: src.smart_watch.config.processing_config.ProcessingConfig
   :members:
   :undoc-members:

.. autoclass:: src.smart_watch.config.processing_config.ProcessingConfigManager
   :members:
   :undoc-members:
   :show-inheritance:
   proc_config - ProcessingConfigManager()
   
   print(f"Threads: {proc_config.config.nb_threads_url}")
   print(f"Délai: {proc_config.config.delai_entre_appels}s")
