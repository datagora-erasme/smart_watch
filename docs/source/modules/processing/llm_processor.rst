LLM Processor
=============

Fonctionnalités
---------------

Le LLMProcessor gère l'extraction d'horaires via modèles de langage avec structured outputs. Il utilise un pipeline d'enrichissement automatique et supporte plusieurs fournisseurs LLM.

**Support multi-providers :**

- OpenAI-compatible (OpenAI, LM Studio, Ollama, LiteLLM)
- Mistral API native avec support des tools/functions
- Détection automatique du fournisseur selon la configuration
- Adaptation des formats de requête par provider

**Structured Outputs :**

- Utilisation du schéma JSON `opening_hours_schema.json`
- Validation automatique de la structure retournée
- Gestion des erreurs de parsing avec fallback
- Support des formats OpenAI (response_format) et Mistral (tools)

**Pipeline d'enrichissement :**

- Utilisation prioritaire du `markdown_filtre` avec fallback
- Génération de prompts avec schéma JSON intégré
- Enrichissement automatique des mairies avec jours fériés français
- Conversion JSON → OSM via JsonToOsmConverter

**Gestion robuste :**

- Traitement séquentiel avec délais configurables entre appels
- Délais adaptatifs en cas d'erreur (progression géométrique)
- Traçabilité complète des prompts et réponses
- Accumulation des émissions CO2 avec reporting

**Enrichissement spécialisé :**

- Détection automatique des mairies par type_lieu
- Intégration des jours fériés français via API gouvernementale
- Enrichissement conditionnel selon le type d'établissement
- Préservation des horaires d'origine avec enrichissement

Modules
-------

.. automodule:: src.smart_watch.processing.llm_processor
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__, __call__
   :inherited-members:
   :show-inheritance: