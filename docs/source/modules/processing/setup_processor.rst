Setup Processor
===============

Fonctionnalités
---------------

Le module SetupProcessor gère l'initialisation du pipeline SmartWatch :
il charge les données CSV (locales ou distantes) dans un DataFrame Polars,
puis initialise la base de données SQLite avec ces données.

**Étapes d'initialisation :**

- Chargement du fichier CSV principal via CSVToPolars
- Détection automatique du séparateur CSV
- Gestion des sources distantes (URL) ou locales
- Création ou remplacement de la base SQLite avec les données extraites
- Validation et gestion des erreurs centralisée

**Gestion des erreurs :**

- Validation du fichier CSV et de la connexion réseau
- Gestion des exceptions lors de l'initialisation de la base
- Logging détaillé des opérations et erreurs

Modules
-------

.. automodule:: src.smart_watch.processing.setup_processor
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__, __call__
   :inherited-members:
   :show-inheritance: