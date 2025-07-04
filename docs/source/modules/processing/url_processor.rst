URL Processor
=============

.. automodule:: src.smart_watch.processing.url_processor
   :members:
   :undoc-members:
   :show-inheritance:

Classes principales
===================

.. autoclass:: src.smart_watch.processing.url_processor.URLProcessor
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: src.smart_watch.processing.url_processor.ProcessingStats
   :members:
   :undoc-members:

Fonctionnalités
===============

Le URLProcessor gère l'extraction parallèle du contenu web :

**Traitement parallèle :**
- Utilise `ThreadPoolExecutor` avec nombre de threads configurable
- Traitement par batch optimisé pour les mises à jour base de données
- Gestion robuste des timeouts et erreurs réseau

**Pipeline de conversion :**
1. Récupération HTML via `URLRetriever`
2. Conversion HTML → Markdown avec `HtmlToMarkdown`
3. Nettoyage et normalisation du contenu
4. Stockage du `markdown_brut` en base

**Gestion d'erreurs :**
- Codes HTTP détaillés (200, 404, timeout, etc.)
- Messages d'erreur explicites
- Traçabilité complète dans la chaîne d'erreurs

Exemple d'utilisation
=====================

.. code-block:: python

   from src.smart_watch.processing.url_processor import URLProcessor
   from src.smart_watch.core.ConfigManager import ConfigManager

   # Initialisation
   config = ConfigManager()
   processor = URLProcessor(config, logger)
   
   # Traitement des URLs en attente
   stats = processor.process_urls(db_manager, execution_id)
   
   print(f"URLs traitées: {stats.urls_successful}/{stats.urls_processed}")
