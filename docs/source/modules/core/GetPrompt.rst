Générateur de Prompt
=====================

Le module ``GetPrompt`` génère des prompts optimisés pour l'extraction d'horaires à l'aide de modèles de langage (LLM).

Fonctionnalités
---------------

- Crée un prompt système définissant le rôle et les instructions pour le LLM.
- Intègre dynamiquement le schéma JSON attendu dans le prompt.
- Construit un prompt utilisateur avec le contexte spécifique du lieu à analyser (nom, contenu de la page, etc.).
- Fournit des instructions détaillées pour gérer les cas complexes (occurrences spéciales, dates, etc.).

.. admonition:: Usage

   Ce module est utilisé par le :doc:`LLMProcessor <../processing/llm_processor>` pour préparer la requête envoyée au LLM.

Modules
-------

.. automodule:: src.smart_watch.core.GetPrompt
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__, __call__
   :inherited-members:
   :show-inheritance:
