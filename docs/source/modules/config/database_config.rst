Database Configuration
======================

Le module ``DatabaseConfigManager`` gère tous les paramètres liés à l'accès aux données, incluant la base de données locale SQLite et les sources de données CSV externes.

Fonctionnalités
---------------

- **Gestion des Chemins** : Construit et gère les chemins vers la base de données SQLite, le cache des fichiers CSV, et le schéma de données.
- **Configuration des Sources de Données** : Récupère les URLs des fichiers CSV de référence (piscines, mairies, médiathèques) et l'URL du fichier principal depuis les variables d'environnement.
- **Validation** : La méthode ``validate`` vérifie l'existence du fichier de schéma, s'assure que le répertoire de données peut être créé, et contrôle la validité des URLs configurées.
- **Structure de Données** : Utilise le dataclass ``DatabaseConfig`` pour stocker de manière structurée tous les paramètres de configuration.

.. admonition:: Usage

   Le ``DatabaseConfigManager`` est instancié par le :doc:`ConfigManager <../core/ConfigManager>` central. L'application accède ensuite à la configuration via ``ConfigManager.database``, qui contient une instance du dataclass ``DatabaseConfig``.

Modules
-------

.. automodule:: src.smart_watch.config.database_config
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__
   :show-inheritance:
