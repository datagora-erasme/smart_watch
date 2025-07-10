Jours Fériés
============

.. automodule:: src.smart_watch.utils.JoursFeries
   :members:
   :undoc-members:
   :show-inheritance:

Fonctionnalités
===============

Le module JoursFeries enrichit automatiquement les horaires des mairies avec les jours fériés français officiels.

Exemple d'utilisation
=====================

.. code-block:: python

   from src.smart_watch.utils.JoursFeries import enrichir_horaires_mairie

   # Enrichissement automatique
   horaires_json = {...}  # Horaires d'une mairie
   horaires_enrichis = enrichir_horaires_mairie(horaires_json)
   
   # Les jours fériés sont automatiquement ajoutés
   print(horaires_enrichis["horaires_ouverture"]["periodes"]["jours_feries"])
