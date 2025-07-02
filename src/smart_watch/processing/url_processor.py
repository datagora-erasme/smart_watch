"""
Processeur pour les extractions d'URLs.
"""

import concurrent.futures
from typing import Dict

from ..core.ConfigManager import ConfigManager
from ..core.URLRetriever import retrieve_url
from .database_manager import DatabaseManager


class ProcessingStats:
    """Statistiques de traitement pour chaque étape."""

    def __init__(self):
        self.urls_processed: int = 0
        self.urls_successful: int = 0
        self.llm_processed: int = 0
        self.llm_successful: int = 0
        self.comparisons_processed: int = 0
        self.comparisons_successful: int = 0

    def get_summary(self) -> Dict[str, int]:
        return {
            "urls_processed": self.urls_processed,
            "urls_successful": self.urls_successful,
            "llm_processed": self.llm_processed,
            "llm_successful": self.llm_successful,
            "comparisons_processed": self.comparisons_processed,
            "comparisons_successful": self.comparisons_successful,
        }


class URLProcessor:
    """Processeur pour les extractions d'URLs."""

    def __init__(self, config: ConfigManager, logger):
        self.config = config
        self.logger = logger

    def process_urls(
        self, db_manager: DatabaseManager, execution_id: int
    ) -> ProcessingStats:
        """Traite les URLs en parallèle."""
        self.logger.section("EXTRACTION CONTENU URLs")

        resultats_a_traiter = db_manager.get_pending_urls(execution_id)
        stats = ProcessingStats()

        if not resultats_a_traiter:
            self.logger.info("Aucune URL à traiter")
            return stats

        self.logger.info(f"{len(resultats_a_traiter)} URLs à traiter")
        stats.urls_processed = len(resultats_a_traiter)

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
                        stats.urls_successful += 1
                        self.logger.debug(f"URL OK: {nom}")
                    else:
                        self.logger.warning(
                            f"URL échec: {nom} - {result_data.get('message')}"
                        )

                except Exception as e:
                    self.logger.error(f"Erreur traitement URL {nom}: {e}")

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
