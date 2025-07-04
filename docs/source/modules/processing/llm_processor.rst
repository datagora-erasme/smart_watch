LLM Processor
=============

.. automodule:: src.smart_watch.processing.llm_processor
   :members:
   :undoc-members:
   :show-inheritance:

Classes principales
==================

.. autoclass:: src.smart_watch.processing.llm_processor.LLMProcessor
   :members:
   :undoc-members:
   :show-inheritance:

Fonctionnalités
===============

Le LLMProcessor gère l'extraction d'horaires via modèles de langage :

**Support multi-providers :**
- **OpenAI-compatible** : OpenAI, LM Studio, Ollama, LiteLLM
- **Mistral** : API native avec tools/functions
- Détection automatique selon la configuration

**Structured Outputs :**
- Utilise le schéma JSON `opening_hours_schema.json`
- Formats adaptés par provider (response_format vs tools)
- Validation automatique de la structure retournée

**Pipeline d'enrichissement :**
1. Utilisation du `markdown_filtre` (ou fallback vers nettoyé/brut)
2. Génération du prompt avec schéma intégré
3. Appel LLM avec structured outputs
4. Enrichissement automatique jours fériés (mairies)
5. Conversion JSON → OSM via `OSMConverter`

**Gestion robuste :**
- Traitement séquentiel avec délais configurables
- Délais adaptatifs en cas d'erreur
- Traçabilité complète des prompts et réponses
- Enrichissement automatique des mairies avec jours fériés français

Exemple d'utilisation
=====================

.. code-block:: python

   from src.smart_watch.processing.llm_processor import LLMProcessor
   from src.smart_watch.core.ConfigManager import ConfigManager

   # Initialisation
   config = ConfigManager()
   processor = LLMProcessor(config, logger)
   
   # Traitement des extractions LLM
   stats = processor.process_llm_extractions(db_manager, execution_id)
   
   print(f"Extractions LLM: {stats.llm_successful}/{stats.llm_processed}")
