CSV to Polars
=============

Fonctionnalités
---------------

Le module CSVToPolars permet de charger dans un dataframe Polars des fichiers CSV locaux ou distants. Il inclut une détection automatique des séparateurs.

**Chargement multi-source :**

- Support des URLs HTTP/HTTPS et des fichiers locaux
- Téléchargement des URLS vers fichiers temporaires avec nettoyage automatique
- Gestion des timeouts et erreurs réseau

**Détection automatique :**

- Détection du séparateur via csv.Sniffer
- si en-tête détecté, détection du séparateur sur cette ligne,
- sinon échantillonnage des premières lignes (50 max) pour analyse
- Fallback vers point-virgule si détection échoue

**Optimisations Polars :**

- Troncature silencieuse des lignes malformées (truncate_ragged_lines)
- Filtrage automatique des lignes entièrement vides

**Gestion d'erreurs :**

- Validation des fichiers locaux avant lecture
- Gestion des erreurs de téléchargement avec messages explicites
- Nettoyage automatique des fichiers temporaires
- Logging détaillé des opérations


Module
------

.. automodule:: src.smart_watch.utils.CSVToPolars
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__, __call__
   :inherited-members:
   :show-inheritance:
