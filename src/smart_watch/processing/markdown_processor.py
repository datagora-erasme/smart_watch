"""
Processeur pour filtrer le contenu markdown et extraire les sections pertinentes aux horaires.
Utilise des embeddings sémantiques pour identifier les sections les plus pertinentes.
"""

from typing import List, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from ..core.ConfigManager import ConfigManager
from ..core.ErrorHandler import ErrorCategory, ErrorSeverity, handle_errors
from ..core.LLMClient import LLMResponse, MistralAPIClient, OpenAICompatibleClient
from ..data_models.schema_bdd import Lieux, ResultatsExtraction


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

    def _init_embedding_client(self):
        """Initialise le client approprié pour les embeddings selon la configuration."""
        embed_config = self.config.markdown_filtering

        if embed_config.embed_fournisseur == "LOCAL":
            if embed_config.embed_modele:
                try:
                    self.local_embed_model = SentenceTransformer(
                        embed_config.embed_modele
                    )
                    self.logger.info(
                        f"Modèle d'embedding local chargé: {embed_config.embed_modele}"
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
    def _get_embeddings(self, texts: List[str]) -> Tuple[np.ndarray, float]:
        """Obtient les embeddings pour une liste de textes."""
        if self.local_embed_model:
            try:
                embeddings = self.local_embed_model.encode(
                    texts, show_progress_bar=False
                )
                self.logger.info(
                    f"{len(texts)} embeddings calculés avec le modèle local."
                )
                return np.array(embeddings), 0.0  # Pas d'émissions CO2 pour le local
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
                        f"{len(texts)} embeddings calculés avec le modèle {self.embed_client.model}."
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

    def process_markdown_filtering(self, db_manager, execution_id: int):
        """Filtre le contenu markdown."""
        self.logger.section("FILTRAGE MARKDOWN POUR HORAIRES")
        self.total_co2_emissions = 0.0
        self.reference_embeddings = None

        if not self.local_embed_model and not self.embed_client:
            self.logger.warning("Aucun modèle d'embedding disponible - filtrage ignoré")
            return

        resultats_a_filtrer = self._get_pending_markdown_filtering(
            db_manager, execution_id
        )
        if not resultats_a_filtrer:
            self.logger.info("Aucun markdown à filtrer")
            return

        self.logger.info(f"{len(resultats_a_filtrer)} contenus markdown à filtrer")

        try:
            self.logger.info("Pré-calcul des embeddings de référence...")
            self._calculate_reference_embeddings()
        except Exception as e:
            self.logger.error(f"Erreur calcul embeddings de référence: {e}. Arrêt.")
            return

        successful_count = 0
        for i, (resultat, lieu) in enumerate(resultats_a_filtrer, 1):
            self.logger.info(
                f"*{lieu.identifiant}* Filtrage {i}/{len(resultats_a_filtrer)} - '{lieu.nom}'"
            )
            try:
                len_avant = len(resultat.markdown_nettoye)
                filtered_markdown, co2_emissions = self._filter_single_markdown(
                    resultat.markdown_nettoye
                )
                len_apres = len(filtered_markdown)

                if len_avant > 0:
                    reduction = ((len_avant - len_apres) / len_avant) * 100
                    self.logger.info(
                        f"*{lieu.identifiant}* Taille avant/après filtrage: {len_avant} -> {len_apres} "
                        f"caractères (réduction de {reduction:.2f}%)."
                    )
                else:
                    self.logger.info(
                        f"*{lieu.identifiant}* Pas de contenu à filtrer (0 caractère)."
                    )

                db_manager.update_filtered_markdown(
                    resultat.id_resultats_extraction,
                    filtered_markdown,
                    co2_emissions,
                )

                if filtered_markdown and len(filtered_markdown.strip()) > 0:
                    successful_count += 1
                else:
                    self.logger.warning(
                        f"*{lieu.identifiant}* Aucun contenu pertinent trouvé pour '{lieu.nom}'"
                    )
            except Exception as e:
                self.logger.error(
                    f"*{lieu.identifiant}* Erreur filtrage markdown pour '{lieu.nom}': {e}"
                )
                db_manager.add_pipeline_error(
                    resultat.id_resultats_extraction,
                    "FILTRAGE",
                    f"Erreur filtrage markdown: {str(e)}",
                )
                db_manager.update_filtered_markdown(
                    resultat.id_resultats_extraction, resultat.markdown_nettoye
                )

        self.logger.info(
            f"Markdown filtré: {successful_count}/{len(resultats_a_filtrer)} réussies"
        )

        if self.total_co2_emissions > 0:
            db_manager.update_execution_embeddings(
                execution_id, self.total_co2_emissions
            )
            self.logger.info(
                f"Émissions CO2 embeddings totales: {self.total_co2_emissions:.6f} kg"
            )

    def _filter_single_markdown(self, markdown_content: str) -> Tuple[str, float]:
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
            if md_config.chunk_size is None or md_config.chunk_overlap is None:
                return markdown_content, co2_for_this_document
            chunks = self._split_into_chunks(
                text, md_config.chunk_size, md_config.chunk_overlap
            )
            if not chunks:
                return markdown_content, co2_for_this_document

            embed_chunks, co2_chunks = self._get_embeddings(chunks)
            co2_for_this_document += co2_chunks

            if embed_chunks is None or self.reference_embeddings is None:
                return markdown_content, co2_for_this_document

            similarites = cosine_similarity(self.reference_embeddings, embed_chunks)
            similarites_max = similarites.max(axis=0)

            relevant_indices = set()
            for i, score in enumerate(similarites_max):
                if score >= md_config.similarity_threshold:
                    start_idx = max(0, i - md_config.context_window_size)
                    end_idx = min(len(chunks), i + md_config.context_window_size + 1)
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
        """Découpe le texte en segments selon la ponctuation et les retours à la ligne."""
        import re

        # Divise le texte par la ponctuation de fin de phrase.
        sentences = re.split(r"(?<=[.!?])\s+", text)

        # Divise chaque "phrase" par les sauts de ligne.
        final_chunks = []
        for sentence in sentences:
            lines = sentence.split("\n")
            for line in lines:
                stripped_line = line.strip()
                if stripped_line:  # Ajoute uniquement les lignes non vides.
                    final_chunks.append(stripped_line)

        return final_chunks
