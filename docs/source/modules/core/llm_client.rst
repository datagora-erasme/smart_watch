LLM Client
==========

.. automodule:: src.smart_watch.core.LLMClient
   :members:
   :undoc-members:
   :show-inheritance:

Classes principales
===================

.. autoclass:: src.smart_watch.core.LLMClient.OpenAICompatibleClient
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: src.smart_watch.core.LLMClient.MistralClient
   :members:
   :undoc-members:
   :show-inheritance:

Fonctionnalités
===============

Le LLMClient fournit une abstraction unifiée pour interagir avec différents fournisseurs de modèles de langage :

**Fournisseurs supportés :**

- **OpenAI-compatible** : OpenAI, LM Studio, Ollama, LiteLLM, APIs locales
- **Mistral** : API native Mistral avec support des tools/functions

**Fonctionnalités communes :**

- Gestion automatique des timeouts et retry
- Support des structured outputs (JSON Schema)
- Calcul des embeddings pour le filtrage sémantique
- Session HTTP réutilisable pour optimiser les performances
- Gestion robuste des erreurs réseau et API

**Architecture adaptative :**

Le client s'adapte automatiquement selon le fournisseur :
- OpenAI : `response_format` pour structured outputs
- Mistral : `tools` et `tool_choice` pour structured outputs
- Embeddings : Endpoint `/embeddings` compatible OpenAI

Exemple d'utilisation
=====================

.. code-block:: python

   from src.smart_watch.core.LLMClient import OpenAICompatibleClient, MistralClient

   # Client OpenAI-compatible
   openai_client = OpenAICompatibleClient(
       api_key="sk-...",
       model="gpt-4",
       base_url="https://api.openai.com/v1",
       timeout=30
   )
   
   # Client Mistral
   mistral_client = MistralClient(
       api_key="...",
       model="mistral-large-latest",
       timeout=30
   )
   
   # Appel avec structured output
   response = openai_client.chat_completion(
       messages=[{"role": "user", "content": "Extraire les horaires..."}],
       response_format={"type": "json_object"},
       schema=json_schema
   )
   
   # Calcul d'embeddings
   embeddings = openai_client.get_embeddings(
       texts=["phrase 1", "phrase 2"],
       model="nomic-embed-text"
   )
