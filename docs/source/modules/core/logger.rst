Logger
======

.. automodule:: src.smart_watch.core.Logger
   :members:
   :undoc-members:
   :show-inheritance:

Classes principales
===================

.. autoclass:: src.smart_watch.core.Logger.SmartWatchLogger
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: src.smart_watch.core.Logger.LogLevel
   :members:
   :undoc-members:

.. autoclass:: src.smart_watch.core.Logger.LogOutput
   :members:
   :undoc-members:

Fonctions utilitaires
=====================

.. autofunction:: src.smart_watch.core.Logger.create_logger

Exemple d'utilisation
=====================

.. code-block:: python

   from src.smart_watch.core.Logger import create_logger, LogLevel

   # Création d'un logger avec sorties par défaut (fichier + console)
   logger = create_logger("MonModule")
   
   # Logger avec sortie console uniquement
   logger_console = create_logger("MonModule", outputs=["console"])
   
   # Utilisation
   logger.info("Message d'information")
   logger.error("Message d'erreur")
   logger.section("SECTION IMPORTANTE")
   logger.debug("Message de debug")
