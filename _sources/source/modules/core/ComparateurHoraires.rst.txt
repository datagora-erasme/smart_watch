Comparateur d'Horaires
======================

Le module ``ComparateurHoraires`` effectue une comparaison de deux structures d'horaires au format JSON personnalisé.

.. admonition:: Usage

   La classe ``HorairesComparator`` est utilisée dans :doc:`ComparisonProcessor <../processing/comparison_processor>` pour comparer les horaires extraits avec ceux présents en base de données.

Fonctionnalités
---------------

- Normalise les données avant la comparaison (tri des créneaux, gestion des occurrences spéciales).
- Compare les horaires par périodes distinctes (vacances scolaires, jours fériés).
- Détecte les différences précises : changements de statut, modification de créneaux, etc.
- Génère un rapport détaillé des différences constatées.

Modules
-------

.. automodule:: src.smart_watch.core.ComparateurHoraires
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__, __call__
   :inherited-members:
   :show-inheritance:
