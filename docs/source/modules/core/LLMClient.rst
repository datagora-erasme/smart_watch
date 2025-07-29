Client LLM
==========

Le module ``LLMClient`` fournit une interface unifiée pour interagir avec différents fournisseurs de modèles de langage (LLM).

Fonctionnalités
---------------

- Supporte les API compatibles OpenAI (OpenAI, Ollama, etc.) et l'API native de Mistral.
- Gère les appels aux LLM pour l'extraction de données structurées (JSON).
- Intègre `CodeCarbon` pour mesurer l'empreinte carbone de chaque requête.
- Gère les erreurs de communication et les re-essais.

.. admonition:: Usage

   Le ``LLMClient`` est utilisé par le :doc:`LLMProcessor <../processing/llm_processor>` pour communiquer avec le modèle de langage configuré.

Modules
-------

.. automodule:: src.smart_watch.core.LLMClient
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__, __call__
   :inherited-members:
   :show-inheritance:
