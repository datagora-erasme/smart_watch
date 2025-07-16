Email Configuration
===================

Fonctionnalités
---------------

Le module EmailConfig gère la configuration SMTP pour l'envoi de rapports par email. Il supporte les protocoles SSL/TLS et STARTTLS avec authentification optionnelle.

**Configuration SMTP :**

- Support des protocoles SSL/TLS (port 465) et STARTTLS (port 587)
- Authentification SMTP avec login/mot de passe
- Configuration des adresses émetteur et récepteur
- Serveur SMTP configurable avec port personnalisé

**Gestion optionnelle :**

- Configuration email entièrement optionnelle
- Validation intelligente selon la présence des paramètres
- Fallback gracieux si email non configuré
- Gestion des erreurs de configuration avec messages explicites

**Sécurité :**

- Mots de passe chargés depuis variables d'environnement
- Support des contextes SSL sécurisés
- Validation des paramètres obligatoires
- Gestion des erreurs d'authentification

Modules
-------

.. automodule:: src.smart_watch.config.email_config
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__, __call__
   :inherited-members:
   :show-inheritance:
