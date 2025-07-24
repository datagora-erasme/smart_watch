"""
Configuration traitement centralisée.
"""

from dataclasses import dataclass
from typing import Dict

from ..core.ErrorHandler import ErrorCategory, ErrorSeverity, handle_errors
from .base_config import BaseConfig


@dataclass
class ProcessingConfig:
    """Configuration traitement."""

    nb_threads_url: int = 1
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
            nb_threads_url=int(self.get_env_var("NB_THREADS_URL")),
            delai_entre_appels=float(self.get_env_var("DELAI_ENTRE_APPELS")),
            delai_en_cas_erreur=float(self.get_env_var("DELAI_EN_CAS_ERREUR")),
            char_replacements=char_replacements,
        )

    @handle_errors(
        category=ErrorCategory.CONFIGURATION,
        severity=ErrorSeverity.MEDIUM,
        user_message="Erreur lors de la validation de la configuration processing",
        reraise=True,
    )
    def validate(self) -> bool:
        """Valide la configuration traitement."""
        validation_errors = []

        if self.config.nb_threads_url <= 0:
            validation_errors.append(
                f"NB_THREADS_URL doit être positif (valeur actuelle: {self.config.nb_threads_url})"
            )

        if self.config.delai_entre_appels < 0:
            validation_errors.append(
                f"DELAI_ENTRE_APPELS doit être positif ou nul (valeur actuelle: {self.config.delai_entre_appels})"
            )

        if self.config.delai_en_cas_erreur < 0:
            validation_errors.append(
                f"DELAI_EN_CAS_ERREUR doit être positif ou nul (valeur actuelle: {self.config.delai_en_cas_erreur})"
            )

        # Validation des remplacements de caractères
        if not self.config.char_replacements:
            validation_errors.append("char_replacements ne peut pas être vide")

        # Si des erreurs sont trouvées, lever une exception avec les détails
        if validation_errors:
            error_message = "Validation échouée:\n" + "\n".join(
                f"  - {error}" for error in validation_errors
            )
            raise ValueError(error_message)

        return True
