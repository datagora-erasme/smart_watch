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
        """
        Initialise l'EmailSender avec la configuration du gestionnaire de configuration.

        Cette classe utilise les paramètres de configuration pour envoyer des emails, y compris les destinataires, l'émetteur, le serveur SMTP et les informations d'authentification.

        Args:
            config (ConfigManager): instance de ConfigManager contenant les paramètres de configuration.
        """
        if not config.email:
            # Cette erreur ne devrait jamais se produire si la validation en amont est correcte.
            # Elle sert de garde-fou et informe l'analyseur de code Pylance.
            raise ValueError(
                "EmailSender a été initialisé sans configuration email valide."
            )
        self.config = config.email
        self.logger = create_logger(self.__class__.__name__)

    def send_email(
        self, subject: str, body: str, attachments: Optional[List[str]] = None
    ):
        """
        Envoie un email avec support pour pièces jointes multiples.

        L'envoi se fait avec _send_ssl ou _send_starttls en fonction du port configuré :
            - Port 465 : SSL/TLS
            - Port 587 : STARTTLS

        Args:
            subject (str): sujet de l'email.
            body (str): corps de l'email (HTML).
            attachments (Optional[List[str]]): liste des chemins vers les fichiers à joindre.
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
        """
        Envoie l'email via une connexion SSL/TLS. Utilise le port 465 pour la connexion SSL.

        Args:
            email_string (str): contenu de l'email à envoyer.

        Warning:
            Cette méthode utilise une connexion SSL/TLS non vérifiée pour contourner les erreurs de certificat SSL. Ceci est INSECURISÉ car bien que l'on connaisse le serveur dans notre cas, on ne peut être certain du réseau par contre.
        """
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
        """
        Envoie l'email via une connexion STARTTLS. Utilise le port 587 pour STARTTLS.

        Args:
            email_string (str): contenu de l'email à envoyer.
        """
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
