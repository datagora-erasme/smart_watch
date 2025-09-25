# Gestionnaire d'envoi d'emails pour le projet smart_watch
# Documentation : https://datagora-erasme.github.io/smart_watch/source/modules/core/EnvoyerMail.html

import os
import smtplib
import ssl
import time
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

from .ConfigManager import ConfigManager
from .Logger import create_logger

# Initialize logger for this module
logger = create_logger(module_name="EmailSender")


class EmailSender:
    """Classe pour envoyer des emails via SMTP."""

    def __init__(self, config: ConfigManager):
        """
        Initialise l'EmailSender avec la configuration.

        Args:
            config (ConfigManager): Instance de ConfigManager contenant les
                paramètres de configuration.

        Attributes:
            config: Configuration email extraite de l'instance ConfigManager.
            logger: Instance de logger pour cette classe.
            max_retries (int): Nombre maximum de tentatives d'envoi.
            retry_delay (int): Délai en secondes entre les tentatives.

        Raises:
            ValueError: Si la configuration email n'est pas valide.
        """
        if not config.email:
            raise ValueError(
                "EmailSender a été initialisé sans configuration email valide."
            )
        self.config = config.email
        self.logger = create_logger(self.__class__.__name__)
        self.max_retries = 10  # Nombre maximum de tentatives
        self.retry_delay = 300  # Délai en secondes entre les tentatives

    def send_email(
        self, subject: str, body: str, attachments: Optional[List[str]] = None
    ) -> None:
        """
        Envoie un email avec support pour pièces jointes multiples.

        L'envoi se fait avec _send_ssl ou _send_starttls en fonction du port
        configuré :
            - Port 465 : SSL/TLS
            - Port 587 : STARTTLS

        Args:
            subject (str): Sujet de l'email.
            body (str): Corps de l'email (HTML).
            attachments (Optional[List[str]]): Liste des chemins vers les
                fichiers à joindre.
        """
        message = MIMEMultipart()
        message["From"] = self.config.emetteur
        message["To"] = ", ".join(self.config.recepteurs)
        message["Subject"] = subject
        message.attach(MIMEText(body, "html"))

        if attachments:
            for file_path in attachments:
                if not os.path.exists(file_path):
                    self.logger.warning(f"Pièce jointe non trouvée: {file_path}")
                    continue
                try:
                    with open(file_path, "rb") as attachment:
                        part = MIMEApplication(
                            attachment.read(), Name=os.path.basename(file_path)
                        )
                    part["Content-Disposition"] = (
                        f'attachment; filename="{os.path.basename(file_path)}"'
                    )
                    message.attach(part)
                    self.logger.debug(f"Pièce jointe: {os.path.basename(file_path)}")
                except Exception as e:
                    self.logger.error(
                        f"Erreur attachement pièce jointe {file_path}: {e}"
                    )

        email_string = message.as_string()

        for attempt in range(self.max_retries):
            try:
                self.logger.info(
                    f"Tentative {attempt + 1}/{self.max_retries} d'envoi de l'email: "
                    f"{self.config.emetteur} → {len(self.config.recepteurs)} destinataires"
                )
                if self.config.smtp_port == 465:
                    self._send_ssl(email_string)
                else:
                    self._send_starttls(email_string)
                return
            except (smtplib.SMTPException, OSError) as e:
                self.logger.warning(
                    f"Échec de la tentative {attempt + 1}/{self.max_retries} d'envoi de l'email: {e}"
                )
                if attempt < self.max_retries - 1:
                    self.logger.info(
                        f"Nouvelle tentative dans {self.retry_delay} secondes..."
                    )
                    time.sleep(self.retry_delay)
                else:
                    self.logger.error(
                        "Échec de l'envoi de l'email après plusieurs tentatives."
                    )
                    raise

    def _send_ssl(self, email_string: str) -> None:
        """
        Envoie l'email via une connexion SSL/TLS.

        Utilise le port 465 pour la connexion SSL.

        Args:
            email_string (str): Contenu de l'email à envoyer.

        Warning:
            Cette méthode utilise une connexion SSL/TLS non vérifiée pour
            contourner les erreurs de certificat SSL. Ceci est INSECURISÉ.
        """
        # NOTE: Utilisation d'un contexte non vérifié pour contourner les erreurs de certificat SSL.
        # Ceci est INSECURISÉ et ne devrait être utilisé que si vous faites confiance au réseau et au serveur.
        context = ssl._create_unverified_context()
        self.logger.debug(f"Connexion SMTP SSL/TLS port {self.config.smtp_port}")
        with smtplib.SMTP_SSL(
            self.config.smtp_server,
            self.config.smtp_port,
            context=context,
            timeout=30,
        ) as server:
            if self.config.smtp_login and self.config.smtp_password:
                server.login(self.config.smtp_login, self.config.smtp_password)
            server.sendmail(self.config.emetteur, self.config.recepteurs, email_string)
            self.logger.info(
                f"Email envoyé avec succès (SSL/TLS) à {len(self.config.recepteurs)} destinataires"
            )

    def _send_starttls(self, email_string: str) -> None:
        """
        Envoie l'email via une connexion STARTTLS.

        Utilise le port 587 pour STARTTLS.

        Args:
            email_string (str): Contenu de l'email à envoyer.
        """
        self.logger.debug(f"Connexion SMTP STARTTLS port {self.config.smtp_port}")
        with smtplib.SMTP(
            self.config.smtp_server, self.config.smtp_port, timeout=30
        ) as server:
            server.starttls()
            if self.config.smtp_login and self.config.smtp_password:
                server.login(self.config.smtp_login, self.config.smtp_password)
            server.sendmail(self.config.emetteur, self.config.recepteurs, email_string)
            self.logger.info(
                f"Email envoyé avec succès (STARTTLS) à {len(self.config.recepteurs)} destinataires"
            )
