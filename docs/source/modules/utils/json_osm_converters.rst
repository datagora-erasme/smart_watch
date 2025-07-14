JSON/OSM Converters
===================

Convertisseurs bidirectionnels pour les formats JSON personnalisé et OpenStreetMap opening_hours.

Fonctionnalités
---------------

Les convertisseurs JSON/OSM permettent la conversion bidirectionnelle entre le format JSON personnalisé de SmartWatch et la spécification OpenStreetMap opening_hours. Ils gèrent les cas complexes d'horaires avec occurrences, jours spéciaux et périodes de vacances.

**Conversion JSON vers OSM :**
- Support des occurrences spéciales (1er mardi du mois, etc.)
- Gestion des périodes (hors vacances, vacances, jours fériés)
- Compression intelligente des plages de jours (Mo-Fr, Sa-Su)
- Détection des fermetures définitives

**Conversion OSM vers JSON :**
- Parsing robuste des chaînes opening_hours complexes
- Gestion des dates spécifiques et plages de dates
- Support des jours avec occurrences [1], [1,3]
- Reconstruction de la structure JSON complète

**Gestion des cas complexes :**
- Horaires avec multiples créneaux par jour
- Jours fériés avec dates précises (YYYY MMM DD)
- Périodes de vacances scolaires
- Établissements définitivement fermés

JSON vers OSM
-------------

.. automodule:: src.smart_watch.utils.CustomJsonToOSM
   :members:
   :undoc-members:
   :show-inheritance:

OSM vers JSON
-------------

.. automodule:: src.smart_watch.utils.OSMToCustomJson
   :members:
   :undoc-members:
   :show-inheritance:

Classes de données
------------------

.. autoclass:: src.smart_watch.utils.CustomJsonToOSM.TimeSlot
   :members:
   :undoc-members:

.. autoclass:: src.smart_watch.utils.CustomJsonToOSM.ConversionResult
   :members:
   :undoc-members:

.. autoclass:: src.smart_watch.utils.OSMToCustomJson.DaySchedule
   :members:
   :undoc-members:

.. autoclass:: src.smart_watch.utils.OSMToCustomJson.SpecialDate
   :members:
   :undoc-members:
