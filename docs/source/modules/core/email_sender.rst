Email Sender
============

.. automodule:: src.smart_watch.core.EnvoyerMail
   :members:
   :undoc-members:
   :show-inheritance:

Classes principales
===================

.. autoclass:: src.smart_watch.core.EnvoyerMail.EmailSender
   :members:
   :undoc-members:
   :show-inheritance:

Fonctionnalités
===============

Le module EmailSender gère l'envoi automatique d'emails avec pièces jointes :

**Configuration SMTP :**

- Support des connexions SSL/TLS
- Authentification SMTP configurable
- Gestion des erreurs de connexion
- Configuration via variables d'environnement

**Fonctionnalités d'envoi :**

- **Templates HTML** : Corps d'email riche avec templates Jinja2
- **Pièces jointes multiples** : Support des fichiers ZIP, HTML, logs
- **Encodage UTF-8** : Gestion complète des caractères spéciaux
- **Headers personnalisés** : Subject, From, To, Date automatiques

**Intégration pipeline :**

- Envoi automatique des rapports après génération
- Fichiers joints : rapport HTML complet + logs zippés
- Email de résumé avec statistiques principales
- Gestion optionnelle (peut être désactivé)

**Sécurité :**

- Validation des adresses email
- Gestion sécurisée des credentials SMTP
- Timeouts configurables pour éviter les blocages

Exemple d'utilisation
=====================

.. code-block:: python

   from src.smart_watch.core.EnvoyerMail import EmailSender
   from src.smart_watch.core.ConfigManager import ConfigManager

   # Initialisation
   config = ConfigManager()
   email_sender = EmailSender(config, logger)
   
   # Envoi d'un rapport avec pièces jointes
   attachments = [
       "rapport_complet.html",
       "logs_execution.zip"
   ]
   
   success = email_sender.send_report_email(
       subject="Rapport SmartWatch - Extraction horaires",
       html_body="<h1>Rapport généré</h1><p>Voir pièces jointes.</p>",
       attachments=attachments
   )
   
   if success:
       logger.info("Email envoyé avec succès")
   else:
       logger.error("Échec envoi email")

Configuration SMTP
==================

Variables d'environnement requises dans `.env` :

.. code-block:: bash

   MAIL_EMETTEUR="noreply@monsite.org"
   MAIL_RECEPTEUR="admin@monsite.org"
   SMTP_SERVER="smtp.monsite.org"
   SMTP_PORT=465
   SMTP_LOGIN="login"
   SMTP_PASSWORD="password"

**Paramètres supportés :**

- **SMTP_PORT** : 25 (non-sécurisé), 587 (STARTTLS), 465 (SSL)
- **Authentification** : Login/password ou anonyme
- **Sécurité** : Détection automatique SSL/TLS selon le port
