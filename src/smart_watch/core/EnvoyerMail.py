import os
import smtplib
import ssl
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

from .ConfigManager import ConfigManager
from .Logger import create_logger

logger = create_logger(__name__)


class EmailSender:
    """Classe pour envoyer des emails via SMTP."""

    def __init__(self, config: ConfigManager):
        self.config = config.email
        self.logger = create_logger(self.__class__.__name__)

    def send_email(
        self, subject: str, body: str, attachments: Optional[List[str]] = None
    ):
        """
        Envoie un email avec support pour pièces jointes multiples.

        Args:
            subject: Sujet de l'email.
            body: Corps de l'email (HTML).
            attachments: Liste des chemins vers les fichiers à joindre.
        """
        message = MIMEMultipart()
        message["From"] = self.config.emetteur

        # Joindre tous les destinataires dans le header "To"
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

        try:
            self.logger.info(
                f"Envoi email: {self.config.emetteur} → {len(self.config.recepteurs)} destinataires"
            )
            if self.config.smtp_port == 465:
                self._send_ssl(email_string)
            else:
                self._send_starttls(email_string)
        except Exception as e:
            self.logger.error(f"Échec envoi email: {e}")
            raise

    def _send_ssl(self, email_string: str):
        """Envoie via SSL."""
        # NOTE: Utilisation d'un contexte non vérifié pour contourner les erreurs de certificat SSL.
        # Ceci est INSECURISÉ et ne devrait être utilisé que si vous faites confiance au réseau et au serveur.
        context = ssl._create_unverified_context()
        self.logger.debug(f"Connexion SMTP SSL/TLS port {self.config.smtp_port}")
        with smtplib.SMTP_SSL(
            self.config.smtp_server, self.config.smtp_port, context=context
        ) as server:
            if self.config.smtp_login and self.config.smtp_password:
                server.login(self.config.smtp_login, self.config.smtp_password)
            # Utiliser la liste des destinataires pour l'envoi effectif
            server.sendmail(self.config.emetteur, self.config.recepteurs, email_string)
            self.logger.info(
                f"Email envoyé avec succès (SSL/TLS) à {len(self.config.recepteurs)} destinataires"
            )

    def _send_starttls(self, email_string: str):
        """Envoie via STARTTLS."""
        self.logger.debug(f"Connexion SMTP STARTTLS port {self.config.smtp_port}")
        with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
            # NOTE: Utilisation d'un contexte non vérifié pour contourner les erreurs de certificat SSL.
            #
            server.starttls()
            if self.config.smtp_login and self.config.smtp_password:
                server.login(self.config.smtp_login, self.config.smtp_password)
            # Utiliser la liste des destinataires pour l'envoi effectif
            server.sendmail(self.config.emetteur, self.config.recepteurs, email_string)
            self.logger.info(
                f"Email envoyé avec succès (STARTTLS) à {len(self.config.recepteurs)} destinataires"
            )
