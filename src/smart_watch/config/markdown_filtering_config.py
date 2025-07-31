# Documentation
# https://datagora-erasme.github.io/smart_watch/source/modules/config/markdown_filtering_config.html

from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.ErrorHandler import ErrorCategory, ErrorSeverity, handle_errors
from .base_config import BaseConfig


class MarkdownFilteringConfig:
    """Encapsule la configuration pour le filtrage de contenu Markdown.

    Cette classe stocke les paramètres spécifiques au filtrage sémantique de documents Markdown, y compris la configuration du fournisseur d'embeddings et les seuils de similarité.

    Attributes:
        embed_fournisseur (str): le fournisseur d'embeddings à utiliser ("OPENAI", "MISTRAL", ou "LOCAL").
        embed_modele (Optional[str]): le modèle d'embedding à utiliser.
        embed_api_key (Optional[str]): la clé API pour le service d'embedding.
        embed_base_url (Optional[str]): l'URL de base pour le service d'embedding (spécifique à OpenAI).
        similarity_threshold (Optional[float]): le seuil de similarité pour filtrer les contenus.
        chunk_size (Optional[int]): la taille des morceaux (chunks) de texte.
        chunk_overlap (Optional[int]): le chevauchement entre les morceaux de texte.
        min_content_length (Optional[int]): la longueur minimale du contenu pour être traité.
        reference_phrases (Optional[List[str]]): les phrases de référence pour la comparaison de similarité.
        context_window_size (int): la taille de la fenêtre de contexte pour l'analyse.
    """

    def __init__(self, config_data: Dict[str, Any]) -> None:
        """Initialise l'objet de configuration de filtrage Markdown.

        Args:
            config_data (Dict[str, Any]): un dictionnaire contenant les données de configuration, chargées depuis des variables d'environnement.
        """
        self.embed_fournisseur: str = self._determine_embed_provider(config_data)

        if self.embed_fournisseur == "OPENAI":
            self.embed_modele: Optional[str] = config_data.get("embed_modele_openai")
            self.embed_api_key: Optional[str] = config_data.get("embed_api_key_openai")
            self.embed_base_url: Optional[str] = config_data.get(
                "embed_base_url_openai"
            )
        elif self.embed_fournisseur == "MISTRAL":
            self.embed_modele: Optional[str] = config_data.get("embed_modele_mistral")
            self.embed_api_key: Optional[str] = config_data.get("embed_api_key_mistral")
            self.embed_base_url: Optional[str] = None
        else:  # LOCAL
            self.embed_modele: Optional[str] = config_data.get("embed_modele_local")
            self.embed_api_key: Optional[str] = None
            self.embed_base_url: Optional[str] = None

        self.similarity_threshold: Optional[float] = config_data.get(
            "similarity_threshold"
        )
        self.chunk_size: Optional[int] = config_data.get("chunk_size")
        self.chunk_overlap: Optional[int] = config_data.get("chunk_overlap")
        self.min_content_length: Optional[int] = config_data.get("min_content_length")
        self.reference_phrases: Optional[List[str]] = config_data.get(
            "reference_phrases"
        )
        self.context_window_size: int = config_data.get("context_window_size", 1)

    def _determine_embed_provider(self, config_data: Dict[str, Any]) -> str:
        """Détermine le fournisseur d'embeddings à partir de la configuration.

        La sélection est basée sur la présence de clés API spécifiques dans l'ordre suivant : OpenAI, Mistral, puis Local par défaut.

        Args:
            config_data (Dict[str, Any]): le dictionnaire de configuration contenant les clés API.

        Returns:
            str: le nom du fournisseur d'embeddings ("OPENAI", "MISTRAL", ou "LOCAL").
        """
        if config_data.get("embed_api_key_openai"):
            return "OPENAI"
        if config_data.get("embed_api_key_mistral"):
            return "MISTRAL"
        return "LOCAL"


