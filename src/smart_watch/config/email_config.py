"""
Configuration email centralisée.
"""

import re
from dataclasses import dataclass
from typing import List, Optional

from ..core.ErrorHandler import ErrorCategory, ErrorSeverity, handle_errors
from .base_config import BaseConfig


@dataclass
class EmailConfig:
    """Configuration email."""

    emetteur: str
    recepteurs: List[str]  # Changé de recepteur à recepteurs (liste)
    smtp_server: str
    smtp_port: int
    smtp_password: str
    smtp_login: Optional[str] = None


class EmailConfigManager(BaseConfig):
    """Gestionnaire de configuration email."""

    def __init__(self, env_file=None):
        super().__init__(env_file)
        self.config = self._init_email_config()

    def _init_email_config(self) -> Optional[EmailConfig]:
        """Initialise la configuration email."""
        emetteur = self.get_env_var("MAIL_EMETTEUR", required=True)
        recepteur_raw = self.get_env_var("MAIL_RECEPTEUR", required=True)

        # Parser les destinataires multiples (séparés par des virgules)
        recepteurs = [
            email.strip() for email in recepteur_raw.split(",") if email.strip()
        ]

        if not recepteurs:
            raise ValueError("Aucun destinataire email valide configuré")

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
        user_message="Erreur lors de la validation de la configuration email",
        reraise=True,
    )
    def validate(self) -> bool:
        """Valide la configuration email."""
        validation_errors = []

        if not self.config:
            validation_errors.append("Configuration email manquante")
            error_message = "Validation échouée:\n" + "\n".join(
                f"  - {error}" for error in validation_errors
            )
            raise ValueError(error_message)

        # Vérifier le mot de passe SMTP
        if not self.config.smtp_password:
            validation_errors.append("SMTP_PASSWORD manquant")

        # Vérifier qu'au moins un destinataire valide existe
        if not self.config.recepteurs:
            validation_errors.append("Aucun destinataire email configuré")

        # Valider le format des emails
        email_pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

        if not email_pattern.match(self.config.emetteur):
            validation_errors.append(
                f"Format d'email émetteur invalide: {self.config.emetteur}"
            )

        for email in self.config.recepteurs:
            if not email_pattern.match(email):
                validation_errors.append(
                    f"Format d'email destinataire invalide: {email}"
                )

        # Vérifier le port SMTP
        if not (1 <= self.config.smtp_port <= 65535):
            validation_errors.append(
                f"Port SMTP invalide: {self.config.smtp_port} (doit être entre 1 et 65535)"
            )

        # Vérifier le serveur SMTP
        if not self.config.smtp_server:
            validation_errors.append("SMTP_SERVER manquant")

        # Si des erreurs sont trouvées, lever une exception avec les détails
        if validation_errors:
            error_message = "Validation échouée:\n" + "\n".join(
                f"  - {error}" for error in validation_errors
            )
            raise ValueError(error_message)

        return True
