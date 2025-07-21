"""
Processeur pour les extractions d'URLs.
"""

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

        # Le traitement parallèle avec ThreadPoolExecutor n'est pas compatible
        # avec l'API sync de Playwright. Passage en traitement séquentiel.
        # Pour réactiver le parallélisme, il faudrait une refonte en asyncio.
        self.logger.warning(
            "Le traitement des URLs est en mode séquentiel en raison de l'utilisation de Playwright."
        )

        successful_count = 0
        total_urls = len(resultats_a_traiter)
        for index, (resultat, lieu) in enumerate(resultats_a_traiter, 1):
            try:
                row_data = {
                    "identifiant": lieu.identifiant,
                    "nom": lieu.nom,
                    "url": lieu.url,
                    "type_lieu": lieu.type_lieu,
                }
                result_data = self._process_single_url(
                    row_data, resultat.id_resultats_extraction, index, total_urls
                )
                db_manager.update_url_result(
                    resultat.id_resultats_extraction, result_data
                )

                if result_data.get("statut") == "ok":
                    successful_count += 1
                    self.logger.debug(f"URL OK: {lieu.nom}")
                else:
                    self.logger.warning(
                        f"URL échec: {lieu.nom} - {result_data.get('message')}"
                    )
            except Exception as e:
                self.logger.error(f"Erreur traitement URL {lieu.nom}: {e}")

        self.logger.info(
            f"URLs traitées: {successful_count}/{len(resultats_a_traiter)} réussies"
        )

    def _process_single_url(
        self, row_data: Dict, resultat_id: int, index: int, total: int
    ) -> Dict:
        """Traite une URL individuelle."""
        return retrieve_url(
            row_data,
            sortie="markdown",
            encoding_errors="ignore",
            config=self.config,
            index=index,
            total=total,
        )
