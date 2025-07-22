"""
Processeur pour filtrer le contenu markdown et extraire les sections pertinentes aux horaires.
Utilise des embeddings sémantiques pour identifier les sections les plus pertinentes.
"""

from typing import List, Tuple

import numpy as np
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

        if embed_config.embed_fournisseur == "MISTRAL":
            self.embed_client = MistralAPIClient(
                api_key=embed_config.embed_api_key_mistral,
                model=embed_config.embed_modele_mistral,
                timeout=30,
            )
            self.logger.debug(
                f"Client embeddings Mistral initialisé avec modèle {embed_config.embed_modele_mistral}"
            )
        else:  # Par défaut ou si "OPENAI"
            self.embed_client = OpenAICompatibleClient(
                api_key=embed_config.embed_api_key_openai,
                model=embed_config.embed_modele_openai,
                base_url=embed_config.embed_base_url_openai,
                timeout=30,
            )
            self.logger.debug(
                f"Client embeddings OpenAI initialisé avec modèle {embed_config.embed_modele_openai}"
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
        if not self.embed_client:
            raise ValueError("Le client embeddings n'est pas initialisé")

        try:
            # Appel aux embeddings avec le client approprié
            response: LLMResponse = self.embed_client.call_embeddings(texts)

            if isinstance(response.content, list):
                embeddings = np.array(response.content)

                # Accumuler les émissions CO2
                self.total_co2_emissions += response.co2_emissions

                return embeddings, response.co2_emissions
            else:
                self.logger.error("Format de réponse embeddings inattendu")
                raise ValueError("Format de réponse embeddings inattendu")

        except Exception as e:
            self.logger.error(f"Erreur lors du calcul des embeddings: {e}")
            raise

    def _calculate_reference_embeddings(self):
        """Calcule les embeddings pour les phrases de référence."""
        if not self.reference_phrases:
            raise ValueError("Aucune phrase de référence configurée")

        # Calculer les embeddings pour toutes les phrases de référence
        embeddings, _ = self._get_embeddings(self.reference_phrases)

        # Stocker pour réutilisation
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
                    ResultatsExtraction.markdown_filtre == "",  # Pas encore filtré
                )
                .all()
            )
        finally:
            session.close()

    def process_markdown_filtering(self, db_manager, execution_id: int):
        """Filtre le contenu markdown."""
        self.logger.section("FILTRAGE MARKDOWN POUR HORAIRES")

        # Reset des émissions pour cette exécution
        self.total_co2_emissions = 0.0
        self.reference_embeddings = None  # Réinitialiser pour chaque exécution

        if not self.embed_client:
            self.logger.warning("Client embeddings non disponible - filtrage ignoré")
            return

        # Récupérer les enregistrements avec markdown à filtrer
        resultats_a_filtrer = self._get_pending_markdown_filtering(
            db_manager, execution_id
        )

        if not resultats_a_filtrer:
            self.logger.info("Aucun markdown à filtrer")
            return

        self.logger.info(f"{len(resultats_a_filtrer)} contenus markdown à filtrer")

        # Pré-calculer les embeddings de référence une seule fois
        try:
            self.logger.info("Pré-calcul des embeddings de référence...")
            embed_themes, _ = self._get_embeddings(self.reference_phrases)
            self.reference_embeddings = np.array(embed_themes)
            self.logger.info(
                f"{len(self.reference_phrases)} embeddings de référence calculés."
            )
        except Exception as e:
            self.logger.error(f"Erreur calcul embeddings de référence: {e}. Arrêt.")
            return

        successful_count = 0
        for i, (resultat, lieu) in enumerate(resultats_a_filtrer, 1):
            self.logger.info(
                f"[{lieu.identifiant}] Filtrage {i}/{len(resultats_a_filtrer)} - '{lieu.nom}'"
            )

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
                    successful_count += 1
                    self.logger.debug(
                        f"[{lieu.identifiant}] Markdown filtré pour '{lieu.nom}': {len(filtered_markdown)} caractères"
                    )
                else:
                    self.logger.warning(
                        f"[{lieu.identifiant}] Aucun contenu pertinent trouvé pour '{lieu.nom}'"
                    )

            except Exception as e:
                self.logger.error(
                    f"[{lieu.identifiant}] Erreur filtrage markdown pour '{lieu.nom}': {e}"
                )
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
            f"Markdown filtré: {successful_count}/{len(resultats_a_filtrer)} réussies"
        )

        # Mettre à jour les émissions totales d'embeddings dans la base
        if self.total_co2_emissions > 0:
            db_manager.update_execution_embeddings(
                execution_id, self.total_co2_emissions
            )
            self.logger.info(
                f"Émissions CO2 embeddings totales: {self.total_co2_emissions:.6f} kg"
            )

    def _extract_context_around_phrase(
        self, phrases: List[str], phrase_index: int, context_window: int = 1
    ) -> List[int]:
        """Extrait les indices des phrases dans la fenêtre de contexte autour d'une phrase donnée."""
        start_idx = max(0, phrase_index - context_window)
        end_idx = min(len(phrases), phrase_index + context_window + 1)
        return list(range(start_idx, end_idx))

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
            # Diviser le contenu en lignes, en conservant les sauts de ligne
            lines = markdown_content.splitlines(keepends=True)

            # Filtrer les lignes vides pour l'analyse sémantique, mais les conserver pour la reconstruction
            non_empty_lines = [line for line in lines if line.strip()]

            if not non_empty_lines:
                return markdown_content, co2_for_this_document

            # Générer les embeddings pour les lignes non vides
            embed_lines, co2_lines = self._get_embeddings(non_empty_lines)
            co2_for_this_document += co2_lines
            embed_lines = np.array(embed_lines)

            # Calculer les similarités avec les embeddings de référence
            similarites = cosine_similarity(self.reference_embeddings, embed_lines)
            similarites_max = similarites.max(axis=0)

            # Normaliser les scores
            min_val, max_val = similarites_max.min(), similarites_max.max()
            similarites_norm = (
                (similarites_max - min_val) / (max_val - min_val)
                if max_val > min_val
                else np.zeros_like(similarites_max)
            )

            # Identifier les lignes pertinentes
            threshold = self.config.markdown_filtering.similarity_threshold
            context_window = self.config.markdown_filtering.context_window

            # Créer une map pour retrouver l'index original dans `lines`
            line_map = {
                i: original_idx
                for i, (original_idx, _) in enumerate(
                    filter(lambda x: x[1].strip(), enumerate(lines))
                )
            }

            relevant_indices = set()
            for i, score in enumerate(similarites_norm):
                if score >= threshold:
                    # Extraire le contexte basé sur les lignes non vides
                    context_indices_non_empty = self._extract_context_around_phrase(
                        non_empty_lines, i, context_window
                    )
                    # Mapper vers les indices originaux
                    for idx in context_indices_non_empty:
                        if idx in line_map:
                            relevant_indices.add(line_map[idx])

            # Reconstruire le contenu en préservant la structure
            if relevant_indices:
                # Assurer que les lignes vides entre les sections pertinentes sont conservées
                final_indices = set()
                sorted_indices = sorted(list(relevant_indices))
                if sorted_indices:
                    for i in range(min(sorted_indices), max(sorted_indices) + 1):
                        final_indices.add(i)

                filtered_content = "".join(
                    lines[i] for i in sorted(list(final_indices))
                )
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
