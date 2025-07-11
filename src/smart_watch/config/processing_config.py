"""
Configuration traitement centralisée.
"""

from dataclasses import dataclass
from typing import Dict

from .base_config import BaseConfig


@dataclass
class ProcessingConfig:
    """Configuration traitement."""

    nb_threads_url: int = 5
    delai_entre_appels: float = 1.0
    delai_en_cas_erreur: float = 5.0
    char_replacements: Dict[str, str] = None


class ProcessingConfigManager(BaseConfig):
    """Gestionnaire de configuration traitement."""

    def __init__(self, env_file=None):
        super().__init__(env_file)
        self.config = self._init_processing_config()

    def _init_processing_config(self) -> ProcessingConfig:
        """Initialise la configuration de traitement."""
        # Remplacements de caractères pour le nettoyage markdown
        char_replacements = {
            # Guillemets
            "«": '"',
            "»": '"',
            """: '"',
            """: '"',
            "'": "'",
            "'": "'",
            # Tirets
            "–": "-",
            "—": "-",
            # Espaces spéciaux
            "\u00a0": " ",  # Non-breaking space
            "\u2009": " ",  # Thin space
            "\u200b": "",  # Zero-width space
            # Caractères de formatage markdown
            "*": " ",
            "_": " ",
            "`": " ",
            "+": " ",
            "\\": " ",
            # Nettoyage des espaces (ordre important pour éviter les récursions infinies)
            "\t": " ",  # Tabulations vers espaces
            "    ": " ",  # 4 espaces vers 1 (en premier)
            "   ": " ",  # 3 espaces vers 1
            "  ": " ",  # 2 espaces vers 1 (en dernier)
            " \n": "\n",  # Espaces en fin de ligne
        }

        return ProcessingConfig(
            nb_threads_url=int(self.get_env_var("NB_THREADS_URL", "100")),
            delai_entre_appels=float(self.get_env_var("DELAI_ENTRE_APPELS", "2.0")),
            delai_en_cas_erreur=float(self.get_env_var("DELAI_EN_CAS_ERREUR", "30")),
            char_replacements=char_replacements,
        )

    def validate(self) -> bool:
        """Valide la configuration traitement."""
        if self.config.nb_threads_url <= 0:
            return False
        if self.config.delai_entre_appels < 0:
            return False
        return True
