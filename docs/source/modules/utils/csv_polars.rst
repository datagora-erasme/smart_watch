CSV to Polars
=============

.. automodule:: src.smart_watch.utils.CSVToPolars
   :members:
   :undoc-members:
   :show-inheritance:

Fonctionnalités
---------------

Le module CSVToPolars fournit un chargeur de fichiers CSV robuste avec support des sources locales et distantes. Il utilise Polars pour des performances optimales et inclut la détection automatique de séparateurs.

**Chargement multi-source :**
- Support des URLs HTTP/HTTPS avec téléchargement automatique
- Fichiers locaux avec validation d'existence
- Téléchargement vers fichiers temporaires avec nettoyage automatique
- Gestion des timeouts et erreurs réseau

**Détection automatique :**
- Détection intelligente du séparateur CSV via csv.Sniffer
- Échantillonnage des premières lignes pour analyse
- Fallback vers point-virgule si détection échoue
- Support des en-têtes configurables

**Optimisations Polars :**
- Lecture efficace avec Polars pour grandes données
- Troncature des lignes malformées (truncate_ragged_lines)
- Filtrage automatique des lignes entièrement vides
- Gestion robuste des encodages UTF-8

**Gestion d'erreurs :**
- Validation des fichiers locaux avant lecture
- Gestion des erreurs de téléchargement avec messages explicites
- Nettoyage automatique des fichiers temporaires
- Logging détaillé des opérations et statistiques

Classes principales
-------------------

.. autoclass:: src.smart_watch.utils.CSVToPolars.CSVToPolars
   :members:
   :undoc-members:
   :show-inheritance:
