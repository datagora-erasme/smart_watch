"""
Processeur pour filtrer le contenu markdown et extraire les sections pertinentes aux horaires.
Utilise des embeddings sémantiques pour identifier les sections les plus pertinentes.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Tuple

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

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

        for i, (resultat, lieu) in enumerate(resultats_a_filtrer, 1):
            self.logger.info(f"Filtrage {i}/{len(resultats_a_filtrer)}: {lieu.nom}")

            try:
                filtered_markdown = self._filter_single_markdown(
                    resultat.markdown, lieu.nom, lieu.type_lieu
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

    def _extract_context_around_phrase(
        self, phrases: List[str], phrase_index: int, context_window: int = 1
    ) -> List[int]:
        """Extrait les indices des phrases dans la fenêtre de contexte autour d'une phrase donnée."""
        start_idx = max(0, phrase_index - context_window)
        end_idx = min(len(phrases), phrase_index + context_window + 1)
        return list(range(start_idx, end_idx))

    def _filter_single_markdown(
        self, markdown_content: str, nom: str = "", type_lieu: str = ""
    ) -> str:
        """Filtre un contenu markdown pour extraire les sections pertinentes aux horaires."""
        if (
            not markdown_content
            or len(markdown_content.strip())
            < self.config.markdown_filtering.min_content_length
        ):
            return markdown_content

        try:
            # Créer des thèmes dynamiques incluant le nom et type d'établissement
            themes = self.reference_phrases.copy()
            if nom:
                if type_lieu:
                    themes.extend([f"horaires d'ouverture {nom} ({type_lieu})"])
                else:
                    themes.extend([f"horaires d'ouverture {nom}"])
            else:
                if type_lieu:
                    themes.extend([f"horaires d'ouverture {type_lieu}"])

            # Pré-calculer les embeddings des thèmes
            embed_themes = self.model.encode(themes)

            # Segmenter le texte en phrases
            split_chars = ["."]
            regex = "|".join(map(re.escape, split_chars))
            phrases = [
                p.strip() for p in re.split(regex, markdown_content) if p.strip()
            ]

            if not phrases:
                return markdown_content

            # Générer les embeddings des phrases
            embed_phrases = self.model.encode(phrases)

            # Calculer les similarités
            similarites = cosine_similarity(embed_themes, embed_phrases)
            similarites_max = similarites.max(axis=0)

            # Normaliser pour obtenir des scores [0, 1]
            min_val = similarites_max.min()
            max_val = similarites_max.max()
            if max_val - min_val > 0:
                similarites_norm = (similarites_max - min_val) / (max_val - min_val)
            else:
                similarites_norm = similarites_max * 0  # all zeros

            # Filtrer les phrases ayant un score élevé
            threshold = getattr(
                self.config.markdown_filtering, "similarity_threshold", 0.25
            )

            # Obtenir le contexte autour des phrases pertinentes
            context_window = getattr(
                self.config.markdown_filtering, "context_window", 1
            )

            relevant_indices = set()

            for i, score in enumerate(similarites_norm):
                if score >= threshold:
                    # Ajouter le contexte autour de cette phrase
                    context_indices = self._extract_context_around_phrase(
                        phrases, i, context_window
                    )
                    relevant_indices.update(context_indices)

            # Convertir en liste triée pour maintenir l'ordre
            relevant_indices = sorted(list(relevant_indices))

            # Extraire les phrases avec leur contexte
            relevant_phrases = [phrases[i] for i in relevant_indices]

            # Retourner les phrases pertinentes avec contexte concaténées
            if relevant_phrases:
                filtered_content = ". ".join(relevant_phrases)
                return (
                    filtered_content if filtered_content.strip() else markdown_content
                )
            else:
                return markdown_content

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
            resultat = session.get(ResultatsExtraction, resultat_id)
            if resultat:
                resultat.markdown_horaires = filtered_markdown
                session.commit()
