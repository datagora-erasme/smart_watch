Database Processor
==================

Le ``DatabaseProcessor`` est un module de service central qui encapsule toutes les interactions avec la base de données pour le pipeline de traitement. Il ne constitue pas une étape du pipeline lui-même, mais fournit une API de haut niveau aux autres processeurs pour lire et écrire des données de manière structurée.

Fonctionnalités
---------------

- **Gestion de la Base de Données** : Utilise SQLAlchemy pour gérer la connexion, les sessions et le schéma de la base de données (création des tables `lieux`, `executions`, `resultats_extraction`).
- **Initialisation d'Exécution** : La méthode ``setup_execution`` est une fonction clé qui prépare une nouvelle exécution en mettant à jour la liste des lieux, en créant un enregistrement d'exécution, et en identifiant les tâches incomplètes des exécutions précédentes à reprendre.
- **Fournisseur de Données** : Offre des méthodes spécifiques comme ``get_pending_urls`` et ``get_pending_llm`` que les processeurs du pipeline utilisent pour récupérer leur file de travail.
- **Persistance des Résultats** : Propose des méthodes dédiées (ex: ``update_url_result``, ``update_llm_result``) pour que chaque processeur puisse sauvegarder les résultats de son traitement à l'étape correspondante.
- **Gestion des Erreurs** : Centralise l'enregistrement des erreurs du pipeline dans la base de données, en les ajoutant à une chaîne d'erreurs traçable pour chaque lieu.

.. admonition:: Usage

   Une instance de ``DatabaseProcessor`` est créée au début du pipeline et est ensuite passée en argument à chaque processeur qui a besoin d'interagir avec la base de données.

Modules
-------

.. automodule:: src.smart_watch.processing.database_processor
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__
   :show-inheritance:
