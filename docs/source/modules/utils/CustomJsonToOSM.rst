CustomJsonToOSM
===============

Ce module convertit les horaires d'ouverture du format JSON personnalisé de SmartWatch vers la spécification `opening_hours <https://wiki.openstreetmap.org/wiki/Key:opening_hours>`_ d'OpenStreetMap.

Fonctionnalités
---------------

- Conversion des horaires hebdomadaires avec compression des plages de jours (ex: Mo-Fr).
- Gestion des périodes spéciales : vacances scolaires, jours fériés (PH) et autres dates spécifiques.
- Analyse des descriptions de dates en français pour les convertir au format OSM.
- Traitement des créneaux horaires multiples pour une même journée.
- Gestion des occurrences pour les jours (ex: le 1er et 3ème mardi du mois).
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
