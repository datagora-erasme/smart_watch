Comparison Processor
====================

.. automodule:: src.smart_watch.processing.comparison_processor
   :members:
   :undoc-members:
   :show-inheritance:

Classes principales
===================

.. autoclass:: src.smart_watch.processing.comparison_processor.ComparisonProcessor
   :members:
   :undoc-members:
   :show-inheritance:

Fonctionnalités
===============

Le ComparisonProcessor compare les horaires extraits par LLM avec les données de référence :

**Sources de comparaison :**
- **Référence** : Données data.grandlyon.com converties en JSON via `OSMToCustomJson`
- **Extraction** : Horaires LLM au format JSON personnalisé
- Comparaison directe JSON vs JSON avec normalisation

**Logique de comparaison :**
- Utilise `HorairesComparator` pour comparaison intelligente
- Normalisation des structures (tri, formats, occurrences)
- Détection des fermetures définitives
- Comparaison par période (hors vacances, vacances, fériés)

**Types de résultats :**
- **`True`** : Horaires identiques
- **`False`** : Différences détectées avec description
- **`None`** : Impossible de comparer (erreur ou données manquantes)

**Traitement global :**
- Traite TOUS les enregistrements nécessitant une comparaison
- Indépendant de l'execution_id (rattrapage automatique)
- Mise à jour sélective (seulement si comparaison réussit)

Exemple d'utilisation
=====================

.. code-block:: python

   from src.smart_watch.processing.comparison_processor import ComparisonProcessor
   from src.smart_watch.core.ConfigManager import ConfigManager

   # Initialisation
   config = ConfigManager()
   processor = ComparisonProcessor(config, logger)
   
   # Traitement des comparaisons
   stats = processor.process_comparisons(db_manager)
   
   print(f"Comparaisons: {stats.comparisons_successful}/{stats.comparisons_processed}")
