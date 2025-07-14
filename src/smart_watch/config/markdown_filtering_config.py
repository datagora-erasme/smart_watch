"""
Configuration filtrage markdown centralisée.
"""

from typing import Dict

from ..core.ErrorHandler import ErrorCategory, ErrorSeverity, handle_errors
from .base_config import BaseConfig


class MarkdownFilteringConfig:
    """Configuration pour le filtrage markdown par embeddings."""

    def __init__(self, config_data: Dict):
        # Paramètres pour les embeddings OpenAI
        self.embed_api_key_openai = config_data.get("embed_api_key_openai")
        self.embed_base_url_openai = config_data.get("embed_base_url_openai")
        self.embed_modele_openai = config_data.get(
            "embed_modele_openai", "nomic-embed-text"
        )

        # Paramètres pour les embeddings Mistral
        self.embed_api_key_mistral = config_data.get("embed_api_key_mistral")
        self.embed_modele_mistral = config_data.get(
            "embed_modele_mistral", "nomic-embed-text"
        )

        # Seuil de similarité pour considérer une phrase comme pertinente
        self.similarity_threshold = config_data.get("similarity_threshold", 0.25)

        # Taille de la fenêtre de contexte autour des phrases pertinentes
        self.context_window = config_data.get("context_window", 1)

        # Taille minimale du contenu markdown pour déclencher le filtrage
        self.min_content_length = config_data.get("min_content_length", 50)

        # Phrases de référence pour identifier les sections d'horaires
        self.reference_phrases = config_data.get("reference_phrases", [])

        # Détermine le fournisseur d'embeddings à utiliser (OPENAI ou MISTRAL)
        self.embed_fournisseur = self._determine_embed_provider()

    def _determine_embed_provider(self) -> str:
        """Détermine le fournisseur d'embeddings à utiliser en fonction des clés API disponibles."""
        if self.embed_api_key_mistral:
            return "MISTRAL"
        elif self.embed_api_key_openai:
            return "OPENAI"
        else:
            # Valeur par défaut si aucune clé n'est définie
            return "OPENAI"


class MarkdownFilteringConfigManager(BaseConfig):
    """Gestionnaire de configuration filtrage markdown."""

    def __init__(self, env_file=None):
        super().__init__(env_file)
        self.config = self._init_markdown_filtering_config()

    def _init_markdown_filtering_config(self) -> MarkdownFilteringConfig:
        """Initialise la configuration du filtrage markdown."""
        default_phrases = "horaires d'ouverture et de fermeture"
        reference_phrases_str = self.get_env_var("REFERENCE_PHRASES", default_phrases)
        reference_phrases = [
            phrase.strip() for phrase in reference_phrases_str.split(";;")
        ]

        return MarkdownFilteringConfig(
            {
                # Paramètres embeddings OpenAI
                "embed_api_key_openai": self.get_env_var("EMBED_API_KEY_OPENAI", ""),
                "embed_base_url_openai": self.get_env_var("EMBED_BASE_URL_OPENAI", ""),
                "embed_modele_openai": self.get_env_var(
                    "EMBED_MODELE_OPENAI", "nomic-embed-text"
                ),
                # Paramètres embeddings Mistral
                "embed_api_key_mistral": self.get_env_var("EMBED_API_KEY_MISTRAL", ""),
                "embed_modele_mistral": self.get_env_var(
                    "EMBED_MODELE_MISTRAL", "nomic-embed-text"
                ),
                # Paramètres généraux de filtrage
                "similarity_threshold": float(
                    self.get_env_var("SIMILARITY_THRESHOLD", "0.4")
                ),
                "context_window": int(self.get_env_var("CONTEXT_WINDOW", "1")),
                "min_content_length": int(
                    self.get_env_var("MIN_CONTENT_LENGTH", "1000")
                ),
                "reference_phrases": reference_phrases,
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

        # Vérifie qu'au moins un fournisseur d'embeddings est configuré
        if not (self.config.embed_api_key_openai or self.config.embed_api_key_mistral):
            validation_errors.append(
                "Aucune clé API embeddings configurée (EMBED_API_KEY_OPENAI ou EMBED_API_KEY_MISTRAL)"
            )

        # Si OpenAI est configuré, vérifier l'URL de base et le modèle
        if self.config.embed_api_key_openai and not self.config.embed_base_url_openai:
            validation_errors.append(
                "EMBED_BASE_URL_OPENAI manquant alors que EMBED_API_KEY_OPENAI est configuré"
            )

        # Validation des autres paramètres
        if not (0.0 <= self.config.similarity_threshold <= 1.0):
            validation_errors.append(
                f"SIMILARITY_THRESHOLD doit être entre 0.0 et 1.0 (valeur actuelle: {self.config.similarity_threshold})"
            )

        if self.config.context_window < 0:
            validation_errors.append(
                f"CONTEXT_WINDOW doit être positif (valeur actuelle: {self.config.context_window})"
            )

        if not self.config.reference_phrases:
            validation_errors.append("REFERENCE_PHRASES est vide ou non configuré")

        # Si des erreurs sont trouvées, lever une exception avec les détails
        if validation_errors:
            error_message = "Validation échouée:\n" + "\n".join(
                f"  - {error}" for error in validation_errors
            )
            raise ValueError(error_message)

        return True
