"""
Configuration filtrage markdown centralisée.
"""

from typing import Dict

from .base_config import BaseConfig


class MarkdownFilteringConfig:
    """Configuration pour le filtrage markdown par embeddings."""

    def __init__(self, config_data: Dict):
        # Modèle d'embeddings à utiliser
        self.embedding_model = config_data.get("embedding_model", "nomic-embed-text")

        # Seuil de similarité pour considérer une phrase comme pertinente
        self.similarity_threshold = config_data.get("similarity_threshold", 0.25)

        # Taille de la fenêtre de contexte autour des phrases pertinentes
        self.context_window = config_data.get("context_window", 1)

        # Taille minimale du contenu markdown pour déclencher le filtrage
        self.min_content_length = config_data.get("min_content_length", 50)

        # Phrases de référence pour identifier les sections d'horaires
        self.reference_phrases = config_data.get("reference_phrases", [])


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
                "embedding_model": self.get_env_var(
                    "EMBEDDING_MODEL", "nomic-embed-text"
                ),
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

    def validate(self) -> bool:
        """Valide la configuration markdown filtering."""
        if not self.config.embedding_model:
            return False
        if not (0.0 <= self.config.similarity_threshold <= 1.0):
            return False
        if self.config.context_window < 0:
            return False
        if not self.config.reference_phrases:
            return False
        return True
