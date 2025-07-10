JSON/OSM Converters
===================

Convertisseurs bidirectionnels pour les formats JSON personnalisé et OpenStreetMap.

JSON vers OSM
=============

.. automodule:: src.smart_watch.utils.CustomJsonToOSM
   :members:
   :undoc-members:
   :show-inheritance:

OSM vers JSON
=============

.. automodule:: src.smart_watch.utils.OSMToCustomJson
   :members:
   :undoc-members:
   :show-inheritance:

Classes de données
==================

.. autoclass:: src.smart_watch.utils.CustomJsonToOSM.TimeSlot
   :members:
   :undoc-members:

.. autoclass:: src.smart_watch.utils.CustomJsonToOSM.ConversionResult
   :members:
   :undoc-members:

Exemples d'utilisation
======================

.. code-block:: python

   from src.smart_watch.utils.CustomJsonToOSM import JsonToOsmConverter
   from src.smart_watch.utils.OSMToCustomJson import OsmToJsonConverter

   # JSON vers OSM
   json_data = {"horaires_ouverture": {...}}
   json_converter = JsonToOsmConverter()
   osm_result = json_converter.convert_to_osm(json_data)
   print(osm_result.osm_periods)

   # OSM vers JSON
   osm_string = "Mo-Fr 09:00-17:00; Sa 09:00-12:00"
   osm_converter = OsmToJsonConverter()
   json_result = osm_converter.convert_osm_string(osm_string, metadata)
