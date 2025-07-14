Markdown Filtering Configuration
================================

.. automodule:: src.smart_watch.config.markdown_filtering_config
   :members:
   :undoc-members:
   :show-inheritance:

Fonctionnalités
---------------

Le module MarkdownFilteringConfig configure le filtrage sémantique du contenu markdown via des embeddings. Il gère les paramètres pour les modèles d'embeddings OpenAI et Mistral, ainsi que les seuils de similarité et fenêtres de contexte.

**Configuration des embeddings :**
- Support des API OpenAI compatibles (Ollama, LM Studio) et Mistral
- Paramètres des modèles d'embeddings (par défaut : nomic-embed-text)
- Clés API et URLs de base configurables
- Détection automatique du fournisseur selon les clés disponibles

**Paramètres de filtrage :**
- Seuil de similarité pour la pertinence des phrases (0.0 à 1.0)
- Fenêtre de contexte autour des phrases pertinentes
- Taille minimale du contenu pour déclencher le filtrage
- Phrases de référence configurables pour identifier les sections d'horaires

**Logique de priorisation :**
- Mistral prioritaire si clé API disponible
- Fallback vers OpenAI si seule cette clé est configurée
- Validation des paramètres et URL de base requises

Classes principales
-------------------

.. autoclass:: src.smart_watch.config.markdown_filtering_config.MarkdownFilteringConfig
   :members:
   :undoc-members:

.. autoclass:: src.smart_watch.config.markdown_filtering_config.MarkdownFilteringConfigManager
   :members:
   :undoc-members:
   :show-inheritance:
