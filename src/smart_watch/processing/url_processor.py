"""
Processeur pour les extractions d'URLs.
"""

import concurrent.futures
from typing import Dict

from ..core.ConfigManager import ConfigManager
from ..core.URLRetriever import retrieve_url
from ..stats import URLProcessingStats
from .database_manager import DatabaseManager


class URLProcessor:
    """Processeur pour les extractions d'URLs."""

    def __init__(self, config: ConfigManager, logger):
        self.config = config
        self.logger = logger

    def process_urls(
        self, db_manager: DatabaseManager, execution_id: int
    ) -> URLProcessingStats:
        """Traite les URLs en parallèle."""
        self.logger.section("EXTRACTION CONTENU URLs")

        resultats_a_traiter = db_manager.get_pending_urls(execution_id)
        stats = URLProcessingStats()

        if not resultats_a_traiter:
            self.logger.info("Aucune URL à traiter")
            return stats

        self.logger.info(f"{len(resultats_a_traiter)} URLs à traiter")
        stats.processed = len(resultats_a_traiter)

        # Traitement parallèle optimisé
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.config.processing.nb_threads_url
        ) as executor:
            future_to_data = {}

            for resultat, lieu in resultats_a_traiter:
                row_data = {
                    "identifiant": lieu.identifiant,
                    "nom": lieu.nom,
                    "url": lieu.url,
                    "type_lieu": lieu.type_lieu,
                }

                future = executor.submit(
                    self._process_single_url, row_data, resultat.id_resultats_extraction
                )
                future_to_data[future] = (resultat.id_resultats_extraction, lieu.nom)

            # Traitement des résultats avec batch updates
            for future in concurrent.futures.as_completed(future_to_data):
                resultat_id, nom = future_to_data[future]
                try:
                    result_data = future.result()
                    db_manager.update_url_result(resultat_id, result_data)

                    if result_data.get("statut") == "ok":
                        stats.successful += 1
                        stats.markdown_extracted += 1
                        self.logger.debug(f"URL OK: {nom}")
                    else:
                        stats.errors += 1
                        # Catégoriser les erreurs
                        if result_data.get("code_http", 0) >= 400:
                            stats.http_errors += 1
                        elif "timeout" in result_data.get("message", "").lower():
                            stats.timeout_errors += 1
                        self.logger.warning(
                            f"URL échec: {nom} - {result_data.get('message')}"
                        )

                except Exception as e:
                    stats.errors += 1
                    self.logger.error(f"Erreur traitement URL {nom}: {e}")

        self.logger.info(
            f"URLs traitées: {stats.successful}/{stats.processed} réussies"
        )
        return stats

    def _process_single_url(self, row_data: Dict, resultat_id: int) -> Dict:
        """Traite une URL individuelle."""
        return retrieve_url(
            row_data,
            sortie="markdown",
            encoding_errors="ignore",
            config=self.config,
        )
        self.logger.info(
            f"URLs traitées: {stats.urls_successful}/{stats.urls_processed} réussies"
        )
        return stats

    def _process_single_url(self, row_data: Dict, resultat_id: int) -> Dict:
        """Traite une URL individuelle."""
        return retrieve_url(
            row_data,
            sortie="markdown",
            encoding_errors="ignore",
            config=self.config,
        )
