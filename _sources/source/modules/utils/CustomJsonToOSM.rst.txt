CustomJsonToOSM
===============

Ce module convertit les horaires d'ouverture du format JSON personnalisé de SmartWatch vers la spécification `opening_hours <https://wiki.openstreetmap.org/wiki/Key:opening_hours>`_ d'OpenStreetMap.

Fonctionnalités
---------------

- Conversion des horaires hebdomadaires compressés (ex: Mo-Fr).
- Prise en charge des périodes spéciales : vacances, jours fériés, dates spécifiques.
- Analyse des dates en français et anglais.
- Gestion des créneaux multiples et occurrences (ex: 1er mardi du mois).
- Détection des fermetures définitives.

.. admonition:: Usage

   La classe ``JsonToOsmConverter`` est utilisée dans :

   - la classe ``LLMProcessor`` du module :doc:`llm_processor <../processing/llm_processor>`, pour convertir le JSON structuré extrait par le LLM au format OSM.

Module
-------

.. automodule:: src.smart_watch.utils.CustomJsonToOSM
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__
   :show-inheritance:
