LLM Configuration
=================

Le module ``LLMConfigManager`` gère la configuration des modèles de langage (LLM). Sa principale caractéristique est la détection automatique du fournisseur de services (OpenAI, Mistral, ou un modèle local) en fonction des variables d'environnement disponibles.

.. admonition:: Usage

   ``LLMConfigManager`` est instancié par le :doc:`ConfigManager <../core/ConfigManager>` central. L'application accède à la configuration via ``ConfigManager.llm``, qui contient une instance du dataclass ``LLMConfig``.

Fonctionnalités
---------------

- **Détection du fournisseur** : le gestionnaire sélectionne le fournisseur à utiliser selon la présence des clés d'API dans l'environnement, avec la priorité suivante :
    1. **OpenAI** (ou compatible) si ``LLM_API_KEY_OPENAI`` est définie.
    2. **Mistral** si ``LLM_API_KEY_MISTRAL`` est définie.
    3. **Modèle Local** si ``EMBED_MODELE_LOCAL`` est défini.
- **Configuration** : permet de définir le modèle et le timeout des requêtes via des variables d'environnement.
- **Configuration de secours** : en cas d'échec de l'initialisation, une configuration par défaut utilisant un modèle local est chargée pour garantir la résilience du système.
- **Validation** : la méthode ``validate`` adapte ses vérifications au fournisseur sélectionné. Par exemple, une clé d'API n'est requise que pour les fournisseurs distants. Elle valide également la plage des valeurs pour la température et le timeout.

Modules
-------

.. automodule:: src.smart_watch.config.llm_config
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__
   :show-inheritance:
