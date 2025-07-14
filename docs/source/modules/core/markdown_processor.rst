Markdown Processor
==================

.. automodule:: src.smart_watch.core.MarkdownProcessor
   :members:
   :undoc-members:
   :show-inheritance:

Fonctionnalités
---------------

Le MarkdownProcessor utilise des embeddings sémantiques pour filtrer intelligemment le contenu markdown et extraire uniquement les sections pertinentes aux horaires d'ouverture. Il optimise les appels LLM en réduisant la taille des prompts.

**Filtrage sémantique :**
- Segmentation du contenu en phrases avec patterns configurables
- Calcul d'embeddings via API OpenAI/Mistral compatibles
- Comparaison de similarité cosinus avec phrases de référence
- Sélection des sections au-dessus du seuil de pertinence

**Optimisation des embeddings :**
- Pré-calcul des embeddings de référence une seule fois par exécution
- Réutilisation des embeddings pour tous les documents
- Accumulation des émissions CO2 pour reporting global
- Gestion des erreurs d'API avec fallback vers contenu original

**Enrichissement contextuel :**
- Fenêtre de contexte autour des phrases pertinentes
- Préservation du sens avec phrases adjacentes
- Reconstruction du contenu filtré avec ponctuation
- Validation de la longueur minimale avant filtrage

**Gestion d'erreurs :**
- Fallback vers markdown nettoyé en cas d'erreur
- Traçabilité des erreurs dans la chaîne pipeline
- Logging détaillé des opérations et statistiques
- Mise à jour des émissions CO2 en base de données

Classes principales
-------------------

.. autoclass:: src.smart_watch.core.MarkdownProcessor.MarkdownProcessor
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: src.smart_watch.core.MarkdownProcessor.ProcessingStats
   :members:
   :undoc-members:
   # Initialisation
   config - ConfigManager()
   processor - MarkdownProcessor(config, logger)
   
   # Traitement par lot
   stats - processor.process_markdown_filtering(db_manager, execution_id)
   
   # Traitement d'un contenu spécifique
   markdown_filtre - processor._filter_single_markdown(
       markdown_content-"Contenu à filtrer...",
       nom-"Piscine Municipale",
       type_lieu-"piscine"
   )
