Module d'Évaluation
===================

Le module ``evaluate`` fournit un ensemble d'outils pour mesurer la performance du pipeline d'extraction d'horaires de SmartWatch par rapport à un jeu de données de référence (vérité terrain).

Principe de fonctionnement
--------------------------

L'évaluation se base sur un fichier CSV contenant des URLs et les horaires de référence au format OSM. Pour chaque ligne du fichier, le module va :

1.  **Exécuter le pipeline** : Simuler le pipeline principal (récupération URL, conversion Markdown, nettoyage, filtrage, extraction LLM) pour obtenir une prédiction d'horaires.
2.  **Comparer** : Comparer la prédiction avec la vérité terrain en utilisant le même comparateur que le projet.
3.  **Compter les erreurs** : Analyser les différences pour obtenir un décompte fin des erreurs.
4.  **Agréger les résultats** : Calculer des métriques de performance sur l'ensemble du jeu de données et afficher un rapport détaillé.

Comment l'utiliser ?
--------------------

Le module est conçu pour être lancé via le script ``evaluate_pipeline.py`` situé à la racine du projet.

1.  **Préparez votre fichier d'évaluation**

Créez un fichier CSV (par exemple, ``evaluation_data.csv``) avec au minimum les colonnes ``url`` et ``ground_truth_osm``.

.. code-block:: csv

   url;ground_truth_osm
   "https://www.exemple.com/lieu1";"Mo-Fr 09:00-17:00"
   "https://www.exemple.com/lieu2";"Tu-Sa 10:00-18:00, Su 10:00-13:00"

2.  **Lancez le script d'évaluation**

Exécutez la commande suivante depuis la racine du projet :

.. code-block:: bash

   python evaluate_pipeline.py chemin/vers/votre/evaluation_data.csv

3.  **Analysez le rapport**

Le script affichera un rapport complet dans la console, incluant le taux de concordance, le nombre moyen de différences, et le détail de chaque erreur.

Composition du Module
---------------------

.. toctree::
   :maxdepth: 1

   evaluator
   scorer
   metrics
