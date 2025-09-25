Envoi d'Email
=============

Le module ``EnvoyerMail`` gère l'envoi d'emails via un serveur SMTP.

.. admonition:: Usage

   Ce module est utilisé par :doc:`NotificationManager <NotificationManager>` pour envoyer les rapports d'analyse par email.

Fonctionnalités
---------------

- Envoi d'emails au format HTML.
- Prise en charge des pièces jointes multiples.
- Support des modes de sécurité SSL/TLS et STARTTLS.
- Configuration via le `ConfigManager`.

Modules
-------

.. automodule:: src.smart_watch.core.EnvoyerMail
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__, __call__
   :inherited-members:
   :show-inheritance:
