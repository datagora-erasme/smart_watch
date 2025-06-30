"""
Configuration filtrage markdown centralisée.
"""

from typing import Dict

from .base_config import BaseConfig


class MarkdownFilteringConfig:
    """Configuration pour le filtrage markdown par embeddings."""

    def __init__(self, config_data: Dict):
        # Modèle d'embeddings à utiliser
        self.embedding_model = config_data.get(
            "embedding_model", "paraphrase-multilingual-MiniLM-L12-v2"
        )

        # Nombre de sections à sélectionner
        self.max_sections = config_data.get("max_sections", 5)

        # Taille minimale d'une section pour être considérée
        self.min_section_length = config_data.get("min_section_length", 20)

        # Taille minimale du contenu markdown pour déclencher le filtrage
        self.min_content_length = config_data.get("min_content_length", 50)

        # Headers pour le splitting markdown
        self.headers_to_split = config_data.get(
            "headers_to_split",
            [
                ("#", "Header 1"),
                ("##", "Header 2"),
                ("###", "Header 3"),
                ("####", "Header 4"),
            ],
        )

        # Phrases de référence pour identifier les sections d'horaires
        self.reference_phrases = config_data.get("reference_phrases", [])


class MarkdownFilteringConfigManager(BaseConfig):
    """Gestionnaire de configuration filtrage markdown."""

    def __init__(self, env_file=None):
        super().__init__(env_file)
        self.config = self._init_markdown_filtering_config()

    def _init_markdown_filtering_config(self) -> MarkdownFilteringConfig:
        """Initialise la configuration du filtrage markdown."""
        default_phrases = "horaires d'ouverture et de fermeture;;heures d'ouverture quotidiennes;;jours et heures d'ouverture;;horaires de service;;horaires de fonctionnement;;horaires des différentes sections;;horaires d'ouverture pour les médiathèques;;horaires des bibliothèques;;horaires des centres culturels;;horaires des espaces multimédias;;horaires des services publics;;horaires des jours fériés;;horaires des vacances scolaires;;lundi mardi mercredi jeudi vendredi samedi dimanche;;ouvert fermé;;de 9h à 18h;;de 14h à 19h;;planning hebdomadaire"
        reference_phrases_str = self.get_env_var("REFERENCE_PHRASES", default_phrases)
        reference_phrases = [
            phrase.strip() for phrase in reference_phrases_str.split(";;")
        ]

        return MarkdownFilteringConfig(
            {
                "embedding_model": self.get_env_var(
                    "EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2"
                ),
                "max_sections": int(self.get_env_var("MAX_SECTIONS", "5")),
                "min_section_length": int(self.get_env_var("MIN_SECTION_LENGTH", "20")),
                "min_content_length": int(self.get_env_var("MIN_CONTENT_LENGTH", "50")),
                "headers_to_split": [
                    ("#", "Header 1"),
                    ("##", "Header 2"),
                    ("###", "Header 3"),
                    ("####", "Header 4"),
                ],
                "reference_phrases": reference_phrases,
            }
        )

    def validate(self) -> bool:
        """Valide la configuration markdown filtering."""
        if not self.config.embedding_model:
            return False
        if self.config.max_sections <= 0:
            return False
        if not self.config.reference_phrases:
            return False
        return True