class MarkdownFilteringConfigManager(BaseConfig):
    """Gère le chargement et la validation de la configuration de filtrage Markdown.

    Cette classe hérite de `BaseConfig` pour charger les variables d'environnement et initialise un objet `MarkdownFilteringConfig` validé.

    Attributes:
        config (MarkdownFilteringConfig): l'objet de configuration contenant tous les paramètres de filtrage.
    """

    def __init__(self, env_file: Optional[Path] = None) -> None:
        """Initialise le gestionnaire de configuration.

        Args:
            env_file (Optional[Path], optional): le chemin vers un fichier .env. Par défaut, None.
        """
        super().__init__(env_file)
        self.config: MarkdownFilteringConfig = self._init_markdown_filtering_config()

    def _init_markdown_filtering_config(self) -> MarkdownFilteringConfig:
        """Initialise l'objet de configuration à partir des variables d'environnement.

        Returns:
            MarkdownFilteringConfig: un objet de configuration initialisé.
        """
        reference_phrases_str = self.get_env_var("REFERENCE_PHRASES", "")
        reference_phrases: List[str] = [
            phrase.strip()
            for phrase in reference_phrases_str.split(";;")
            if phrase.strip()
        ]

        return MarkdownFilteringConfig(
            {
                "embed_api_key_openai": self.get_env_var("EMBED_API_KEY_OPENAI"),
                "embed_base_url_openai": self.get_env_var("EMBED_BASE_URL_OPENAI"),
                "embed_modele_openai": self.get_env_var("EMBED_MODELE_OPENAI"),
                "embed_api_key_mistral": self.get_env_var("EMBED_API_KEY_MISTRAL"),
                "embed_modele_mistral": self.get_env_var("EMBED_MODELE_MISTRAL"),
                "embed_modele_local": self.get_env_var("EMBED_MODELE_LOCAL"),
                "similarity_threshold": float(
                    self.get_env_var("SIMILARITY_THRESHOLD", "0.0")
                ),
                "chunk_size": int(self.get_env_var("CHUNK_SIZE", "0")),
                "chunk_overlap": int(self.get_env_var("CHUNK_OVERLAP", "0")),
                "min_content_length": int(self.get_env_var("MIN_CONTENT_LENGTH", "0")),
                "reference_phrases": reference_phrases,
                "context_window_size": int(
                    self.get_env_var("CONTEXT_WINDOW_SIZE", "1")
                ),
            }
        )

    @handle_errors(
        category=ErrorCategory.CONFIGURATION,
        severity=ErrorSeverity.MEDIUM,
        user_message="Erreur lors de la validation de la configuration du filtrage Markdown.",
        reraise=True,
    )
    def validate(self) -> bool:
        """Valide la configuration chargée.

        Vérifie la cohérence des paramètres, comme la présence de clés API pour les fournisseurs distants et la validité des valeurs numériques.

        Returns:
            bool: True si la configuration est valide.

        Raises:
            ValueError: si une ou plusieurs erreurs de validation sont détectées.
        """
        validation_errors: List[str] = []

        if self.config.embed_fournisseur != "LOCAL":
            if not self.config.embed_api_key:
                validation_errors.append(
                    f"La clé API pour le fournisseur '{self.config.embed_fournisseur}' est manquante."
                )
        elif not self.config.embed_modele:
            validation_errors.append(
                "Le modèle d'embedding local (EMBED_MODELE_LOCAL) doit être spécifié."
            )

        if self.config.embed_fournisseur == "OPENAI" and not self.config.embed_base_url:
            validation_errors.append(
                "L'URL de base (EMBED_BASE_URL_OPENAI) est requise pour OpenAI."
            )

        if self.config.similarity_threshold is not None and not (
            0.0 <= self.config.similarity_threshold <= 1.0
        ):
            validation_errors.append(
                f"Le seuil de similarité ({self.config.similarity_threshold}) doit être compris entre 0.0 et 1.0."
            )

        if self.config.chunk_size is None or self.config.chunk_size <= 0:
            validation_errors.append(
                f"La taille des chunks ({self.config.chunk_size}) doit être un entier positif."
            )

        if self.config.chunk_overlap is None or self.config.chunk_overlap < 0:
            validation_errors.append(
                f"Le chevauchement des chunks ({self.config.chunk_overlap}) doit être un entier positif ou nul."
            )

        if (
            self.config.chunk_overlap is not None
            and self.config.chunk_size is not None
            and self.config.chunk_overlap >= self.config.chunk_size
        ):
            validation_errors.append(
                "Le chevauchement des chunks doit être inférieur à leur taille."
            )

        if not self.config.reference_phrases:
            validation_errors.append(
                "La liste des phrases de référence (REFERENCE_PHRASES) est vide."
            )

        if validation_errors:
            error_message = "Erreurs de validation de la configuration:\n" + "\n".join(
                f"  - {error}" for error in validation_errors
            )
            raise ValueError(error_message)

        return True
