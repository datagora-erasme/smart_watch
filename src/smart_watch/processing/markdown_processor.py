# Documentation:
# https://datagora-erasme.github.io/smart_watch/source/modules/processing/markdown_processor.html

import os
import re
from typing import Any, Dict, List, Optional, Tuple

import nltk
import numpy as np
from fastembed import TextEmbedding

from ..config.markdown_filtering_config import MarkdownFilteringConfig
from ..core.ConfigManager import ConfigManager
from ..core.ErrorHandler import ErrorCategory, ErrorSeverity, handle_errors
from ..core.LLMClient import LLMResponse, MistralAPIClient, OpenAICompatibleClient
from ..core.Logger import SmartWatchLogger, create_logger
from ..processing.database_processor import DatabaseProcessor

logger: SmartWatchLogger = create_logger(module_name="MarkdownProcessor")


class MarkdownProcessor:
    """
    Classe pour traiter et filtrer le contenu Markdown en se basant sur la pertinence sémantique.

    Cette classe utilise des embeddings pour identifier et extraire les sections d'un document
    Markdown qui sont les plus pertinentes par rapport à un ensemble de phrases de référence.
    """

    def __init__(
        self, config_manager: ConfigManager, logger_instance: SmartWatchLogger
    ):
        """
        Initialise le processeur de markdown.

        Args:
            config_manager (ConfigManager) : le gestionnaire de configuration de l'application.
            logger_instance (SmartWatchLogger) : l'instance de logger à utiliser.
        """
        self.config: MarkdownFilteringConfig = config_manager.markdown_filtering
        self.reference_embeddings: Optional[np.ndarray] = None
        self.local_embed_model: Optional[TextEmbedding] = None
        self.embed_client: Optional[MistralAPIClient | OpenAICompatibleClient] = None
        self.logger: SmartWatchLogger = logger_instance

        try:
            self._init_embedding_client()
            self.logger.info(
                f"Client embeddings initialisé avec le fournisseur: {self.config.embed_fournisseur}"
            )
        except Exception as e:
            self.logger.error(
                f"Erreur lors de l'initialisation du client embeddings: {e}"
            )
            self.embed_client = None

        if self.config.sentencizer == "NLTK":
            self._init_nltk()

    def _init_nltk(self) -> None:
        """
        Initialise le tokenizer NLTK ('punkt') s'il n'est pas déjà disponible.
        """
        try:
            nltk.data.find("tokenizers/punkt")
            self.logger.info("Le tokenizer 'punkt' de NLTK est déjà téléchargé.")
        except LookupError:
            self.logger.info("Téléchargement du tokenizer 'punkt' de NLTK...")
            nltk.download("punkt")
            self.logger.info("Tokenizer 'punkt' de NLTK téléchargé avec succès.")

    def _init_embedding_client(self) -> None:
        """
        Initialise le client pour la génération d'embeddings (local, Mistral, ou OpenAI).

        Raises:
            ValueError : si la configuration pour le fournisseur d'embedding est incomplète.
        """
        embed_config = self.config

        if embed_config.embed_fournisseur == "LOCAL":
            if embed_config.embed_modele:
                try:
                    cpu_count = os.cpu_count() or 1
                    threads = max(1, cpu_count // 4)
                    self.local_embed_model = TextEmbedding(
                        model_name=embed_config.embed_modele, threads=threads
                    )
                    self.logger.info(
                        f"Modèle d'embedding local chargé: {embed_config.embed_modele} avec {threads} threads."
                    )
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

    @handle_errors(
        category=ErrorCategory.EMBEDDINGS,
        severity=ErrorSeverity.HIGH,
        default_return=(None, 0.0),
    )
    def _get_embeddings(self, texts: List[str]) -> Tuple[Optional[np.ndarray], float]:
        """
        Génère les embeddings pour une liste de textes.

        Args:
            texts (List[str]) : la liste des textes à encoder.

        Returns:
            Tuple[Optional[np.ndarray], float] : un tuple contenant les embeddings sous forme de tableau NumPy
                                                 et les émissions de CO2 estimées.

        Raises:
            ValueError : si aucun client d'embedding n'est initialisé.
        """
        if not texts:
            return None, 0.0

        valid_texts = [text for text in texts if text and not text.isspace()]
        if not valid_texts:
            return None, 0.0

        if self.local_embed_model:
            try:
                embeddings = list(self.local_embed_model.embed(valid_texts))
                return np.array(embeddings), 0.0
            except Exception as e:
                self.logger.error(f"Erreur calcul embeddings locaux: {e}")
                raise
        elif self.embed_client:
            try:
                response: LLMResponse = self.embed_client.call_embeddings(valid_texts)
                if isinstance(response.content, list):
                    return np.array(response.content), response.co2_emissions
                else:
                    raise ValueError("Format de réponse embeddings inattendu")
            except Exception as e:
                self.logger.error(f"Erreur lors du calcul des embeddings: {e}")
                raise
        else:
            raise ValueError("Aucun client d'embedding n'est initialisé.")

    def _calculate_reference_embeddings(self) -> None:
        """
        Calcule et met en cache les embeddings pour les phrases de référence définies dans la configuration.

        Raises:
            ValueError : si aucune phrase de référence n'est configurée.
        """
        if self.reference_embeddings is None:
            if not self.config.reference_phrases:
                raise ValueError("Aucune phrase de référence configurée")
            self.logger.debug("Calcul des embeddings pour les phrases de référence.")
            embeddings, _ = self._get_embeddings(self.config.reference_phrases)
            self.reference_embeddings = embeddings

    def process_markdown_filtering(
        self, db_processor: DatabaseProcessor, execution_id: int
    ) -> None:
        """
        Filtre le contenu markdown pour tous les résultats d'une exécution donnée.

        Args:
            db_processor (DatabaseProcessor) : l'instance du processeur de base de données.
            execution_id (int) : l'ID de l'exécution à traiter.
        """
        self._calculate_reference_embeddings()
        pending_results = db_processor.get_results_with_cleaned_markdown(execution_id)
        total_results = len(pending_results)

        for i, result in enumerate(pending_results):
            try:
                markdown_content = getattr(result, "markdown_nettoye", "") or ""
                counter = (i + 1, total_results)
                filtered_markdown, co2_emissions = self.filter_markdown(
                    markdown_content, counter
                )
                resultat_id = getattr(result, "id_resultats_extraction", None)

                if resultat_id is not None:
                    db_processor.update_filtered_markdown(
                        resultat_id, filtered_markdown, co2_emissions
                    )
                else:
                    self.logger.warning(
                        "ID de résultat non trouvé pour le filtrage markdown"
                    )
            except Exception as e:
                self.logger.error(
                    f"Erreur lors du filtrage markdown pour résultat {getattr(result, 'id_resultats_extraction', 'inconnu')}: {e}"
                )
                continue

    @handle_errors(
        category=ErrorCategory.PARSING,
        severity=ErrorSeverity.HIGH,
        default_return=("", 0.0),
    )
    def filter_markdown(
        self, markdown_content: str, counter: Optional[Tuple[int, int]] = None
    ) -> Tuple[str, float]:
        """
        Filtre un contenu Markdown pour n'en conserver que les sections sémantiquement pertinentes.

        Args:
            markdown_content (str) : le contenu Markdown à filtrer.
            counter (Optional[Tuple[int, int]]) : un compteur (ex: (1, 10)) pour le logging.

        Returns:
            Tuple[str, float] : le contenu Markdown filtré et les émissions de CO2 associées.
        """
        prefix = f"*{counter[0]}/{counter[1]}* " if counter else ""
        min_len = self.config.min_content_length or 0
        if len(markdown_content) < min_len:
            logger.debug(f"{prefix}Contenu trop court, filtrage ignoré.")
            return markdown_content, 0.0

        all_lines = markdown_content.split("\n")
        logical_blocks = self._identify_logical_blocks(all_lines)
        if not logical_blocks:
            return "", 0.0

        chunks = self._chunk_blocks(logical_blocks)
        relevant_chunks, co2_emissions = self._filter_chunks(chunks)
        if not relevant_chunks:
            logger.warning(f"{prefix}Aucune section pertinente trouvée après filtrage.")
            return "", co2_emissions

        relevant_line_ranges = [
            (block["start_line"], block["end_line"])
            for chunk in relevant_chunks
            for block in chunk["blocks"]
        ]

        merged_ranges = self._merge_ranges(relevant_line_ranges)

        expansion_lines = self.config.context_window_size
        expanded_ranges = [
            (
                max(0, start - expansion_lines),
                min(len(all_lines) - 1, end + expansion_lines),
            )
            for start, end in merged_ranges
        ]

        final_ranges = self._merge_ranges(expanded_ranges)

        final_sections = [
            "\n".join(all_lines[start : end + 1]) for start, end in final_ranges
        ]
        final_content = "\n\n".join(final_sections)

        logger.info(
            f"{prefix}Filtrage terminé. Contenu réduit de {len(markdown_content)} à {len(final_content)} car."
        )
        return final_content, co2_emissions

    def _classify_line(self, line: str) -> str:
        """
        Classifie une ligne de texte en catégories structurelles (paragraphe, tabulaire, etc.).

        Args:
            line (str) : la ligne à classifier.

        Returns:
            str : le type de la ligne ('empty', 'tabular', 'indented', 'paragraph').
        """
        if not line.strip():
            return "empty"
        if len(re.findall(r"\s{2,}", line)) >= 2:
            return "tabular"
        if line.startswith((" ", "\t")):
            return "indented"
        return "paragraph"

    def _identify_logical_blocks(self, lines: List[str]) -> List[Dict[str, Any]]:
        """
        Segmente une liste de lignes en blocs logiques (paragraphes, tableaux, etc.).

        Args:
            lines (List[str]) : les lignes de texte à analyser.

        Returns:
            List[Dict[str, Any]] : une liste de dictionnaires, chaque dictionnaire représentant un bloc.
        """
        blocks = []
        if not lines:
            return blocks

        current_block_lines, start_line_num = [], 0
        current_block_type = self._classify_line(lines[0])

        for i, line in enumerate(lines):
            line_type = self._classify_line(line)
            is_new_block = (
                line_type != current_block_type and line_type != "empty"
            ) or (line_type == "empty" and current_block_type != "empty")

            if is_new_block and current_block_lines:
                blocks.append(
                    {
                        "type": current_block_type,
                        "lines": current_block_lines,
                        "start_line": start_line_num,
                        "end_line": i - 1,
                    }
                )
                current_block_lines = []

            if line_type != "empty":
                if not current_block_lines:
                    start_line_num, current_block_type = i, line_type
                current_block_lines.append(line)

        if current_block_lines:
            blocks.append(
                {
                    "type": current_block_type,
                    "lines": current_block_lines,
                    "start_line": start_line_num,
                    "end_line": len(lines) - 1,
                }
            )
        return blocks

    def _chunk_blocks(self, blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Regroupe les blocs logiques en 'chunks' de taille définie pour l'analyse sémantique.

        Args:
            blocks (List[Dict[str, Any]]) : la liste des blocs logiques à regrouper.

        Returns:
            List[Dict[str, Any]] : une liste de chunks, chaque chunk contenant un ou plusieurs blocs.
        """
        chunks, current_chunk_blocks, current_size = [], [], 0
        chunk_size = self.config.chunk_size or 100
        chunk_overlap = self.config.chunk_overlap or 15

        for block in blocks:
            block_content = "\n".join(block["lines"])
            block_size = len(block_content)
            if current_size + block_size > chunk_size and current_chunk_blocks:
                chunks.append(
                    {
                        "content": "\n".join(
                            b["content"] for b in current_chunk_blocks
                        ),
                        "blocks": current_chunk_blocks,
                    }
                )
                overlap_count = int(chunk_overlap / 100 * len(current_chunk_blocks))
                current_chunk_blocks = (
                    current_chunk_blocks[-overlap_count:] if overlap_count > 0 else []
                )
                current_size = sum(
                    len("\n".join(b["lines"])) for b in current_chunk_blocks
                )
            block["content"] = block_content
            current_chunk_blocks.append(block)
            current_size += block_size
        if current_chunk_blocks:
            chunks.append(
                {
                    "content": "\n".join(b["content"] for b in current_chunk_blocks),
                    "blocks": current_chunk_blocks,
                }
            )
        return chunks

    def _filter_chunks(
        self, chunks: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], float]:
        """
        Filtre les chunks en fonction de leur similarité sémantique avec les phrases de référence.

        Args:
            chunks (List[Dict[str, Any]]) : la liste des chunks à filtrer.

        Returns:
            Tuple[List[Dict[str, Any]], float] : une liste des chunks pertinents et les émissions de CO2.
        """
        relevant_chunks, total_co2 = [], 0.0
        chunk_contents = [chunk["content"] for chunk in chunks]

        if not chunk_contents:
            return [], 0.0

        chunk_embeddings, co2 = self._get_embeddings(chunk_contents)
        total_co2 += co2

        if chunk_embeddings is None or self.reference_embeddings is None:
            return [], total_co2

        for i, chunk_embedding in enumerate(chunk_embeddings):
            max_similarity = max(
                self._cosine_similarity(chunk_embedding, ref_embedding)
                for ref_embedding in self.reference_embeddings
            )
            similarity_threshold = self.config.similarity_threshold or 0.0
            if max_similarity >= similarity_threshold:
                relevant_chunks.append(chunks[i])
        return relevant_chunks, total_co2

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calcule la similarité cosinus entre deux vecteurs NumPy.

        Args:
            vec1 (np.ndarray) : le premier vecteur.
            vec2 (np.ndarray) : le second vecteur.

        Returns:
            float : la similarité cosinus (entre -1 et 1).
        """
        dot_product = np.dot(vec1, vec2)
        norm_vec1 = np.linalg.norm(vec1)
        norm_vec2 = np.linalg.norm(vec2)
        if norm_vec1 == 0 or norm_vec2 == 0:
            return 0.0
        return dot_product / (norm_vec1 * norm_vec2)

    def _merge_ranges(
        self, ranges: List[Tuple[int, int]], gap: int = 1
    ) -> List[Tuple[int, int]]:
        """
        Fusionne des plages de nombres (intervalles) qui se chevauchent ou sont proches.

        Args:
            ranges (List[Tuple[int, int]]) : une liste de tuples représentant les plages (début, fin).
            gap (int) : l'écart maximal entre deux plages pour qu'elles soient fusionnées.

        Returns:
            List[Tuple[int, int]] : une liste de plages fusionnées.
        """
        if not ranges:
            return []
        sorted_ranges = sorted(ranges, key=lambda x: x[0])
        merged = [sorted_ranges[0]]
        for current_start, current_end in sorted_ranges[1:]:
            last_start, last_end = merged[-1]
            if current_start <= last_end + gap:
                merged[-1] = (last_start, max(last_end, current_end))
            else:
                merged.append((current_start, current_end))
        return merged
