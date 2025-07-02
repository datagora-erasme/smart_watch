"""
Configuration LLM centralisée.
"""

from dataclasses import dataclass
from typing import Optional

from .base_config import BaseConfig


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

    def __init__(self, env_file=None):
        super().__init__(env_file)
        self.config = self._init_llm_config()

    def _init_llm_config(self) -> LLMConfig:
        """Initialise la configuration LLM avec détection automatique."""
        # Tentative OpenAI/compatible
        api_key_openai = self.get_env_var("API_KEY_OPENAI")
        base_url_openai = self.get_env_var("BASE_URL_OPENAI")

        # Tentative Mistral
        api_key_mistral = self.get_env_var("API_KEY_MISTRAL")

        if api_key_openai:
            return LLMConfig(
                fournisseur="OPENAI",
                modele=self.get_env_var("MODELE_OPENAI", required=True),
                api_key=api_key_openai,
                base_url=base_url_openai,
                temperature=float(self.get_env_var("LLM_TEMPERATURE", "0")),
                timeout=int(self.get_env_var("LLM_TIMEOUT", "30")),
            )
        elif api_key_mistral:
            return LLMConfig(
                fournisseur="MISTRAL",
                modele=self.get_env_var("MODELE_MISTRAL", required=True),
                api_key=api_key_mistral,
                temperature=float(self.get_env_var("LLM_TEMPERATURE", "0")),
                timeout=int(self.get_env_var("LLM_TIMEOUT", "30")),
            )
        else:
            raise ValueError(
                "Aucune clé API LLM trouvée (API_KEY_OPENAI ou API_KEY_MISTRAL)"
            )

    def validate(self) -> bool:
        """Valide la configuration LLM."""
        if not self.config.api_key:
            return False
        if not self.config.modele:
            return False
        return True
