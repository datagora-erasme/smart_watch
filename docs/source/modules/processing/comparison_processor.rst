Comparison Processor
====================

Le ``ComparisonProcessor`` est la dernière étape du pipeline de traitement. Sa fonction est de valider la qualité de l'extraction LLM en comparant les horaires obtenus avec ceux de la source de données de référence (data.grandlyon.com).

Fonctionnalités
---------------

- **Comparaison d'Horaires** : Utilise l'utilitaire ``HorairesComparator`` pour effectuer une comparaison sémantique entre deux objets JSON représentant des horaires : celui extrait par le LLM et celui provenant de la source de référence.
- **Traitement Global** : Récupère tous les enregistrements de la base de données qui ont une extraction LLM valide mais qui n'ont pas encore été comparés, indépendamment de leur exécution d'origine. Cela permet de rattraper les comparaisons qui auraient pu échouer lors d'exécutions précédentes.
- **Gestion des Résultats** : Met à jour la base de données avec le résultat de la comparaison :
    - ``True`` si les horaires sont identiques.
    - ``False`` si des différences sont détectées, avec une description des écarts.
    - ``None`` si la comparaison n'a pas pu être effectuée (ex: données de référence manquantes).

.. admonition:: Usage

   Ce processeur s'exécute à la fin du pipeline. Ses résultats sont essentiels pour le rapport final, car ils permettent de quantifier la fiabilité des extractions et d'identifier les changements d'horaires.

Modules
-------

.. automodule:: src.smart_watch.processing.comparison_processor
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__
   :show-inheritance:
