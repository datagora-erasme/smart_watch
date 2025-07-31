# Documentation
# https://datagora-erasme.github.io/smart_watch/source/modules/config/llm_config.html

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ..core.ErrorHandler import ErrorCategory, ErrorSeverity, handle_errors
from .base_config import BaseConfig

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """Représente la configuration pour un client LLM.

    Attributes:
        fournisseur (str): Le nom du fournisseur de LLM ("OPENAI", "MISTRAL", "LOCAL").
        modele (str): Le nom du modèle de LLM à utiliser.
        api_key (Optional[str]): La clé API pour accéder au service du LLM.
        base_url (Optional[str]): L'URL de base pour les appels API, principalement pour les fournisseurs compatibles OpenAI.
        temperature (float): La température pour la génération de texte, contrôle le caractère aléatoire.
        timeout (int): Le délai d'attente en secondes pour les requêtes API.
    """

    fournisseur: str
    modele: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0
    timeout: int = 30


class LLMConfigManager(BaseConfig):
    """Gère la configuration du client LLM à partir des variables d'environnement.

    Cette classe lit les variables d'environnement pour configurer le client LLM, en détectant automatiquement le fournisseur (OpenAI, Mistral, ou local) en fonction des clés API disponibles.

    Attributes:
        config (LLMConfig): L'objet de configuration LLM initialisé.
    """

    def __init__(self, env_file: Optional[Path] = None) -> None:
        """Initialise le gestionnaire de configuration LLM.

        Args:
            env_file (Optional[Path]): Le chemin vers un fichier .env personnalisé. Si non fourni, utilise les variables d'environnement système.
        """
        super().__init__(env_file)
        try:
            self.config = self._init_llm_config()
        except Exception as e:
            # Gestion d'erreur simplifiée pour éviter les problèmes d'initialisation
            logger.error(f"Erreur initialisation config LLM: {e}")
            # Configuration par défaut pour permettre au système de démarrer
            self.config = self._get_default_config()

    def _init_llm_config(self) -> LLMConfig:
        """Initialise la configuration LLM en détectant le fournisseur.

        La méthode recherche les clés API pour OpenAI, puis Mistral, et enfin un modèle local. Le premier trouvé est utilisé pour la configuration.

        Returns:
            LLMConfig: L'objet de configuration LLM initialisé.

        Raises:
            ValueError: Si aucune configuration de LLM (OpenAI, Mistral) ou de modèle d'embedding local n'est trouvée.
        """
        # Tentative OpenAI/compatible
        llm_api_key_openai = self.get_env_var("LLM_API_KEY_OPENAI")
        llm_base_url_openai = self.get_env_var("LLM_BASE_URL_OPENAI")

        # Tentative Mistral
        llm_api_key_mistral = self.get_env_var("LLM_API_KEY_MISTRAL")

        # Tentative modèle local
        embed_modele_local = self.get_env_var("EMBED_MODELE_LOCAL")

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
        elif embed_modele_local:
            return LLMConfig(
                fournisseur="LOCAL",
                modele=embed_modele_local,
                api_key=None,  # Pas de clé API pour le modèle local
            )
        else:
            raise ValueError(
                "Aucune configuration LLM ou embedding local trouvée."
                "Veuillez définir LLM_API_KEY_OPENAI, LLM_API_KEY_MISTRAL, ou EMBED_MODELE_LOCAL."
            )

    def _get_default_config(self) -> LLMConfig:
        """Retourne une configuration LLM par défaut.

        Cette configuration est utilisée comme solution de repli en cas d'échec de l'initialisation pour permettre au système de démarrer sans planter.

        Returns:
            LLMConfig: Une configuration LLM locale par défaut.
        """
        return LLMConfig(
            fournisseur="LOCAL",
            modele="paraphrase-multilingual-mpnet-base-v2",
            api_key=None,
            base_url=None,
            temperature=0.1,
            timeout=30,
        )

    @handle_errors(
        category=ErrorCategory.CONFIGURATION,
        severity=ErrorSeverity.HIGH,
        user_message="Erreur lors de la validation de la configuration LLM",
        reraise=True,
    )
    def validate(self) -> bool:
        """Valide la configuration LLM chargée.

        Vérifie que les paramètres essentiels sont présents et valides, comme la clé API pour les fournisseurs distants, le nom du modèle, et les valeurs de température et de timeout.

        Returns:
            bool: True si la configuration est valide.

        Raises:
            ValueError: Si la validation échoue, avec un message détaillant les erreurs.
        """
        validation_errors = []

        # Si le fournisseur n'est pas local, vérifier la clé API
        if self.config.fournisseur != "LOCAL" and not self.config.api_key:
            validation_errors.append(
                "Clé API LLM manquante pour le fournisseur configuré"
            )

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
