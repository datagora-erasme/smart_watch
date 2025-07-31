# Documentation
# https://datagora-erasme.github.io/smart_watch/source/modules/config/email_config.html

import re
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
        config (Optional[EmailConfig]) : objet de configuration email chargé.
    """

    def __init__(self, env_file: Optional[Path] = None) -> None:
        """
        Initialise le gestionnaire de configuration email.

        Args:
            env_file : chemin vers le fichier d'environnement.
        """
        super().__init__(env_file)
        self.config: Optional[EmailConfig] = self._init_email_config()

    def _init_email_config(self) -> Optional[EmailConfig]:
        """
        Initialise la configuration email à partir des variables d'environnement.

        Returns:
            Optional[EmailConfig] : un objet `EmailConfig` si toutes les variables requises sont trouvées, sinon None.

        Raises:
            ValueError : si aucun destinataire email valide n'est configuré.
        """
        emetteur: str = self.get_env_var("MAIL_EMETTEUR", required=True)
        recepteur_raw: str = self.get_env_var("MAIL_RECEPTEUR", required=True)

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
        Valide la configuration email chargée.

        Cette méthode vérifie la présence des champs obligatoires, valide le format des adresses email et s'assure que le port SMTP est dans la plage autorisée.

        Returns:
            bool : True si la configuration est valide.

        Raises:
            ValueError : si la configuration est absente ou invalide.
        """
        validation_errors: List[str] = []

        if not self.config:
            validation_errors.append("La configuration email est absente.")
            error_message: str = "Échec de la validation :\n" + "\n".join(
                f"  - {error}" for error in validation_errors
            )
            raise ValueError(error_message)

        if not self.config.smtp_password:
            validation_errors.append("SMTP_PASSWORD est manquant.")

        if not self.config.recepteurs:
            validation_errors.append("Aucun destinataire email n'est configuré.")

        email_pattern: re.Pattern = re.compile(
            r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        )

        if not email_pattern.match(self.config.emetteur):
            validation_errors.append(
                f"Format d'email expéditeur invalide : {self.config.emetteur}"
            )

        for email in self.config.recepteurs:
            if not email_pattern.match(email):
                validation_errors.append(
                    f"Format d'email destinataire invalide : {email}"
                )

        if not (1 <= self.config.smtp_port <= 65535):
            validation_errors.append(
                f"Port SMTP invalide : {self.config.smtp_port} "
                f"(doit être compris entre 1 et 65535)."
            )

        if not self.config.smtp_server:
            validation_errors.append("SMTP_SERVER est manquant.")

        if validation_errors:
            error_message = "Échec de la validation :\n" + "\n".join(
                f"  - {error}" for error in validation_errors
            )
            raise ValueError(error_message)

        return True
