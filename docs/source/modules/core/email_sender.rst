Email Sender
============

.. automodule:: src.smart_watch.core.EnvoyerMail
   :members:
   :undoc-members:
   :show-inheritance:

Fonctionnalités
---------------

Le module EmailSender gère l'envoi d'emails via SMTP avec support des pièces jointes multiples et des différents modes de sécurité. Il s'intègre avec la configuration centralisée pour les paramètres SMTP.

**Support SMTP multi-mode :**

- SSL/TLS direct (port 465) avec contexte sécurisé
- STARTTLS (port 587) avec négociation de sécurité
- Authentification optionnelle avec login/mot de passe
- Gestion des erreurs de connexion et d'authentification

**Pièces jointes :**

- Support de multiples fichiers en pièces jointes
- Validation de l'existence des fichiers
- Gestion des erreurs d'attachement individuelles
- Noms de fichiers préservés avec Content-Disposition

**Formats d'email :**

- Corps HTML avec support du formatage riche
- Multipart MIME pour compatibilité maximale
- Encodage UTF-8 pour caractères internationaux
- Headers configurables (From, To, Subject)

**Gestion robuste :**

- Logging détaillé des opérations d'envoi
- Continuation en cas d'erreur sur une pièce jointe
- Messages d'erreur explicites pour debugging
- Intégration avec le système de configuration

Classes principales
-------------------

.. autoclass:: src.smart_watch.core.EnvoyerMail.EmailSender
   :members:
   :undoc-members:
   :show-inheritance:

Configuration SMTP
------------------

Variables d'environnement requises dans `.env` :

.. code-block:: bash

   MAIL_EMETTEUR-"noreply@monsite.org"
   MAIL_RECEPTEUR-"admin@monsite.org"
   SMTP_SERVER-"smtp.monsite.org"
   SMTP_PORT-465
   SMTP_LOGIN-"login"
   SMTP_PASSWORD-"password"

**Paramètres supportés :**

- **SMTP_PORT** : 25 (non-sécurisé), 587 (STARTTLS), 465 (SSL)
- **Authentification** : Login/password ou anonyme
- **Sécurité** : Détection automatique SSL/TLS selon le port
