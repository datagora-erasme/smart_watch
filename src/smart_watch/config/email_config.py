# Documentation
# https://datagora-erasme.github.io/smart_watch/source/modules/config/email_config.html

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from ..core.ErrorHandler import ErrorCategory, ErrorSeverity, handle_errors
from .base_config import BaseConfig


@dataclass
class EmailConfig:
    """
    Dataclasse pour stocker les paramètres de configuration email.

    Attributes:
        emetteur (str) : adresse email de l'expéditeur.
        recepteurs (List[str]) : liste des adresses email des destinataires.
        smtp_server (str) : adresse du serveur SMTP.
        smtp_port (int) : port du serveur SMTP.
        smtp_password (str) : mot de passe SMTP pour l'authentification.
        smtp_login (Optional[str]) : identifiant de connexion SMTP. Par défaut à None.
    """

    emetteur: str
    recepteurs: List[str]
    smtp_server: str
    smtp_port: int
    smtp_password: str
    smtp_login: Optional[str] = None


class EmailConfigManager(BaseConfig):
    """
    Gère le chargement et la validation de la configuration email depuis les variables d'environnement.

    Cette classe hérite de `BaseConfig` et fournit des méthodes pour initialiser et valider les paramètres email, en s'assurant que tous les paramètres requis sont présents et correctement formatés.

    Attributes:
        config (EmailConfig) : objet de configuration email chargé.
    """

    def __init__(self, env_file: Optional[Path] = None) -> None:
        """
        Initialise le gestionnaire de configuration email.

        Args:
            env_file (Optional[Path], optional) : chemin vers le fichier d'environnement.
        """
        super().__init__(env_file)
        self.config: EmailConfig = self._init_email_config()

    def _init_email_config(self) -> EmailConfig:
        """
        Initialise la configuration email à partir des variables d'environnement.

        Returns:
            EmailConfig : un objet `EmailConfig` si toutes les variables requises sont trouvées.

        Raises:
            ValueError : si une variable d'environnement requise est manquante ou invalide.
        """
        emetteur: str = self.get_env_var("MAIL_EMETTEUR", required=True)
        recepteur_raw: str = self.get_env_var("MAIL_RECEPTEUR", required=True)

        if not emetteur or not recepteur_raw:
            # Cette vérification est redondante si required=True lève une exception,
            # mais elle enlève les erreurs Pylance.
            raise ValueError(
                "Les variables d'environnement MAIL_EMETTEUR et MAIL_RECEPTEUR sont obligatoires."
            )

        recepteurs: List[str] = [
            email.strip() for email in recepteur_raw.split(",") if email.strip()
        ]

        if not recepteurs:
            raise ValueError("Aucun destinataire email valide n'est configuré.")

        return EmailConfig(
            emetteur=emetteur,
            recepteurs=recepteurs,
            smtp_server=self.get_env_var("SMTP_SERVER", required=True),
            smtp_port=int(self.get_env_var("SMTP_PORT", "587")),
            smtp_password=self.get_env_var("SMTP_PASSWORD", required=True),
            smtp_login=self.get_env_var("SMTP_LOGIN"),
        )

    @handle_errors(
        category=ErrorCategory.CONFIGURATION,
        severity=ErrorSeverity.HIGH,
        user_message="Erreur lors de la validation de la configuration email.",
        reraise=True,
    )
    def validate(self) -> bool:
        """
        Valide la configuration email. Lève une exception si la configuration est absente ou incomplète.
        """
        # Si l'émetteur n'est pas défini, la configuration est considérée comme absente et invalide.
        if not self.config.emetteur:
            raise ValueError(
                "La configuration pour l'envoi d'email est obligatoire. "
                "Veuillez définir EMAIL_EMETTEUR et les variables associées dans le fichier .env."
            )

        # Si l'émetteur est défini, les autres champs obligatoires doivent l'être aussi.
        required_fields = {
            "recepteurs": self.config.recepteurs,
            "smtp_server": self.config.smtp_server,
            "smtp_port": self.config.smtp_port,
        }

        missing_fields = [
            field for field, value in required_fields.items() if not value
        ]

        if missing_fields:
            raise ValueError(
                f"Configuration email incomplète. Champs manquants: {', '.join(missing_fields)}"
            )

        return True
