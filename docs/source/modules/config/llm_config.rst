LLM Configuration
=================

.. automodule:: src.smart_watch.config.llm_config
   :members:
   :undoc-members:
   :show-inheritance:

Classes principales
===================

.. autoclass:: src.smart_watch.config.llm_config.LLMConfig
   :members:
   :undoc-members:

.. autoclass:: src.smart_watch.config.llm_config.LLMConfigManager
   :members:
   :undoc-members:
   :show-inheritance:

Fournisseurs supportés
======================

- **OpenAI** et compatibles (LM Studio, Ollama, LiteLLM)
- **Mistral** via API officielle

Exemple d'utilisation
=====================

.. code-block:: python

   from src.smart_watch.config.llm_config import LLMConfigManager

   # Initialisation
   llm_config = LLMConfigManager()
   
   # Accès aux paramètres
   print(f"Fournisseur: {llm_config.config.fournisseur}")
   print(f"Modèle: {llm_config.config.modele}")
   print(f"URL: {llm_config.config.base_url}")
