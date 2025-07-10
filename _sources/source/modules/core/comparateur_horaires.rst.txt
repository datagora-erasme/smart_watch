Comparateur d'Horaires
======================

.. automodule:: src.smart_watch.core.ComparateurHoraires
   :members:
   :undoc-members:
   :show-inheritance:

Classes principales
===================

.. autoclass:: src.smart_watch.core.ComparateurHoraires.HorairesComparator
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: src.smart_watch.core.ComparateurHoraires.ScheduleNormalizer
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: src.smart_watch.core.ComparateurHoraires.ComparisonResult
   :members:
   :undoc-members:

Fonctionnalités
===============

Le comparateur d'horaires effectue une comparaison intelligente et robuste entre deux structures d'horaires JSON :

**Normalisation :**

- Tri des créneaux par heure de début
- Gestion des occurrences (1er mardi du mois, etc.)
- Normalisation des formats de données
- Support des horaires spéciaux et jours fériés

**Comparaison :**

- Détection des fermetures définitives
- Comparaison par période (hors vacances, vacances, fériés)
- Identification précise des différences
- Rapport détaillé des changements

**Types de différences détectées :**

- Changements d'état (ouvert/fermé)
- Modification des créneaux horaires
- Ajout/suppression de créneaux
- Modifications des jours spéciaux

Exemple d'utilisation
=====================

.. code-block:: python

   from src.smart_watch.core.ComparateurHoraires import HorairesComparator
   import json

   # Initialisation
   comparator = HorairesComparator()
   
   # Comparaison de deux structures JSON
   horaires1 = {...}  # Structure d'horaires 1
   horaires2 = {...}  # Structure d'horaires 2
   
   result = comparator.compare_schedules(horaires1, horaires2)
   
   print(f"Identique: {result.identical}")
   print(f"Différences: {result.differences}")
   
   # Comparaison de fichiers
   result = comparator.compare_files("horaires1.json", "horaires2.json")
