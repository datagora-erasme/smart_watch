"""
Processeur pour les extractions d'URLs.
"""

import concurrent.futures
from typing import Dict

from ..core.ConfigManager import ConfigManager
from ..core.URLRetriever import retrieve_url
from .database_processor import DatabaseProcessor


class URLProcessor:
    """Processeur pour les extractions d'URLs."""

    def __init__(self, config: ConfigManager, logger):
        self.config = config
        self.logger = logger

    def process_urls(self, db_manager: DatabaseProcessor, execution_id: int):
        """Traite les URLs en parallèle."""
        self.logger.section("EXTRACTION CONTENU URLs")

        resultats_a_traiter = db_manager.get_pending_urls(execution_id)

        if not resultats_a_traiter:
            self.logger.info("Aucune URL à traiter")
            return

        self.logger.info(f"{len(resultats_a_traiter)} URLs à traiter")

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
            successful_count = 0
            for future in concurrent.futures.as_completed(future_to_data):
                resultat_id, nom = future_to_data[future]
                try:
                    result_data = future.result()
                    db_manager.update_url_result(resultat_id, result_data)

                    if result_data.get("statut") == "ok":
                        successful_count += 1
                        self.logger.debug(f"URL OK: {nom}")
                    else:
                        self.logger.warning(
                            f"URL échec: {nom} - {result_data.get('message')}"
                        )

                except Exception as e:
                    self.logger.error(f"Erreur traitement URL {nom}: {e}")

        self.logger.info(
            f"URLs traitées: {successful_count}/{len(resultats_a_traiter)} réussies"
        )

    def _process_single_url(self, row_data: Dict, resultat_id: int) -> Dict:
        """Traite une URL individuelle."""
        return retrieve_url(
            row_data,
            sortie="markdown",
            encoding_errors="ignore",
            config=self.config,
        )
