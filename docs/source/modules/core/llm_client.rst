LLM Client
==========

.. automodule:: src.smart_watch.core.LLMClient
   :members:
   :undoc-members:
   :show-inheritance:

Fonctionnalités
---------------

Le module LLMClient fournit une abstraction unifiée pour interagir avec différents fournisseurs de modèles de langage. Il gère les appels API avec mesure d'émissions CO2, structured outputs et calcul d'embeddings.

**Architecture multi-provider :**
- Support OpenAI-compatible (OpenAI, Ollama, LM Studio, LiteLLM)
- Client Mistral natif avec support des tools/functions
- Session HTTP réutilisable pour optimiser les performances
- Gestion des timeouts et retry configurable

**Structured Outputs :**
- Adaptation automatique selon le fournisseur (response_format vs tools)
- Validation des schémas JSON avec strict mode
- Support des tools/functions pour Mistral
- Gestion des erreurs de parsing structuré

**Mesure d'émissions CO2 :**
- Intégration CodeCarbon pour mesurer les émissions
- Tracking isolé par requête avec EmissionsTracker
- Accumulation des émissions pour reporting global
- Support des embeddings et chat completions

**Gestion d'erreurs :**
- Codes d'erreur HTTP détaillés (401, 429, timeout)
- Messages d'erreur explicites par provider
- Décorateurs de gestion d'erreurs avec fallback
- Logging détaillé pour debugging

Modules
-------

.. automodule:: src.smart_watch.core.LLMClient
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__, __call__
   :inherited-members:
   :show-inheritance:
