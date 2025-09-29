Métriques d'Évaluation
========================

Le module ``metrics`` agrège les résultats de scoring individuels pour produire un rapport de performance global.

.. admonition:: Rôle

   La classe ``EvaluationMetrics`` prend une liste de ``ScoreResult`` et calcule des statistiques agrégées pour donner une vue d'ensemble de la performance du pipeline sur le jeu de données.

Fonctionnalités
---------------

- Calcule des métriques sommaires (nombre d'items identiques, différents, en erreur).
- Calcule un **taux de concordance parfaite** (accuracy).
- Fournit une **analyse fine des différences** :
    - Nombre total de différences atomiques.
    - Nombre moyen de différences par item incorrect.
    - Distribution des erreurs (ex: "5 items avec 1 différence, 2 items avec 3 différences").
- Affiche un rapport textuel complet et lisible dans la console.

Module
------

.. automodule:: src.smart_watch.evaluate.metrics
   :members:
   :undoc-members:
   :special-members: __init__
   :show-inheritance:
