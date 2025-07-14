"""
Configuration LLM centralisée.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ..core.ErrorHandler import ErrorCategory, ErrorSeverity, handle_errors
from .base_config import BaseConfig

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """Configuration LLM simplifiée."""

    fournisseur: str
    modele: str
    api_key: str
    base_url: Optional[str] = None
    temperature: float = 0
    timeout: int = 30


class LLMConfigManager(BaseConfig):
    """Gestionnaire de configuration LLM."""

    def __init__(self, env_file: Path = None):
        super().__init__(env_file)
        try:
            self.config = self._init_llm_config()
        except Exception as e:
            # Gestion d'erreur simplifiée pour éviter les problèmes d'initialisation
            logger.error(f"Erreur initialisation config LLM: {e}")
            # Configuration par défaut pour permettre au système de démarrer
            self.config = self._get_default_config()

    def _init_llm_config(self) -> LLMConfig:
        """Initialise la configuration LLM avec détection automatique."""
        # Tentative OpenAI/compatible
        llm_api_key_openai = self.get_env_var("LLM_API_KEY_OPENAI")
        llm_base_url_openai = self.get_env_var("LLM_BASE_URL_OPENAI")

        # Tentative Mistral
        llm_api_key_mistral = self.get_env_var("LLM_API_KEY_MISTRAL")

        if llm_api_key_openai:
            return LLMConfig(
                fournisseur="OPENAI",
                modele=self.get_env_var("LLM_MODELE_OPENAI", required=True),
                api_key=llm_api_key_openai,
                base_url=llm_base_url_openai,
                temperature=float(self.get_env_var("LLM_TEMPERATURE", "0")),
                timeout=int(self.get_env_var("LLM_TIMEOUT", "30")),
            )
        elif llm_api_key_mistral:
            return LLMConfig(
                fournisseur="MISTRAL",
                modele=self.get_env_var("LLM_MODELE_MISTRAL", required=True),
                api_key=llm_api_key_mistral,
                temperature=float(self.get_env_var("LLM_TEMPERATURE", "0")),
                timeout=int(self.get_env_var("LLM_TIMEOUT", "30")),
            )
        else:
            raise ValueError(
                "Aucune clé API LLM trouvée (LLM_API_KEY_OPENAI ou LLM_API_KEY_MISTRAL)"
            )

    def _get_default_config(self):
        """Retourne une configuration par défaut en cas d'erreur."""
        return type(
            "DefaultConfig",
            (),
            {
                "fournisseur": "OPENAI",
                "modele": "gpt-3.5-turbo",
                "api_key": "",
                "base_url": "http://localhost:8000",
                "temperature": 0.1,
                "timeout": 30,
            },
        )()

    @handle_errors(
        category=ErrorCategory.CONFIGURATION,
        severity=ErrorSeverity.HIGH,
        user_message="Erreur lors de la validation de la configuration LLM",
        reraise=True,
    )
    def validate(self) -> bool:
        """Valide la configuration LLM."""
        validation_errors = []

        # Vérifier la clé API
        if not self.config.api_key:
            validation_errors.append("Clé API LLM manquante")

        # Vérifier le modèle
        if not self.config.modele:
            validation_errors.append("Modèle LLM manquant")

        # Vérifier les paramètres numériques
        if not (0.0 <= self.config.temperature <= 2.0):
            validation_errors.append(
                f"LLM_TEMPERATURE doit être entre 0.0 et 2.0 (valeur actuelle: {self.config.temperature})"
            )

        if self.config.timeout <= 0:
            validation_errors.append(
                f"LLM_TIMEOUT doit être positif (valeur actuelle: {self.config.timeout})"
            )

        # Vérifier l'URL de base pour OpenAI
        if self.config.fournisseur == "OPENAI" and self.config.base_url:
            import urllib.parse

            parsed = urllib.parse.urlparse(self.config.base_url)
            if not parsed.scheme or not parsed.netloc:
                validation_errors.append(
                    f"LLM_BASE_URL_OPENAI invalide: {self.config.base_url}"
                )

        # Si des erreurs sont trouvées, lever une exception avec les détails
        if validation_errors:
            error_message = "Validation échouée:\n" + "\n".join(
                f"  - {error}" for error in validation_errors
            )
            raise ValueError(error_message)

        return True
