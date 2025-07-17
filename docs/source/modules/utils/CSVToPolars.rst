CSV to Polars
=============

Le module CSVToPolars permet de charger dans un dataframe Polars des fichiers CSV locaux ou distants. Il inclut une détection automatique des séparateurs.

Fonctionnalités
---------------

- Chargement depuis une URL ou un fichier local, avec gestion des erreurs réseau.
- Détection automatique du séparateur (csv.Sniffer), avec fallback sur le point-virgule.
- Optimisations : troncature des lignes malformées et suppression des lignes vides.

.. admonition:: Usage

   La classe ``CSVToPolars`` est utilisée dans :

   - la fonction ``_update_horaires_lieux_depuis_gl`` du module :doc:`database_processor <../processing/database_processor>`, pour charger les CSV désignés par les variables ``CSV_URL_PISCINES``, ``CSV_URL_MAIRIES`` et ``CSV_URL_MEDIATHEQUES``.
   - la fonction ``setup_execution`` du module :doc:`setup_processor <../processing/setup_processor>`, pour charger le csv désigné par la varialbe ``CSV_URL_HORAIRES``

Modules
-------

.. automodule:: src.smart_watch.utils.CSVToPolars
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__, __call__
   :inherited-members:
   :show-inheritance:
