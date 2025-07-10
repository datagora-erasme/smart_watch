CSV to Polars
=============

.. automodule:: src.smart_watch.utils.CSVToPolars
   :members:
   :undoc-members:
   :show-inheritance:

Classes principales
===================

.. autoclass:: src.smart_watch.utils.CSVToPolars.CSVToPolars
   :members:
   :undoc-members:
   :show-inheritance:

Exemple d'utilisation
=====================

.. code-block:: python

   from src.smart_watch.utils.CSVToPolars import CSVToPolars

   # Chargement depuis URL
   loader = CSVToPolars(
       source="https://monsite.org/data.csv",
       separator=";",
       has_header=True
   )
   df = loader.load_csv()
   
   # Chargement depuis fichier local
   loader = CSVToPolars(source="./data/local.csv")
   df = loader.load_csv()
