LLM Configuration
=================

Fonctionnalités
---------------

Le module LLMConfig gère la configuration des modèles de langage avec détection automatique du fournisseur selon les clés API disponibles. Il supporte les fournisseurs OpenAI-compatibles et Mistral.

**Détection automatique du fournisseur :**
- Priorité OpenAI/compatible si LLM_API_KEY_OPENAI présente
- Fallback vers Mistral si LLM_API_KEY_MISTRAL présente
- Configuration par défaut en cas d'erreur d'initialisation
- Validation des paramètres obligatoires

**Support multi-fournisseurs :**
- OpenAI et APIs compatibles (LM Studio, Ollama, LiteLLM)
- Mistral via API officielle
- URL de base configurable pour APIs locales
- Paramètres de température et timeout personnalisables

**Gestion robuste :**
- Configuration par défaut en cas d'erreur
- Logging des erreurs d'initialisation
- Validation des clés API et modèles
- Gestion des exceptions avec fallback

**Paramètres configurables :**
- Température (défaut: 0 pour cohérence)
- Timeout des requêtes (défaut: 30 secondes)
- Modèle spécifique par fournisseur
- URL de base pour déploiements locaux

Fournisseurs supportés
----------------------

- **OpenAI** et compatibles (LM Studio, Ollama, LiteLLM)
- **Mistral** via API officielle

Modules
-------

.. automodule:: src.smart_watch.config.llm_config
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__, __call__
   :inherited-members:
   :show-inheritance:
