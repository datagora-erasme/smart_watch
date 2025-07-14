Error Handler
=============

.. automodule:: src.smart_watch.core.ErrorHandler
   :members:
   :undoc-members:
   :show-inheritance:

Fonctionnalités
---------------

Le module ErrorHandler fournit un système centralisé de gestion d'erreurs avec catégorisation, traçabilité et solutions automatiques. Il standardise le traitement des erreurs dans tout le système SmartWatch.

**Système de catégorisation :**
- Classification des erreurs par catégorie (CONFIGURATION, DATABASE, NETWORK, LLM, etc.)
- Niveaux de gravité (LOW, MEDIUM, HIGH, CRITICAL)
- Traitement spécialisé selon la catégorie d'erreur
- Suggestions de solutions automatiques

**Traçabilité complète :**
- Contexte enrichi avec module, fonction et opération
- Registre centralisé de toutes les erreurs traitées
- Timestamps et tracebacks détaillés
- Données contextuelles pour debugging

**Gestion adaptative :**
- Décorateur @handle_errors pour simplifier l'usage
- Valeurs de retour par défaut en cas d'erreur
- Option de relancer ou continuer selon le contexte
- Logging automatique selon la gravité

**Solutions automatiques :**
- Détection de patterns d'erreur courants
- Suggestions de configuration pour les erreurs API
- Messages d'aide contextuels
- Résumés d'erreurs pour reporting

Classes principales
-------------------

.. autoclass:: src.smart_watch.core.ErrorHandler.ErrorHandler
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: src.smart_watch.core.ErrorHandler.ErrorSeverity
   :members:
   :undoc-members:

.. autoclass:: src.smart_watch.core.ErrorHandler.ErrorCategory
   :members:
   :undoc-members:

.. autoclass:: src.smart_watch.core.ErrorHandler.ErrorContext
   :members:
   :undoc-members:

.. autoclass:: src.smart_watch.core.ErrorHandler.HandledError
   :members:
   :undoc-members:

Décorateurs
-----------

.. autofunction:: src.smart_watch.core.ErrorHandler.handle_errors

Fonctions utilitaires
---------------------

.. autofunction:: src.smart_watch.core.ErrorHandler.get_error_handler
