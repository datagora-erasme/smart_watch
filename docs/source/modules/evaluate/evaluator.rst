Évaluateur du Pipeline
======================

Le module ``evaluator`` orchestre le processus d'évaluation complet.

.. admonition:: Rôle

   La classe ``Evaluator`` est le chef d'orchestre du module d'évaluation. Elle simule le pipeline de traitement de SmartWatch sur un jeu de données fourni (un fichier CSV) et utilise les autres composants (Scorer, Metrics) pour calculer et afficher les résultats.

Fonctionnalités
---------------

- Charge un jeu de données d'évaluation depuis un fichier CSV (séparateur = ;)
- Pour chaque item, exécute les étapes clés du pipeline : récupération de l'URL, nettoyage et filtrage du Markdown, et extraction par le LLM.
- Fait appel au ``Scorer`` pour comparer le résultat prédit avec la vérité terrain.
- Collecte tous les résultats et les transmet à ``EvaluationMetrics`` pour l'affichage du rapport final.

Module
------

.. automodule:: src.smart_watch.evaluate.evaluator
   :members:
   :undoc-members:
   :private-members: _process_single_item
   :special-members: __init__
   :show-inheritance:
