LLM Processor
=============

Le ``LLMProcessor`` est le cœur de l'extraction de données intelligentes. Il prend le Markdown filtré, le soumet à un Modèle de Langage (LLM) pour en extraire des horaires structurés, puis enrichit et transforme ces données.

Fonctionnalités
---------------

- **Extraction par LLM** : Construit un prompt détaillé incluant le Markdown filtré et un schéma JSON, puis l'envoie à un LLM (OpenAI ou Mistral) pour obtenir des horaires au format JSON structuré.
- **Enrichissement des Données** : Post-traite la réponse JSON du LLM pour :
    - Nettoyer les horaires spécifiques correspondant à des dates passées.
    - Enrichir les horaires des mairies et bibliothèques avec les jours fériés français à venir.
- **Conversion au Format OSM** : Utilise l'utilitaire ``JsonToOsmConverter`` pour transformer la réponse JSON finale en une chaîne de caractères au format standard `opening_hours`.
- **Mise à Jour de la Base de Données** : Sauvegarde le prompt, le JSON final, la chaîne OSM et les émissions de CO2 estimées dans la base de données via le :doc:`DatabaseProcessor <database_processor>`.

.. admonition:: Usage

   Ce processeur s'exécute après le filtrage du Markdown. Il constitue l'étape la plus coûteuse en temps et en ressources. Le résultat de son traitement (le JSON et l'OSM) est ensuite utilisé par le :doc:`ComparisonProcessor <comparison_processor>`.

Modules
-------

.. automodule:: src.smart_watch.processing.llmprocessor
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__
   :show-inheritance:
