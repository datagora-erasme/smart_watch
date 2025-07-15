Error Handler
=============

Fonctionnalités
---------------

Le module ErrorHandler fournit un système centralisé de gestion d'erreurs avec catégorisation, traçabilité et propositions de solutions.
Il standardise le traitement des erreurs dans tout le système SmartWatch.

**Système de catégorisation :**

- Classification des erreurs par catégorie (CONFIGURATION, DATABASE, NETWORK, LLM, etc.)
- Niveaux de gravité (LOW, MEDIUM, HIGH, CRITICAL)
- Traitement spécialisé selon la catégorie d'erreur
- Suggestions de solutions

**Traçabilité complète :**

- Contexte enrichi avec module, fonction et opération
- Registre centralisé de toutes les erreurs traitées
- Timestamps et tracebacks détaillés
- Données contextuelles pour debugging

**Gestion adaptative :**

- Décorateur @handle_errors pour simplifier l'usage
- Valeurs de retour par défaut en cas d'erreur
- Option pour relancer ou continuer selon le contexte
- Logging automatique

**Solutions automatiques :**

- Détection de patterns d'erreur courants
- Suggestions de corrections
- Messages d'aide contextualisés
- Résumés d'erreurs pour reporting

Modules
-------

.. automodule:: src.smart_watch.core.ErrorHandler
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__, __call__
   :inherited-members:
   :show-inheritance: