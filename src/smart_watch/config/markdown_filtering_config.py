"""
Configuration filtrage markdown centralisée.
"""

from typing import Dict

from ..core.ErrorHandler import ErrorCategory, ErrorSeverity, handle_errors
from .base_config import BaseConfig


class MarkdownFilteringConfig:
    """Configuration pour le filtrage markdown par embeddings."""

    def __init__(self, config_data: Dict):
        # Détermine le fournisseur d'embeddings à utiliser (OPENAI, MISTRAL, LOCAL)
        self.embed_fournisseur = self._determine_embed_provider(config_data)

        # Configuration des embeddings selon le fournisseur
        if self.embed_fournisseur == "OPENAI":
            self.embed_modele = config_data.get("embed_modele_openai")
            self.embed_api_key = config_data.get("embed_api_key_openai")
            self.embed_base_url = config_data.get("embed_base_url_openai")
        elif self.embed_fournisseur == "MISTRAL":
            self.embed_modele = config_data.get("embed_modele_mistral")
            self.embed_api_key = config_data.get("embed_api_key_mistral")
            self.embed_base_url = None
        else:
            self.embed_modele = config_data.get("embed_modele_local")
            self.embed_api_key = None
            self.embed_base_url = None

        self.similarity_threshold = config_data.get("similarity_threshold")
        self.chunk_size = config_data.get("chunk_size")
        self.chunk_overlap = config_data.get("chunk_overlap")
        self.min_content_length = config_data.get("min_content_length")
        self.reference_phrases = config_data.get("reference_phrases")
        self.context_window_size = config_data.get("context_window_size", 1)

    def _determine_embed_provider(self, config_data: Dict) -> str:
        """
        Détermine le fournisseur d'embeddings à utiliser en fonction de la configuration.

        Args:
            config_data (Dict): Dictionnaire contenant les clés de configuration pour les API d'embeddings.

        Returns:
            str: Le nom du fournisseur d'embeddings sélectionné ("MISTRAL", "OPENAI" ou "LOCAL").

        Notes:
            - Si la variable d'environnement "EMBED_API_KEY_OPENAI" est présente, OpenAI est utilisé.
            - Sinon, si "EMBED_API_KEY_MISTRAL" est présente, Mistral est utilisé.
            - Sinon, le modèle local est utilisé par défaut.
        """
        if config_data.get("embed_api_key_openai"):
            return "OPENAI"
        elif config_data.get("embed_api_key_mistral"):
            return "MISTRAL"
        else:
            return "LOCAL"


class MarkdownFilteringConfigManager(BaseConfig):
    """Gestionnaire de configuration filtrage markdown."""

    def __init__(self, env_file=None):
        super().__init__(env_file)
        self.config = self._init_markdown_filtering_config()

    def _init_markdown_filtering_config(self) -> MarkdownFilteringConfig:
        """Initialise la configuration du filtrage markdown."""
        reference_phrases_str = self.get_env_var("REFERENCE_PHRASES")
        reference_phrases = [
            phrase.strip() for phrase in reference_phrases_str.split(";;")
        ]

        return MarkdownFilteringConfig(
            {
                "embed_api_key_openai": self.get_env_var("EMBED_API_KEY_OPENAI"),
                "embed_base_url_openai": self.get_env_var("EMBED_BASE_URL_OPENAI"),
                "embed_modele_openai": self.get_env_var("EMBED_MODELE_OPENAI"),
                "embed_api_key_mistral": self.get_env_var("EMBED_API_KEY_MISTRAL"),
                "embed_modele_mistral": self.get_env_var("EMBED_MODELE_MISTRAL"),
                "embed_modele_local": self.get_env_var("EMBED_MODELE_LOCAL"),
                "similarity_threshold": float(self.get_env_var("SIMILARITY_THRESHOLD")),
                "chunk_size": int(self.get_env_var("CHUNK_SIZE")),
                "chunk_overlap": int(self.get_env_var("CHUNK_OVERLAP")),
                "min_content_length": int(self.get_env_var("MIN_CONTENT_LENGTH")),
                "reference_phrases": reference_phrases,
                "context_window_size": int(
                    self.get_env_var("CONTEXT_WINDOW_SIZE", "1")
                ),
            }
        )

    @handle_errors(
        category=ErrorCategory.CONFIGURATION,
        severity=ErrorSeverity.MEDIUM,
        user_message="Erreur lors de la validation de la configuration markdown filtering",
        reraise=True,
    )
    def validate(self) -> bool:
        """Valide la configuration markdown filtering."""
        validation_errors = []

        # Si le fournisseur n'est pas local, vérifier la configuration API
        if self.config.embed_fournisseur != "LOCAL":
            if not self.config.embed_api_key:
                validation_errors.append(
                    "Aucune clé API embeddings configurée pour le fournisseur sélectionné."
                )
        # Si le fournisseur est local, vérifier que le modèle est spécifié
        elif not self.config.embed_modele:
            validation_errors.append(
                "EMBED_MODELE_LOCAL doit être spécifié pour le fournisseur LOCAL."
            )

        # Si OpenAI est configuré, vérifier l'URL de base et le modèle
        if self.config.embed_fournisseur == "OPENAI" and not self.config.embed_base_url:
            validation_errors.append(
                "EMBED_BASE_URL_OPENAI manquant alors que EMBED_API_KEY_OPENAI est configuré"
            )

        # Validation des autres paramètres
        if self.config.similarity_threshold is not None and not (
            0.0 <= self.config.similarity_threshold <= 1.0
        ):
            validation_errors.append(
                f"SIMILARITY_THRESHOLD doit être entre 0.0 et 1.0 (valeur actuelle: {self.config.similarity_threshold})"
            )

        if self.config.chunk_size is None or self.config.chunk_size <= 0:
            validation_errors.append(
                f"CHUNK_SIZE doit être un entier positif (valeur actuelle: {self.config.chunk_size})"
            )

        if self.config.chunk_overlap is None or self.config.chunk_overlap < 0:
            validation_errors.append(
                f"CHUNK_OVERLAP doit être un entier positif ou nul (valeur actuelle: {self.config.chunk_overlap})"
            )

        if (
            self.config.chunk_overlap is not None
            and self.config.chunk_size is not None
            and self.config.chunk_overlap >= self.config.chunk_size
        ):
            validation_errors.append("CHUNK_OVERLAP doit être inférieur à CHUNK_SIZE")

        if not self.config.reference_phrases:
            validation_errors.append("REFERENCE_PHRASES est vide ou non configuré")

        # Si des erreurs sont trouvées, lever une exception avec les détails
        if validation_errors:
            error_message = "Validation échouée:\n" + "\n".join(
                f"  - {error}" for error in validation_errors
            )
            raise ValueError(error_message)

        return True
