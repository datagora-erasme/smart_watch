# Documentation
# https://datagora-erasme.github.io/smart_watch/source/modules/config/processing_config.html

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

from ..core.ErrorHandler import ErrorCategory, ErrorSeverity, handle_errors
from .base_config import BaseConfig


@dataclass
class ProcessingConfig:
    """Représente la configuration pour le traitement des données.

    Attributes:
        nb_threads_url (int): le nombre de threads à utiliser pour le traitement des URLs.
        delai_entre_appels (float): le délai en secondes entre chaque appel d'URL.
        delai_en_cas_erreur (float): le délai en secondes à attendre en cas d'erreur.
        char_replacements (Dict[str, str]): un dictionnaire pour le remplacement de caractères lors du nettoyage.
    """

    nb_threads_url: int = 1
    delai_entre_appels: float = 1.0
    delai_en_cas_erreur: float = 5.0
    char_replacements: Dict[str, str] = field(default_factory=dict)


class ProcessingConfigManager(BaseConfig):
    """Gère la configuration de traitement de l'application.

    Cette classe charge la configuration depuis les variables d'environnement et la valide.

    Attributes:
        config (ProcessingConfig): l'objet de configuration de traitement.
    """

    def __init__(self, env_file: Optional[Path] = None) -> None:
        """Initialise le gestionnaire de configuration de traitement.

        Args:
            env_file (Optional[Path], optional): le chemin vers le fichier .env. Par défaut, None.
        """
        super().__init__(env_file)
        self.config: ProcessingConfig = self._init_processing_config()

    def _init_processing_config(self) -> ProcessingConfig:
        """Initialise l'objet de configuration de traitement.

        Charge les valeurs depuis les variables d'environnement et définit les remplacements de caractères par défaut.

        Returns:
            ProcessingConfig: un objet contenant la configuration de traitement.
        """
        # Remplacements de caractères pour le nettoyage markdown
        char_replacements: Dict[str, str] = {
            # Guillemets
            "«": '"',
            "»": '"',
            "“": '"',
            "”": '"',
            "‘": "'",
            "’": "'",
            # Tirets
            "–": "-",
            "—": "-",
            # Espaces spéciaux
            "\u00a0": " ",  # Espace insécable
            "\u2009": " ",  # Espace fin
            "\u200b": "",  # Espace sans chasse
            # Caractères de formatage markdown
            "*": " ",
            "_": " ",
            "`": " ",
            "+": " ",
            "\\": " ",
            # Nettoyage des espaces (ordre important)
            "\t": " ",  # Tabulations vers espaces
            "    ": " ",  # 4 espaces vers 1
            "   ": " ",  # 3 espaces vers 1
            "  ": " ",  # 2 espaces vers 1
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
        user_message="Erreur lors de la validation de la configuration de traitement.",
        reraise=True,
    )
    def validate(self) -> bool:
        """Valide la configuration de traitement.

        Vérifie que les valeurs de configuration sont dans des plages valides.

        Returns:
            bool: True si la configuration est valide.

        Raises:
            ValueError: si une ou plusieurs valeurs de configuration sont invalides.
        """
        validation_errors: list[str] = []

        if self.config.nb_threads_url <= 0:
            validation_errors.append(
                "NB_THREADS_URL doit être un entier positif "
                f"(valeur: {self.config.nb_threads_url})."
            )

        if self.config.delai_entre_appels < 0:
            validation_errors.append(
                "DELAI_ENTRE_APPELS doit être un nombre positif ou nul "
                f"(valeur: {self.config.delai_entre_appels})."
            )

        if self.config.delai_en_cas_erreur < 0:
            validation_errors.append(
                "DELAI_EN_CAS_ERREUR doit être un nombre positif ou nul "
                f"(valeur: {self.config.delai_en_cas_erreur})."
            )

        if not self.config.char_replacements:
            validation_errors.append(
                "Le dictionnaire char_replacements ne peut pas être vide."
            )

        if validation_errors:
            error_message = "Validation de la configuration échouée:\n" + "\n".join(
                f"  - {error}" for error in validation_errors
            )
            raise ValueError(error_message)

        return True
