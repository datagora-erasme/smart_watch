Email Configuration
===================

Le module ``EmailConfigManager`` centralise la configuration pour l'envoi d'e-mails via SMTP, utilisée pour l'envoi des rapports.

.. admonition:: Usage

   ``EmailConfigManager`` est instancié par le :doc:`ConfigManager <../core/ConfigManager>` central. L'accès se fait via ``ConfigManager.email``.

Fonctionnalités
---------------

- **Configuration SMTP** : gère les paramètres du serveur SMTP, le port, l'identifiant et le mot de passe.
- **Gestion des destinataires** : prend en charge un ou plusieurs destinataires en parsant une chaîne de caractères séparée par des virgules depuis la variable d'environnement ``MAIL_RECEPTEUR``.
- **Structure de données** : utilise le dataclass ``EmailConfig`` pour stocker les paramètres de manière propre et typée.
- **Validation** : la méthode ``validate`` assure que les paramètres essentiels sont présents et valides. Elle vérifie le format des adresses e-mail (émetteur et destinataires) et s'assure que le port SMTP est dans une plage valide.

Modules
-------

.. automodule:: src.smart_watch.config.email_config
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__
   :show-inheritance:
