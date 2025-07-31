Database Configuration
======================

Le module ``DatabaseConfigManager`` gère tous les paramètres liés à l'accès aux données, incluant la base de données locale SQLite et les sources de données CSV externes.

.. admonition:: Usage

   ``DatabaseConfigManager`` est instancié par le :doc:`ConfigManager <../core/ConfigManager>` central. L'application accède ensuite à la configuration via ``ConfigManager.database``, qui contient une instance du dataclass ``DatabaseConfig``.

Fonctionnalités
---------------

- **Gestion des chemins** : construit et gère les chemins vers la base de données SQLite, le cache des fichiers CSV, et le schéma de données.
- **Configuration des sources de données** : récupère les URLs des fichiers CSV de référence (piscines, mairies, médiathèques) et l'URL du fichier principal depuis les variables d'environnement.
- **Structure de données** : utilise le dataclass ``DatabaseConfig`` pour stocker de manière structurée tous les paramètres de configuration.
- **Validation** : la méthode ``validate`` vérifie l'existence du fichier de schéma, s'assure que le répertoire de données peut être créé, et contrôle la validité des URLs configurées.

Modules
-------

.. automodule:: src.smart_watch.config.database_config
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__
   :show-inheritance:
