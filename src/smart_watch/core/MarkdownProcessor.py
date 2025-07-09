"""
Processeur pour filtrer le contenu markdown et extraire les sections pertinentes aux horaires.
Utilise des embeddings sémantiques pour identifier les sections les plus pertinentes.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from ..data_models.schema_bdd import Lieux, ResultatsExtraction
from .ConfigManager import ConfigManager
from .LLMClient import OpenAICompatibleClient


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
        self.total_co2_emissions = (
            0.0  # Accumulation des émissions pour cette exécution
        )
        self.reference_embeddings = None  # Pour stocker les embeddings de référence

        # Initialisation du client LLM pour les embeddings
        try:
            self.llm_client = OpenAICompatibleClient(
                api_key=config.llm.api_key,
                model=config.markdown_filtering.embedding_model,
                base_url=config.llm.base_url,
                timeout=30,
            )
            self.logger.info(
                f"Client embeddings initialisé avec {self.config.markdown_filtering.embedding_model}"
            )
        except Exception as e:
            self.logger.error(f"Erreur initialisation client embeddings: {e}")
            self.llm_client = None

        # Phrases de référence pour identifier les sections d'horaires (depuis la config)
        self.reference_phrases = self.config.markdown_filtering.reference_phrases

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
                    ResultatsExtraction.markdown_filtre == "",  # Pas encore filtré
                )
                .all()
            )
        finally:
            session.close()

    def process_markdown_filtering(
        self, db_manager, execution_id: int
    ) -> "ProcessingStats":
        """Filtre le contenu markdown pour extraire les sections pertinentes aux horaires."""
        self.logger.section("FILTRAGE MARKDOWN POUR HORAIRES")

        # Reset des émissions pour cette exécution
        self.total_co2_emissions = 0.0
        self.reference_embeddings = None  # Réinitialiser pour chaque exécution

        stats = ProcessingStats()

        if not self.llm_client:
            self.logger.warning("Client embeddings non disponible - filtrage ignoré")
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

        # Pré-calculer les embeddings de référence une seule fois
        try:
            self.logger.info("Pré-calcul des embeddings de référence...")
            embed_themes, _ = self._get_embeddings_via_api(self.reference_phrases)
            self.reference_embeddings = np.array(embed_themes)
            # La consommation est déjà ajoutée dans _get_embeddings_via_api
            self.logger.info(
                f"{len(self.reference_phrases)} embeddings de référence calculés."
            )
        except Exception as e:
            self.logger.error(f"Erreur calcul embeddings de référence: {e}. Arrêt.")
            return stats

        for i, (resultat, lieu) in enumerate(resultats_a_filtrer, 1):
            self.logger.info(f"Filtrage {i}/{len(resultats_a_filtrer)}: {lieu.nom}")

            try:
                filtered_markdown, co2_emissions = self._filter_single_markdown(
                    resultat.markdown_nettoye
                )

                # Mise à jour en base
                db_manager.update_filtered_markdown(
                    resultat.id_resultats_extraction,
                    filtered_markdown,
                    co2_emissions,
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
                # Ajouter l'erreur à la chaîne
                db_manager.add_pipeline_error(
                    resultat.id_resultats_extraction,
                    "FILTRAGE",
                    f"Erreur filtrage markdown: {str(e)}",
                )
                # Stocker le markdown nettoyé en cas d'erreur
                db_manager.update_filtered_markdown(
                    resultat.id_resultats_extraction, resultat.markdown_nettoye
                )

        self.logger.info(
            f"Markdown filtré: {stats.urls_successful}/{stats.urls_processed} réussies"
        )

        # Mettre à jour les émissions totales d'embeddings dans la base
        if self.total_co2_emissions > 0:
            db_manager.update_execution_embeddings(
                execution_id, self.total_co2_emissions
            )
            self.logger.info(
                f"Émissions CO2 embeddings totales: {self.total_co2_emissions:.6f} kg"
            )

        return stats

    def _extract_context_around_phrase(
        self, phrases: List[str], phrase_index: int, context_window: int = 1
    ) -> List[int]:
        """Extrait les indices des phrases dans la fenêtre de contexte autour d'une phrase donnée."""
        start_idx = max(0, phrase_index - context_window)
        end_idx = min(len(phrases), phrase_index + context_window + 1)
        return list(range(start_idx, end_idx))

    def _get_embeddings_via_api(
        self, texts: List[str]
    ) -> Tuple[List[List[float]], float]:
        """
        Obtient les embeddings via l'API avec mesure d'émissions.

        Args:
            texts: Liste des textes à encoder

        Returns:
            Tuple(Liste des vecteurs d'embeddings, émissions de CO2)
        """
        if not texts:
            return [], 0.0

        try:
            llm_response = self.llm_client.call_embeddings(texts)

            # Logger les émissions individuelles AVANT accumulation
            individual_emissions = llm_response.co2_emissions
            self.logger.debug(
                f"Embeddings: {len(llm_response.content)} vecteurs, {individual_emissions:.6f} kg CO2 cet appel"
            )

            # Puis accumuler pour le total de l'exécution
            self.total_co2_emissions += individual_emissions

            return llm_response.content, individual_emissions

        except Exception as e:
            self.logger.error(f"Erreur calcul embeddings: {e}")
            raise

    def _filter_single_markdown(self, markdown_content: str) -> Tuple[str, float]:
        """Filtre un contenu markdown et retourne le contenu filtré et les émissions CO2."""
        co2_for_this_document = 0.0
        if (
            not markdown_content
            or len(markdown_content.strip())
            < self.config.markdown_filtering.min_content_length
        ):
            return markdown_content, co2_for_this_document

        try:
            # Segmenter le texte en phrases
            phrases = [
                p.strip() for p in re.split(r"[.\n]", markdown_content) if p.strip()
            ]
            if not phrases:
                return markdown_content, co2_for_this_document

            # Générer les embeddings des phrases du document
            embed_phrases, co2_phrases = self._get_embeddings_via_api(phrases)
            co2_for_this_document += co2_phrases
            embed_phrases = np.array(embed_phrases)

            # Calculer les similarités avec les embeddings de référence pré-calculés
            similarites = cosine_similarity(self.reference_embeddings, embed_phrases)
            similarites_max = similarites.max(axis=0)

            # Normaliser pour obtenir des scores [0, 1]
            min_val = similarites_max.min()
            max_val = similarites_max.max()
            if max_val - min_val > 0:
                similarites_norm = (similarites_max - min_val) / (max_val - min_val)
            else:
                similarites_norm = similarites_max * 0  # all zeros

            # Filtrer les phrases ayant un score élevé
            threshold = self.config.markdown_filtering.similarity_threshold
            context_window = self.config.markdown_filtering.context_window
            relevant_indices = set()

            for i, score in enumerate(similarites_norm):
                if score >= threshold:
                    context_indices = self._extract_context_around_phrase(
                        phrases, i, context_window
                    )
                    relevant_indices.update(context_indices)

            # Reconstruire le contenu
            if relevant_indices:
                relevant_phrases = [phrases[i] for i in sorted(list(relevant_indices))]
                filtered_content = ". ".join(relevant_phrases)
                return (
                    filtered_content if filtered_content.strip() else markdown_content
                ), co2_for_this_document
            else:
                return markdown_content, co2_for_this_document

        except Exception as e:
            self.logger.error(f"Erreur lors du filtrage: {e}")
            return markdown_content, co2_for_this_document

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
