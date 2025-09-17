"""
Processeur pour filtrer le contenu markdown et extraire les sections pertinentes aux horaires.
Utilise des embeddings sémantiques pour identifier les sections les plus pertinentes.
"""

import os
from typing import List, Optional, Tuple

import nltk
import numpy as np
from fastembed import TextEmbedding

from ..core.ConfigManager import ConfigManager
from ..core.ErrorHandler import ErrorCategory, ErrorSeverity, handle_errors
from ..core.LLMClient import LLMResponse, MistralAPIClient, OpenAICompatibleClient
from ..data_models.schema_bdd import Lieux, ResultatsExtraction
from ..processing.database_processor import DatabaseProcessor


class MarkdownProcessor:
    """Processeur pour filtrer le contenu markdown et extraire les sections pertinentes aux horaires."""

    def __init__(self, config: ConfigManager, logger):
        self.config = config
        self.logger = logger
        self.total_co2_emissions = (
            0.0  # Accumulation des émissions pour cette exécution
        )
        self.reference_embeddings = None  # Pour stocker les embeddings de référence
        self.local_embed_model = None  # Pour le modèle local

        # Initialisation du client pour les embeddings selon le fournisseur configuré
        try:
            self._init_embedding_client()
            self.logger.info(
                f"Client embeddings initialisé avec fournisseur: {self.config.markdown_filtering.embed_fournisseur}"
            )
        except Exception as e:
            self.logger.error(f"Erreur initialisation client embeddings: {e}")
            self.embed_client = None

        # Phrases de référence pour identifier les sections d'horaires (depuis la config)
        self.reference_phrases = self.config.markdown_filtering.reference_phrases

        if self.config.markdown_filtering.sentencizer == "NLTK":
            try:
                nltk.data.find("tokenizers/punkt")
                self.logger.info("NLTK 'punkt' tokenizer is already downloaded.")
            except LookupError:
                self.logger.info("Downloading NLTK 'punkt' tokenizer...")
                nltk.download("punkt")
                self.logger.info("NLTK 'punkt' tokenizer downloaded successfully.")

    def _init_embedding_client(self):
        """Initialise le client approprié pour les embeddings selon la configuration."""
        embed_config = self.config.markdown_filtering

        if embed_config.embed_fournisseur == "LOCAL":
            if embed_config.embed_modele:
                try:
                    # Calcul dynamique du nombre de threads
                    cpu_count = os.cpu_count() or 1
                    threads = max(1, cpu_count // 4)

                    self.local_embed_model = TextEmbedding(
                        model_name=embed_config.embed_modele, threads=threads
                    )
                    self.logger.info(
                        f"Modèle d'embedding local chargé: {embed_config.embed_modele} avec {threads} threads."
                    )
                    self.embed_client = None
                except Exception as e:
                    self.logger.error(f"Erreur chargement modèle local: {e}")
                    raise
        elif embed_config.embed_fournisseur == "MISTRAL":
            if embed_config.embed_api_key and embed_config.embed_modele:
                self.embed_client = MistralAPIClient(
                    api_key=embed_config.embed_api_key,
                    model=embed_config.embed_modele,
                    timeout=30,
                )
                self.logger.debug(
                    f"Client embeddings Mistral initialisé avec modèle {embed_config.embed_modele}"
                )
        elif embed_config.embed_fournisseur == "OPENAI":
            if (
                embed_config.embed_api_key
                and embed_config.embed_modele
                and embed_config.embed_base_url
            ):
                self.embed_client = OpenAICompatibleClient(
                    api_key=embed_config.embed_api_key,
                    model=embed_config.embed_modele,
                    base_url=embed_config.embed_base_url,
                    timeout=30,
                )
                self.logger.debug(
                    f"Client embeddings OpenAI initialisé avec modèle {embed_config.embed_modele}"
                )

    @handle_errors(
        category=ErrorCategory.EMBEDDINGS,
        severity=ErrorSeverity.HIGH,
        user_message="Erreur lors du calcul des embeddings.",
        reraise=False,
        default_return=(None, 0.0),
    )
    def _get_embeddings(
        self, texts: List[str], counter: Optional[Tuple[int, int]] = None
    ) -> Tuple[np.ndarray, float]:
        """Obtient les embeddings pour une liste de textes."""
        counter_str = (
            f"Lieu {counter[0]}/{counter[1]} | " if counter else ""
        )  # Crée le préfixe pour le log

        if self.local_embed_model:
            try:
                model_name = self.config.markdown_filtering.embed_modele
                embeddings = list(self.local_embed_model.embed(texts))
                self.logger.info(
                    f"{counter_str}{len(texts)} embeddings calculés avec le modèle local: {model_name}."
                )
                return np.array(embeddings), 0.0
            except Exception as e:
                self.logger.error(f"Erreur calcul embeddings locaux: {e}")
                raise
        elif self.embed_client:
            try:
                response: LLMResponse = self.embed_client.call_embeddings(texts)
                if isinstance(response.content, list):
                    embeddings = np.array(response.content)
                    self.total_co2_emissions += response.co2_emissions
                    self.logger.info(
                        f"{counter_str}{len(texts)} embeddings calculés avec le modèle {self.embed_client.model}."
                    )
                    return embeddings, response.co2_emissions
                else:
                    self.logger.error("Format de réponse embeddings inattendu")
                    raise ValueError("Format de réponse embeddings inattendu")
            except Exception as e:
                self.logger.error(f"Erreur lors du calcul des embeddings: {e}")
                raise
        else:
            raise ValueError(
                "Aucun client d'embedding (local ou API) n'est initialisé."
            )

    def _calculate_reference_embeddings(self):
        """Calcule les embeddings pour les phrases de référence."""
        if not self.reference_phrases:
            raise ValueError("Aucune phrase de référence configurée")

        embeddings, _ = self._get_embeddings(self.reference_phrases)
        self.reference_embeddings = embeddings
        return embeddings

    def _get_pending_markdown_filtering(
        self, db_manager, execution_id: int
    ) -> List[Tuple]:
        """Récupère les enregistrements nécessitant un filtrage de markdown."""
        session = db_manager.Session()
        try:
            return (
                session.query(ResultatsExtraction, Lieux)
                .join(Lieux, ResultatsExtraction.lieu_id == Lieux.identifiant)
                .filter(
                    ResultatsExtraction.id_execution == execution_id,
                    ResultatsExtraction.statut_url == "ok",
                    ResultatsExtraction.markdown_nettoye != "",
                    ResultatsExtraction.markdown_filtre == "",
                )
                .all()
            )
        finally:
            session.close()

    def _extract_result_id(self, result: ResultatsExtraction) -> Optional[int]:
        """
        Extrait l'ID d'un résultat SQLAlchemy de manière sécurisée.

        Args:
            result: Objet ResultatsExtraction

        Returns:
            ID en tant qu'entier ou None si non trouvé
        """
        if hasattr(result, "id_resultats_extraction"):
            result_id = result.id_resultats_extraction
            if isinstance(result_id, int):
                return result_id
            self.logger.warning(f"L'ID du résultat n'est pas un entier: {result_id}")
        return None

    def process_markdown_filtering(
        self, db_processor: DatabaseProcessor, execution_id: int
    ):
        """
        Filtre le markdown nettoyé par embeddings sémantiques.

        Args:
            db_processor (DatabaseProcessor): Processeur de base de données
            execution_id (int): ID de l'exécution
        """
        # Récupérer les résultats avec markdown nettoyé
        if self.reference_embeddings is None:
            self._calculate_reference_embeddings()
        pending_results = db_processor.get_results_with_cleaned_markdown(execution_id)
        total_results = len(pending_results)

        for i, result in enumerate(pending_results):
            try:
                # Filtrer le markdown
                markdown_content = getattr(result, "markdown_nettoye", "") or ""
                counter = (i + 1, total_results)
                filtered_markdown, co2_emissions = self.filter_markdown(
                    markdown_content, counter
                )

                # Extraire l'ID de manière sécurisée
                resultat_id = self._extract_result_id(result)

                if resultat_id is not None:
                    # Mettre à jour en base
                    db_processor.update_filtered_markdown(
                        resultat_id, filtered_markdown, co2_emissions
                    )
                else:
                    self.logger.warning(
                        "ID de résultat non trouvé pour le filtrage markdown"
                    )

            except Exception as e:
                self.logger.error(f"Erreur lors du filtrage markdown: {e}")
                continue

    def filter_markdown(
        self, markdown_content: str, counter: Optional[Tuple[int, int]] = None
    ) -> Tuple[str, float]:
        """
        Filtre le contenu markdown en gardant seulement les parties pertinentes pour les horaires.

        Args:
            markdown_content (str): Contenu markdown à filtrer
            counter (Optional[Tuple[int, int]]): Compteur pour le suivi des logs.

        Returns:
            Tuple[str, float]: (contenu filtré, émissions CO2 du processus)
        """
        return self._filter_single_markdown(markdown_content, counter)

    def _filter_single_markdown(
        self, markdown_content: str, counter: Optional[Tuple[int, int]] = None
    ) -> Tuple[str, float]:
        """Filtre un contenu markdown et retourne le contenu filtré et les émissions CO2."""
        md_config = self.config.markdown_filtering
        co2_for_this_document = 0.0

        if (
            not markdown_content
            or md_config.min_content_length is None
            or len(markdown_content.strip()) < md_config.min_content_length
        ):
            return markdown_content, co2_for_this_document

        try:
            text = markdown_content.strip()
            chunks = self._split_into_chunks(
                text, md_config.chunk_size or 0, md_config.chunk_overlap or 0
            )
            if not chunks:
                return markdown_content, co2_for_this_document

            embed_chunks, co2_chunks = self._get_embeddings(chunks, counter=counter)
            co2_for_this_document += co2_chunks

            if embed_chunks is None or self.reference_embeddings is None:
                return markdown_content, co2_for_this_document

            # Calcul de similarité par produit scalaire
            similarites = self.reference_embeddings @ embed_chunks.T
            similarites_max = similarites.max(axis=0)

            context_window = md_config.context_window_size

            relevant_indices = set()
            for i, score in enumerate(similarites_max):
                if score >= md_config.similarity_threshold:
                    start_idx = max(0, i - context_window)
                    end_idx = min(len(chunks), i + context_window + 1)
                    relevant_indices.update(range(start_idx, end_idx))

            if not relevant_indices:
                return "", co2_for_this_document

            relevant_phrases = [chunks[i] for i in sorted(list(relevant_indices))]
            filtered_content = "\n\n".join(relevant_phrases)

            return filtered_content, co2_for_this_document
        except Exception as e:
            self.logger.error(f"Erreur lors du filtrage: {e}")
            return markdown_content, co2_for_this_document

    def _split_into_chunks(
        self, text: str, chunk_size: int, chunk_overlap: int
    ) -> List[str]:
        """Découpe le texte en segments."""
        md_config = self.config.markdown_filtering
        if md_config.sentencizer == "NLTK":
            self.logger.debug("Découpage du texte avec NLTK sentencizer.")
            return nltk.sent_tokenize(text, language="french")

        self.logger.debug(
            f"Découpage du texte avec chunk_size={chunk_size} et chunk_overlap={chunk_overlap}."
        )
        if chunk_size <= 0:
            self.logger.warning("chunk_size doit être positif. Retour du texte entier.")
            return [text] if text.strip() else []

        words = text.split()
        if not words:
            return []

        chunks = []
        current_pos = 0
        while current_pos < len(words):
            end_pos = current_pos + chunk_size
            chunk_words = words[current_pos:end_pos]
            chunks.append(" ".join(chunk_words))

            # Si le chevauchement est plus grand ou égal à la taille du chunk,
            # on avance d'un seul mot pour éviter une boucle infinie.
            step = chunk_size - chunk_overlap
            if step <= 0:
                self.logger.warning(
                    f"chunk_overlap ({chunk_overlap}) >= chunk_size ({chunk_size}). Avancement d'un mot pour éviter une boucle infinie."
                )
                step = 1

            current_pos += step

        return chunks
