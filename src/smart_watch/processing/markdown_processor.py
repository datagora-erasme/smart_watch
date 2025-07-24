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

        # Par défaut, on utilise le modèle local (SentenceTransformer)
        if (
            embed_config.embed_fournisseur == "LOCAL"
            or not embed_config.embed_fournisseur
        ):
            try:
                self.local_embed_model = SentenceTransformer(embed_config.embed_modele)
                self.logger.info(
                    f"Modèle d'embedding local chargé: {embed_config.embed_modele}"
                )
                self.embed_client = None  # Pas de client API pour le local
            except Exception as e:
                self.logger.error(f"Erreur chargement modèle local: {e}")
                raise
        elif embed_config.embed_fournisseur == "MISTRAL":
            self.embed_client = MistralAPIClient(
                api_key=embed_config.embed_api_key,
                model=embed_config.embed_modele,
                timeout=30,
            )
            self.logger.debug(
                f"Client embeddings Mistral initialisé avec modèle {embed_config.embed_modele}"
            )
        else:  # Par défaut ou si "OPENAI"
            if embed_config.embed_api_key:
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

        # Ne bloque pas si embed_client est None (cas LOCAL)
        if not self.local_embed_model and not self.embed_client:
            self.logger.warning("Aucun modèle d'embedding disponible - filtrage ignoré")
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

                # Mise à jour en base
                db_manager.update_filtered_markdown(
                    resultat.id_resultats_extraction,
                    filtered_markdown,
                    co2_emissions,
                )

                if filtered_markdown and len(filtered_markdown.strip()) > 0:
                    successful_count += 1
                    self.logger.debug(
                        f"*{lieu.identifiant}* Markdown filtré pour '{lieu.nom}': {len(filtered_markdown)} caractères"
                    )
                else:
                    self.logger.warning(
                        f"*{lieu.identifiant}* Aucun contenu pertinent trouvé pour '{lieu.nom}'"
                    )

            except Exception as e:
                self.logger.error(
                    f"*{lieu.identifiant}* Erreur filtrage markdown pour '{lieu.nom}': {e}"
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
        # Paramètres de chunking
        CHUNK_SIZE = 200  # Nombre de caractères par chunk
        CHUNK_OVERLAP = 50  # Chevauchement entre chunks

        co2_for_this_document = 0.0
        if (
            not markdown_content
            or len(markdown_content.strip())
            < self.config.markdown_filtering.min_content_length
        ):
            return markdown_content, co2_for_this_document

        try:
            # Créer des chunks avec chevauchement
            chunks = []
            chunk_positions = []  # Pour retrouver la position dans le texte original

            text = markdown_content.strip()
            start = 0

            while start < len(text):
                end = min(start + CHUNK_SIZE, len(text))

                # Ajuster la fin pour éviter de couper au milieu d'un mot
                if end < len(text):
                    # Chercher le dernier espace avant la fin
                    last_space = text.rfind(" ", start, end)
                    if last_space > start:
                        end = last_space

                chunk = text[start:end].strip()
                if chunk:  # Ignorer les chunks vides
                    chunks.append(chunk)
                    chunk_positions.append((start, end))

                # Avancer avec chevauchement
                start = max(start + 1, end - CHUNK_OVERLAP)

                # Éviter la boucle infinie si on n'avance pas
                if start >= end:
                    start = end

            if not chunks:
                return markdown_content, co2_for_this_document

            # Générer les embeddings pour les chunks
            embed_chunks, co2_chunks = self._get_embeddings(chunks)
            co2_for_this_document += co2_chunks
            embed_chunks = np.array(embed_chunks)

            # Calculer les similarités avec les embeddings de référence
            if self.reference_embeddings is None:
                raise ValueError("Les embeddings de référence ne sont pas calculés.")

            similarites = cosine_similarity(self.reference_embeddings, embed_chunks)
            similarites_max = similarites.max(axis=0)

            # Utiliser le seuil directement sans normalisation
            threshold = self.config.markdown_filtering.similarity_threshold
            context_window = self.config.markdown_filtering.context_window

            # Identifier les chunks pertinents
            relevant_chunks = set()
            for i, score in enumerate(similarites_max):
                if score >= threshold:
                    # Ajouter le contexte autour du chunk pertinent
                    start_ctx = max(0, i - context_window)
                    end_ctx = min(len(chunks), i + context_window + 1)
                    for j in range(start_ctx, end_ctx):
                        relevant_chunks.add(j)

            if not relevant_chunks:
                return markdown_content, co2_for_this_document

            # Reconstruire le contenu à partir des chunks pertinents
            # Fusionner les régions qui se chevauchent pour éviter les doublons
            sorted_chunks = sorted(list(relevant_chunks))
            merged_regions = []

            for chunk_idx in sorted_chunks:
                start_pos, end_pos = chunk_positions[chunk_idx]

                # Fusionner avec la région précédente si elle chevauche
                if merged_regions and start_pos <= merged_regions[-1][1]:
                    merged_regions[-1] = (
                        merged_regions[-1][0],
                        max(merged_regions[-1][1], end_pos),
                    )
                else:
                    merged_regions.append((start_pos, end_pos))

            # Extraire le contenu filtré
            filtered_parts = []
            for start_pos, end_pos in merged_regions:
                filtered_parts.append(text[start_pos:end_pos])

            filtered_content = "\n\n".join(filtered_parts)

            return (
                filtered_content if filtered_content.strip() else markdown_content
            ), co2_for_this_document

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
