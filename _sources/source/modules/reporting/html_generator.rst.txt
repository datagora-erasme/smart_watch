HTML Generator
==============

Le module ``GenererRapportHTML`` est responsable de la transformation des données brutes de la base de données en un rapport HTML interactif et un résumé pour l'e-mail.

Fonctionnalités
---------------

- **Génération via Templates** : Utilise des templates Jinja2 (``ReportTemplate.html`` pour le rapport complet, ``SimpleReportTemplate.html`` pour le résumé) pour générer le HTML.
- **Extraction de Données** : Se connecte à la base de données pour extraire l'ensemble des résultats d'une exécution via une requête SQL.
- **Agrégation et Statistiques** : Calcule de nombreuses statistiques après l'extraction des données :
    - Statistiques globales (nombre d'URLs, succès des comparaisons, etc.).
    - Regroupement des URLs par statut (succès, différence, erreur).
    - Répartition par type de lieu et par code de réponse HTTP.
- **Traitement des Données** : Nettoie et formate les données pour l'affichage, notamment en parsant les chaînes d'erreurs pour les rendre plus lisibles.
- **Filtre Personnalisé** : Inclut un filtre Jinja2 personnalisé, ``tojson``, pour encoder les données complexes (comme des objets JSON) en base64, permettant de les intégrer de manière sûre dans le HTML pour des visualisations interactives.

.. admonition:: Usage

   La fonction ``generer_rapport_html`` est appelée par le :doc:`ReportManager <report_manager>`, qui lui fournit le chemin vers la base de données. Elle retourne le contenu HTML du résumé et le chemin vers le fichier du rapport complet sauvegardé.

Modules
-------

.. automodule:: src.smart_watch.reporting.GenererRapportHTML
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__
   :show-inheritance:
