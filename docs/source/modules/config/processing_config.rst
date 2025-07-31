Processing Configuration
========================

Le module ``ProcessingConfigManager`` configure les paramètres généraux de traitement, notamment ceux liés à la performance du scraping web et au nettoyage initial des données textuelles.

.. admonition:: Usage

   Ce gestionnaire est instancié par le :doc:`ConfigManager <../core/ConfigManager>`. Ses paramètres, accessibles via ``ConfigManager.processing``, sont utilisés par les modules qui effectuent des requêtes réseau ou du nettoyage de texte.

Fonctionnalités
---------------

- **Multithreading** : définit le nombre de threads parallèles (``NB_THREADS_URL``) à utiliser pour le traitement des URLs, permettant d'accélérer la collecte de données.
- **Contrôle des délais** : configure les délais d'attente entre les appels réseau (``DELAI_ENTRE_APPELS``) et en cas d'erreur (``DELAI_EN_CAS_ERREUR``) pour éviter de surcharger les serveurs distants.
- **Nettoyage de caractères** : contient un dictionnaire de remplacements de caractères (``char_replacements``) qui est utilisé pour normaliser le texte brut. Il gère la conversion des guillemets, des tirets et la standardisation des espaces.
- **Validation** : la méthode ``validate`` s'assure que le nombre de threads et les délais sont des valeurs positives et que le dictionnaire de remplacements n'est pas vide.

Modules
-------

.. automodule:: src.smart_watch.config.processing_config
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__
   :show-inheritance:
