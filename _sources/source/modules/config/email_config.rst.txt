Email Configuration
===================

.. automodule:: src.smart_watch.config.email_config
   :members:
   :undoc-members:
   :show-inheritance:

Classes principales
===================

.. autoclass:: src.smart_watch.config.email_config.EmailConfig
   :members:
   :undoc-members:

.. autoclass:: src.smart_watch.config.email_config.EmailConfigManager
   :members:
   :undoc-members:
   :show-inheritance:

Fonctionnalités
================

- Configuration SMTP complète
- Support SSL/TLS
- Gestion des pièces jointes
- Configuration optionnelle (peut être désactivée)

Exemple d'utilisation
=====================

.. code-block:: python

   from src.smart_watch.config.email_config import EmailConfigManager

   # Initialisation
   email_config = EmailConfigManager()
   
   if email_config.config:
       print(f"SMTP: {email_config.config.smtp_server}")
       print(f"Destinataire: {email_config.config.recepteur}")
