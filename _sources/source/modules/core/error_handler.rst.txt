Error Handler
=============

.. automodule:: src.smart_watch.core.ErrorHandler
   :members:
   :undoc-members:
   :show-inheritance:

Classes principales
===================

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
===========

.. autofunction:: src.smart_watch.core.ErrorHandler.handle_errors

Fonctions utilitaires
=====================

.. autofunction:: src.smart_watch.core.ErrorHandler.get_error_handler

Exemple d'utilisation
=====================

.. code-block:: python

   from src.smart_watch.core.ErrorHandler import ErrorHandler, ErrorCategory, ErrorSeverity, handle_errors

   # Utilisation directe
   error_handler = ErrorHandler()
   
   try:
       # Code pouvant générer une erreur
       pass
   except Exception as e:
       context = error_handler.create_error_context(
           module="MonModule",
           function="ma_fonction", 
           operation="Opération critique"
       )
       
       error_handler.handle_error(
           exception=e,
           context=context,
           category=ErrorCategory.LLM,
           severity=ErrorSeverity.MEDIUM
       )
   
   # Utilisation avec décorateur
   @handle_errors(
       category=ErrorCategory.LLM,
       severity=ErrorSeverity.MEDIUM,
       user_message="Erreur lors de l'appel LLM"
   )
   def ma_fonction_llm():
       # Code avec gestion automatique d'erreurs
       pass
