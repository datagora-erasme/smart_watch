Gestionnaire de Statistiques
============================

Le module ``StatsManager`` collecte, analyse et présente les statistiques d'exécution du pipeline de traitement.

Fonctionnalités
---------------

- Extrait les indicateurs clés depuis la base de données via des requêtes SQL.
- Structure les statistiques par section (URLs, Markdown, LLM, Comparaisons, Global).
- Fournit des méthodes pour afficher les statistiques dans les logs ou les formater pour une API.
- Calcule des métriques de performance (taux de réussite, temps de traitement, etc.).

.. admonition:: Usage

   Le ``StatsManager`` est utilisé à la fin du pipeline pour générer un résumé des performances et des résultats du traitement.

Modules
-------

.. automodule:: src.smart_watch.core.StatsManager
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__, __call__
   :inherited-members:
   :show-inheritance:
