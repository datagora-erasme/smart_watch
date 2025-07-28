Email Configuration
===================

Le module ``EmailConfigManager`` centralise la configuration pour l'envoi d'e-mails via SMTP, utilisée notamment pour la distribution des rapports.

Fonctionnalités
---------------

- **Configuration SMTP** : Gère les paramètres du serveur SMTP, le port, l'identifiant et le mot de passe.
- **Gestion des Destinataires** : Prend en charge un ou plusieurs destinataires en parsant une chaîne de caractères séparée par des virgules depuis la variable d'environnement ``MAIL_RECEPTEUR``.
- **Validation Détaillée** : La méthode ``validate`` assure que les paramètres essentiels sont présents et valides. Elle vérifie le format des adresses e-mail (émetteur et destinataires) à l'aide d'une expression régulière et s'assure que le port SMTP est dans une plage valide.
- **Structure de Données** : Utilise le dataclass ``EmailConfig`` pour stocker les paramètres de manière propre et typée.

.. admonition:: Usage

   Le ``EmailConfigManager`` est instancié par le :doc:`ConfigManager <../core/ConfigManager>` central. Si la configuration de l'e-mail est présente, l'application peut envoyer des notifications. L'accès se fait via ``ConfigManager.email``.

Modules
-------

.. automodule:: src.smart_watch.config.email_config
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__
   :show-inheritance:
