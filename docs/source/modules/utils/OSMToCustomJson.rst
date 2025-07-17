OSMToCustomJson
===============

Ce module convertit les chaînes d'horaires `opening_hours <https://wiki.openstreetmap.org/wiki/Key:opening_hours>`_ d'OpenStreetMap en format JSON personnalisé, utilisé par SmartWatch.

Fonctionnalités
---------------

- Parsing des chaînes ``opening_hours`` complexes.
- Gestion des plages de jours (ex: Mo-Fr), des jours uniques et des jours avec occurrences (ex: Tu[1,3]).
- Reconnaissance des règles pour les dates spécifiques et les périodes de vacances.
- Identification des statuts "ouvert" (open) et "fermé" (off/closed).
- Reconstruction de la structure JSON complète, incluant les différentes périodes (semaine, vacances, jours fériés).

.. admonition:: Usage

   La classe ``OsmToJsonConverter`` est utilisée dans :

   - le module :doc:`database_processor <../processing/database_processor>`, pour convertir les horaires au format OSM provenant de data.grandlyon.com en JSON.

Module
-------

.. automodule:: src.smart_watch.utils.OSMToCustomJson
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__
   :show-inheritance:
