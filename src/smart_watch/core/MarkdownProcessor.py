"""
Processeur pour filtrer le contenu markdown et extraire les sections pertinentes aux horaires.
Utilise des embeddings sémantiques pour identifier les sections les plus pertinentes.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
from langchain_text_splitters import MarkdownHeaderTextSplitter
from sentence_transformers import SentenceTransformer, util

from ..data_models.schema_bdd import Lieux, ResultatsExtraction
from .ConfigManager import ConfigManager


@dataclass
class ProcessingStats:
    """Statistiques de traitement pour chaque étape."""

    urls_processed: int = 0
    urls_successful: int = 0
    llm_processed: int = 0
    llm_successful: int = 0
    comparisons_processed: int = 0
    comparisons_successful: int = 0

    def get_summary(self) -> Dict[str, int]:
        return {
            "urls_processed": self.urls_processed,
            "urls_successful": self.urls_successful,
            "llm_processed": self.llm_processed,
            "llm_successful": self.llm_successful,
            "comparisons_processed": self.comparisons_processed,
            "comparisons_successful": self.comparisons_successful,
        }


class MarkdownProcessor:
    """Processeur pour filtrer le contenu markdown et extraire les sections pertinentes aux horaires."""

    def __init__(self, config: ConfigManager, logger):
        self.config = config
        self.logger = logger

        # Initialisation du modèle d'embeddings
        try:
            self.model = SentenceTransformer(
                self.config.markdown_filtering.embedding_model
            )
            self.logger.info("Modèle d'embeddings chargé avec succès")
        except Exception as e:
            self.logger.error(f"Erreur chargement modèle embeddings: {e}")
            self.model = None

        # Headers pour le splitting markdown (depuis la config)
        self.headers_to_split_on = self.config.markdown_filtering.headers_to_split

        # Phrases de référence pour identifier les sections d'horaires (depuis la config)
        self.reference_phrases = self.config.markdown_filtering.reference_phrases

    def process_markdown_filtering(
        self, db_manager, execution_id: int
    ) -> "ProcessingStats":
        """Filtre le contenu markdown pour extraire les sections pertinentes aux horaires."""
        self.logger.section("FILTRAGE MARKDOWN POUR HORAIRES")

        stats = ProcessingStats()

        if not self.model:
            self.logger.warning("Modèle d'embeddings non disponible - filtrage ignoré")
            return stats

        # Récupérer les enregistrements avec markdown à filtrer
        resultats_a_filtrer = self._get_pending_markdown_filtering(
            db_manager, execution_id
        )

        if not resultats_a_filtrer:
            self.logger.info("Aucun markdown à filtrer")
            return stats

        self.logger.info(f"{len(resultats_a_filtrer)} contenus markdown à filtrer")
        stats.urls_processed = len(resultats_a_filtrer)

        # Calcul du vecteur de référence pour les horaires
        reference_embeddings = self.model.encode(self.reference_phrases)
        reference_vector = np.mean(reference_embeddings, axis=0)

        for i, (resultat, lieu) in enumerate(resultats_a_filtrer, 1):
            self.logger.info(f"Filtrage {i}/{len(resultats_a_filtrer)}: {lieu.nom}")

            try:
                filtered_markdown = self._filter_single_markdown(
                    resultat.markdown, reference_vector
                )

                # Mise à jour en base
                self._update_filtered_markdown(
                    db_manager, resultat.id_resultats_extraction, filtered_markdown
                )

                if filtered_markdown and len(filtered_markdown.strip()) > 0:
                    stats.urls_successful += 1
                    self.logger.debug(
                        f"Markdown filtré: {len(filtered_markdown)} caractères"
                    )
                else:
                    self.logger.warning(
                        f"Aucun contenu pertinent trouvé pour {lieu.nom}"
                    )

            except Exception as e:
                self.logger.error(f"Erreur filtrage markdown {lieu.nom}: {e}")
                # Stocker le markdown original en cas d'erreur
                self._update_filtered_markdown(
                    db_manager, resultat.id_resultats_extraction, resultat.markdown
                )

        self.logger.info(
            f"Markdown filtré: {stats.urls_successful}/{stats.urls_processed} réussies"
        )
        return stats

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
                    ResultatsExtraction.markdown != "",
                    (ResultatsExtraction.markdown_horaires == "")
                    | (ResultatsExtraction.markdown_horaires.is_(None)),
                )
                .all()
            )
        finally:
            session.close()

    def _filter_single_markdown(self, markdown_content: str, reference_vector) -> str:
        """Filtre un contenu markdown pour extraire les sections pertinentes aux horaires."""
        if (
            not markdown_content
            or len(markdown_content.strip())
            < self.config.markdown_filtering.min_content_length
        ):
            return markdown_content

        try:
            # Découpage du markdown par sections
            markdown_splitter = MarkdownHeaderTextSplitter(self.headers_to_split_on)
            md_header_splits = markdown_splitter.split_text(markdown_content)

            if not md_header_splits:
                return markdown_content

            # Calcul des scores de similarité pour chaque section
            document_sections_with_scores = []

            for doc in md_header_splits:
                # Ignorer les sections trop courtes (utilise la config)
                if (
                    len(doc.page_content.strip())
                    < self.config.markdown_filtering.min_section_length
                ):
                    continue

                # Calcul de l'embedding pour la section
                section_embedding = self.model.encode(doc.page_content)

                # Calcul de la similarité cosinus
                similarity_score = util.cos_sim(
                    reference_vector, section_embedding
                ).item()

                document_sections_with_scores.append(
                    {
                        "score": similarity_score,
                        "metadata": doc.metadata,
                        "content": doc.page_content,
                    }
                )

            # Tri par score de similarité décroissant
            sorted_sections = sorted(
                document_sections_with_scores, key=lambda x: x["score"], reverse=True
            )

            # Sélection des meilleures sections (utilise la config)
            top_sections = sorted_sections[
                : self.config.markdown_filtering.max_sections
            ]

            # Concaténation des sections sélectionnées
            filtered_content = "\n".join(
                [
                    f"\n## Section Horaires: {section['metadata']}\n{section['content']}"
                    for section in top_sections
                ]
            )

            return filtered_content if filtered_content.strip() else markdown_content

        except Exception as e:
            self.logger.error(f"Erreur lors du filtrage: {e}")
            return markdown_content

    def _update_filtered_markdown(
        self, db_manager, resultat_id: int, filtered_markdown: str
    ):
        """Met à jour le markdown filtré en base de données."""
        session = db_manager.Session()
        try:
            resultat = session.get(ResultatsExtraction, resultat_id)
            if resultat:
                resultat.markdown_horaires = filtered_markdown
                session.commit()
        finally:
            session.close()
