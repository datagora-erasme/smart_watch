"""
Configuration email centralisée.
"""

from dataclasses import dataclass
from typing import Optional

from .base_config import BaseConfig


@dataclass
class EmailConfig:
    """Configuration email."""

    emetteur: str
    recepteur: str
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
        emetteur = self.get_env_var("MAIL_EMETTEUR")
        recepteur = self.get_env_var("MAIL_RECEPTEUR")

        if not emetteur or not recepteur:
            return None

        return EmailConfig(
            emetteur=emetteur,
            recepteur=recepteur,
            smtp_server=self.get_env_var("SMTP_SERVER", required=True),
            smtp_port=int(self.get_env_var("SMTP_PORT", "587")),
            smtp_password=self.get_env_var("SMTP_PASSWORD", required=True),
            smtp_login=self.get_env_var("SMTP_LOGIN"),
        )

    def validate(self) -> bool:
        """Valide la configuration email."""
        if not self.config:
            return True  # Email optionnel

        if not self.config.smtp_password:
            return False
        return True
