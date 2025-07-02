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

        for i, (resultat, lieu) in enumerate(resultats_a_filtrer, 1):
            self.logger.info(f"Filtrage {i}/{len(resultats_a_filtrer)}: {lieu.nom}")

            try:
                filtered_markdown = self._filter_single_markdown(
                    resultat.markdown_nettoye, lieu.nom, lieu.type_lieu
                )

                # Mise à jour en base
                db_manager.update_filtered_markdown(
                    resultat.id_resultats_extraction, filtered_markdown
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
        return stats

    def _extract_context_around_phrase(
        self, phrases: List[str], phrase_index: int, context_window: int = 1
    ) -> List[int]:
        """Extrait les indices des phrases dans la fenêtre de contexte autour d'une phrase donnée."""
        start_idx = max(0, phrase_index - context_window)
        end_idx = min(len(phrases), phrase_index + context_window + 1)
        return list(range(start_idx, end_idx))

    def _get_embeddings_via_api(self, texts: List[str]) -> List[List[float]]:
        """
        Obtient les embeddings via l'API Ollama compatible OpenAI.

        Args:
            texts: Liste des textes à encoder

        Returns:
            Liste des vecteurs d'embeddings
        """
        if not texts:
            return []

        try:
            # URL de l'endpoint embeddings
            url = f"{self.llm_client.base_url}/embeddings"

            # Préparer la requête
            payload = {
                "model": self.config.markdown_filtering.embedding_model,
                "input": texts,
            }

            response = self.llm_client.session.post(url, json=payload, timeout=30)
            response.raise_for_status()

            result = response.json()
            embeddings = [data["embedding"] for data in result["data"]]

            self.logger.debug(f"Embeddings calculés: {len(embeddings)} vecteurs")
            return embeddings

        except Exception as e:
            self.logger.error(f"Erreur calcul embeddings: {e}")
            raise

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
                    themes.extend([f"horaires d'ouverture {type_lieu} de {nom}"])
                else:
                    themes.extend([f"horaires d'ouverture {nom}"])
            else:
                if type_lieu:
                    themes.extend([f"horaires d'ouverture {type_lieu}"])

            # Pré-calculer les embeddings des thèmes avec l'API
            embed_themes = self._get_embeddings_via_api(themes)
            embed_themes = np.array(embed_themes)

            # Segmenter le texte en phrases
            split_chars = ["."]
            regex = "|".join(map(re.escape, split_chars))
            phrases = [
                p.strip() for p in re.split(regex, markdown_content) if p.strip()
            ]

            if not phrases:
                return markdown_content

            # Générer les embeddings des phrases avec l'API
            embed_phrases = self._get_embeddings_via_api(phrases)
            embed_phrases = np.array(embed_phrases)

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
            threshold = self.config.markdown_filtering.similarity_threshold

            # Obtenir le contexte autour des phrases pertinentes
            context_window = self.config.markdown_filtering.context_window

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
