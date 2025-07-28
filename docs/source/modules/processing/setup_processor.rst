Setup Processor
===============

Le ``SetupProcessor`` est la première étape du pipeline de traitement. Son rôle est d'initialiser une nouvelle exécution en chargeant la liste des lieux à traiter et en préparant la base de données.

Fonctionnalités
---------------

- **Chargement des Données Initiales** : Utilise l'utilitaire ``CSVToPolars`` pour charger le fichier CSV principal contenant la liste des lieux et leurs URLs, tel que défini dans la configuration.
- **Initialisation de l'Exécution** : Appelle la méthode ``setup_execution`` du :doc:`DatabaseProcessor <database_processor>` pour effectuer plusieurs actions critiques :
    - Mettre à jour la table des lieux.
    - Enrichir les lieux avec des données de référence.
    - Créer un nouvel enregistrement dans la table des exécutions.
    - Préparer les enregistrements de résultats pour chaque lieu.

.. admonition:: Usage

   Ce processeur est appelé une seule fois au début de chaque exécution du pipeline pour s'assurer que l'environnement est correctement configuré avant de commencer le traitement des URLs.

Modules
-------

.. automodule:: src.smart_watch.processing.setup_processor
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__
   :show-inheritance:
