Error Handler
=============

Le module ``ErrorHandler`` fournit un système centralisé pour la gestion et la traçabilité des erreurs dans l'application.

Fonctionnalités
---------------

- Catégorise les erreurs par type (Configuration, Réseau, LLM, etc.) et par niveau de gravité.
- Enregistre les erreurs avec un contexte détaillé pour faciliter le débogage.
- Fournit un décorateur ``@handle_errors`` pour une intégration simplifiée dans le code.
- Suggère des solutions pour les erreurs courantes.

.. admonition:: Usage

   L'``ErrorHandler`` est utilisé dans toute l'application pour garantir une gestion cohérente et robuste des exceptions.

Modules
-------

.. automodule:: src.smart_watch.core.ErrorHandler
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__, __call__
   :inherited-members:
   :show-inheritance:
