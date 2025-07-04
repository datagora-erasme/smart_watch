Configuration Manager
=====================

.. automodule:: src.smart_watch.core.ConfigManager
   :members:
   :undoc-members:
   :show-inheritance:

Classes de configuration
========================

.. autoclass:: src.smart_watch.core.ConfigManager.ConfigManager
   :members:
   :undoc-members:
   :show-inheritance:

Exemple d'utilisation
=====================

.. code-block:: python

   from src.smart_watch.core.ConfigManager import ConfigManager

   # Initialisation
   config = ConfigManager()
   
   # Validation
   if config.validate():
       print(f"LLM: {config.llm.fournisseur} - {config.llm.modele}")
       print(f"Base: {config.database.db_file}")
   
   # Affichage du résumé
   config.display_summary()
