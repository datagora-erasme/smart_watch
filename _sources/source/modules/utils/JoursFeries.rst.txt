Jours Fériés
============

Le module JoursFeries récupère les jours fériés français officiels depuis l'API gouvernementale calendrier.api.gouv.fr.

Fonctionnalités
---------------

- Récupère les jours fériés français officiels via l'API gouvernementale
- Support des différentes zones, métropole par défaut
- Année configurable, fallback sur l'année courante

.. admonition:: Usage

   La fonction ``get_jours_feries`` est utilisée dans :
   
   - la classe ``LLMProcessor`` du module :doc:`llm_processor <../processing/llm_processor>`, pour enrichir les réponses LLM des mairies et les médiathèques avec les jours fériés à venir.

Modules
-------

.. automodule:: src.smart_watch.utils.JoursFeries
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__, __call__
   :inherited-members:
   :show-inheritance: