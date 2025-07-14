"""
Gestionnaire de statistiques basé sur les requêtes SQL.
Remplace l'ancien système de classes de statistiques.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from ..core.ConfigManager import ConfigManager
from ..core.DatabaseManager import DatabaseManager
from ..core.Logger import create_logger

logger = create_logger("StatsManager")


class StatsManager:
    """Gestionnaire de statistiques basé sur les requêtes SQL."""

    def __init__(self, config: ConfigManager, logger):
        self.config = config
        self.logger = logger
        self.db_manager = DatabaseManager(
            db_file=config.database.db_file, table_name="resultats_extraction"
        )

    def get_pipeline_stats(self) -> Dict[str, Any]:
        """
        Génère les statistiques du pipeline à partir des requêtes SQL sur toutes les données.

        :return: Dictionnaire contenant toutes les statistiques
        """
        logger.info("Génération des statistiques globales depuis la base de données...")

        stats = {
            "execution_id": "global",
            "timestamp": datetime.now().isoformat(),
            "urls": self._get_url_stats(),
            "markdown": self._get_markdown_stats(),
            "llm": self._get_llm_stats(),
            "comparisons": self._get_comparison_stats(),
            "global": self._get_global_stats(),
        }

        return stats

    def _get_latest_execution_id(self) -> Optional[int]:
        """Récupère l'ID de l'exécution la plus récente."""
        try:
            query = "SELECT id_executions FROM executions ORDER BY date_execution DESC LIMIT 1"
            result = self.db_manager.execute_query(query)
            if result and len(result) > 0:
                return result[0][0]  # Premier élément du premier tuple
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'exécution: {e}")
        return None

    def _get_url_stats(self) -> Dict[str, Any]:
        """Statistiques de traitement des URLs."""
        try:
            query = """
            SELECT 
                COUNT(*) as total_urls,
                COUNT(CASE WHEN statut_url = 'ok' THEN 1 END) as successful_urls,
                COUNT(CASE WHEN statut_url != 'ok' THEN 1 END) as failed_urls,
                AVG(CASE WHEN statut_url = 'ok' AND markdown_brut IS NOT NULL THEN 
                    LENGTH(markdown_brut) END) as avg_content_length,
                COUNT(CASE WHEN code_http >= 400 THEN 1 END) as http_errors,
                COUNT(CASE WHEN code_http = 0 THEN 1 END) as timeout_errors
            FROM resultats_extraction
            """
            result = self.db_manager.execute_query(query)

            if result and len(result) > 0:
                row = result[0]
                total = row[0] or 0
                successful = row[1] or 0

                return {
                    "total": total,
                    "successful": successful,
                    "failed": row[2] or 0,
                    "success_rate": f"{(successful / total * 100):.1f}%"
                    if total > 0
                    else "0%",
                    "avg_content_length": f"{row[3]:.0f}" if row[3] else "N/A",
                    "http_errors": row[4] or 0,
                    "timeout_errors": row[5] or 0,
                }
        except Exception as e:
            logger.error(f"Erreur lors du calcul des stats URLs: {e}")

        return {
            "total": 0,
            "successful": 0,
            "failed": 0,
            "success_rate": "0%",
            "avg_content_length": "N/A",
            "http_errors": 0,
            "timeout_errors": 0,
        }

    def _get_markdown_stats(self) -> Dict[str, Any]:
        """Statistiques de traitement Markdown."""
        try:
            query = """
            SELECT 
                COUNT(CASE WHEN markdown_brut IS NOT NULL AND markdown_brut != '' THEN 1 END) as processed,
                COUNT(CASE WHEN markdown_nettoye IS NOT NULL AND markdown_nettoye != '' THEN 1 END) as cleaned,
                COUNT(CASE WHEN markdown_filtre IS NOT NULL AND markdown_filtre != '' THEN 1 END) as filtered,
                AVG(CASE WHEN markdown_filtre IS NOT NULL AND markdown_filtre != '' THEN 
                    LENGTH(markdown_filtre) END) as avg_filtered_length,
                SUM(CASE WHEN markdown_brut IS NOT NULL AND markdown_nettoye IS NOT NULL THEN
                    LENGTH(markdown_brut) - LENGTH(markdown_nettoye) ELSE 0 END) as chars_cleaned
            FROM resultats_extraction
            """
            result = self.db_manager.execute_query(query)

            if result and len(result) > 0:
                row = result[0]
                return {
                    "processed": row[0] or 0,
                    "cleaned": row[1] or 0,
                    "filtered": row[2] or 0,
                    "avg_filtered_length": f"{row[3]:.0f}" if row[3] else "N/A",
                    "chars_cleaned": row[4] or 0,
                }
        except Exception as e:
            logger.error(f"Erreur lors du calcul des stats Markdown: {e}")

        return {
            "processed": 0,
            "cleaned": 0,
            "filtered": 0,
            "avg_filtered_length": "N/A",
            "chars_cleaned": 0,
        }

    def _get_llm_stats(self) -> Dict[str, Any]:
        """Statistiques de traitement LLM."""
        try:
            query = """
            SELECT 
                COUNT(CASE WHEN markdown_filtre IS NOT NULL AND markdown_filtre != '' THEN 1 END) as attempted_extractions,
                COUNT(CASE WHEN llm_horaires_json IS NOT NULL AND llm_horaires_json != '' 
                    AND NOT llm_horaires_json LIKE 'Erreur%' THEN 1 END) as successful_json,
                COUNT(CASE WHEN llm_horaires_osm IS NOT NULL AND llm_horaires_osm != '' 
                    AND NOT llm_horaires_osm LIKE 'Erreur%' THEN 1 END) as successful_osm,
                AVG(CASE WHEN llm_horaires_osm IS NOT NULL AND llm_horaires_osm != '' 
                    AND NOT llm_horaires_osm LIKE 'Erreur%' THEN 
                    LENGTH(llm_horaires_osm) END) as avg_schedule_length,
                SUM(llm_consommation_requete) as total_co2_emissions
            FROM resultats_extraction
            """
            result = self.db_manager.execute_query(query)

            if result and len(result) > 0:
                row = result[0]
                attempted = row[0] or 0
                successful_json = row[1] or 0
                successful_osm = row[2] or 0

                return {
                    "attempted": attempted,
                    "successful_json": successful_json,
                    "successful_osm": successful_osm,
                    "failed": attempted - successful_osm,
                    "success_rate": f"{(successful_osm / attempted * 100):.1f}%"
                    if attempted > 0
                    else "0%",
                    "avg_schedule_length": f"{row[3]:.0f}" if row[3] else "N/A",
                    "total_co2_emissions": f"{(row[4] or 0) * 1000:.3f}g",
                }
        except Exception as e:
            logger.error(f"Erreur lors du calcul des stats LLM: {e}")

        return {
            "attempted": 0,
            "successful_json": 0,
            "successful_osm": 0,
            "failed": 0,
            "success_rate": "0%",
            "avg_schedule_length": "N/A",
            "total_co2_emissions": "0.000g",
        }

    def _get_comparison_stats(self) -> Dict[str, Any]:
        """Statistiques de comparaison."""
        try:
            query = """
            SELECT 
                COUNT(CASE WHEN horaires_identiques IS NOT NULL THEN 1 END) as total_comparisons,
                COUNT(CASE WHEN horaires_identiques = 1 THEN 1 END) as identical,
                COUNT(CASE WHEN horaires_identiques = 0 THEN 1 END) as different,
                COUNT(CASE WHEN horaires_identiques IS NULL AND llm_horaires_osm IS NOT NULL 
                    AND llm_horaires_osm != '' AND NOT llm_horaires_osm LIKE 'Erreur%' THEN 1 END) as not_compared
            FROM resultats_extraction
            """
            result = self.db_manager.execute_query(query)

            if result and len(result) > 0:
                row = result[0]
                total = row[0] or 0
                identical = row[1] or 0
                different = row[2] or 0
                not_compared = row[3] or 0

                return {
                    "total": total,
                    "identical": identical,
                    "different": different,
                    "not_compared": not_compared,
                    "accuracy_rate": f"{(identical / total * 100):.1f}%"
                    if total > 0
                    else "0%",
                }
        except Exception as e:
            logger.error(f"Erreur lors du calcul des stats de comparaison: {e}")

        return {
            "total": 0,
            "identical": 0,
            "different": 0,
            "not_compared": 0,
            "accuracy_rate": "0%",
        }

    def _get_global_stats(self) -> Dict[str, Any]:
        """Statistiques globales."""
        try:
            # Statistiques d'exécution
            exec_query = """
            SELECT 
                MAX(date_execution),
                (SELECT llm_modele FROM executions ORDER BY date_execution DESC LIMIT 1),
                (SELECT llm_fournisseur FROM executions ORDER BY date_execution DESC LIMIT 1),
                SUM(llm_consommation_execution)
            FROM executions
            """
            exec_result = self.db_manager.execute_query(exec_query)

            # Statistiques des résultats
            results_query = """
            SELECT 
                COUNT(*) as total_records,
                COUNT(CASE WHEN erreurs_pipeline IS NOT NULL AND erreurs_pipeline != '' THEN 1 END) as records_with_errors
            FROM resultats_extraction
            """
            results_result = self.db_manager.execute_query(results_query)

            global_stats = {
                "execution_id": "global",
                "total_records": 0,
                "records_with_errors": 0,
                "execution_date": "N/A",
                "llm_model": "N/A",
                "llm_provider": "N/A",
                "total_co2_emissions": "0.000g",
            }

            if exec_result and len(exec_result) > 0:
                exec_row = exec_result[0]
                global_stats.update(
                    {
                        "execution_date": exec_row[0] or "N/A",
                        "llm_model": exec_row[1] or "N/A",
                        "llm_provider": exec_row[2] or "N/A",
                        "total_co2_emissions": f"{(exec_row[3] or 0) * 1000:.3f}g",
                    }
                )

            if results_result and len(results_result) > 0:
                results_row = results_result[0]
                global_stats.update(
                    {
                        "total_records": results_row[0] or 0,
                        "records_with_errors": results_row[1] or 0,
                    }
                )

            return global_stats

        except Exception as e:
            logger.error(f"Erreur lors du calcul des stats globales: {e}")
            return {
                "execution_id": "global",
                "total_records": 0,
                "records_with_errors": 0,
                "execution_date": "N/A",
                "llm_model": "N/A",
                "llm_provider": "N/A",
                "total_co2_emissions": "0.000g",
            }

    def _empty_stats(self) -> Dict[str, Any]:
        """Retourne des statistiques vides."""
        return {
            "execution_id": None,
            "timestamp": datetime.now().isoformat(),
            "urls": {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "success_rate": "0%",
                "avg_content_length": "N/A",
                "http_errors": 0,
                "timeout_errors": 0,
            },
            "markdown": {
                "processed": 0,
                "cleaned": 0,
                "filtered": 0,
                "avg_filtered_length": "N/A",
                "chars_cleaned": 0,
            },
            "llm": {
                "attempted": 0,
                "successful_json": 0,
                "successful_osm": 0,
                "failed": 0,
                "success_rate": "0%",
                "avg_schedule_length": "N/A",
                "total_co2_emissions": "0.000g",
            },
            "comparisons": {
                "total": 0,
                "identical": 0,
                "different": 0,
                "not_compared": 0,
                "accuracy_rate": "0%",
            },
            "global": {
                "execution_id": None,
                "total_records": 0,
                "records_with_errors": 0,
                "execution_date": "N/A",
                "llm_model": "N/A",
                "llm_provider": "N/A",
                "total_co2_emissions": "0.000g",
            },
        }

    def display_stats(self):
        """Affiche les statistiques de manière formatée."""
        stats = self.get_pipeline_stats()

        logger.info("=== STATISTIQUES DU PIPELINE ===")
        logger.info(f"Exécution: {stats['execution_id']}")
        logger.info(f"Timestamp: {stats['timestamp']}")

        # URLs
        url_stats = stats["urls"]
        logger.info("--- URLs ---")
        logger.info(f"Total: {url_stats['total']}")
        logger.info(f"Succès: {url_stats['successful']} ({url_stats['success_rate']})")
        logger.info(f"Échecs: {url_stats['failed']}")
        logger.info(f"Erreurs HTTP: {url_stats['http_errors']}")
        logger.info(f"Timeouts: {url_stats['timeout_errors']}")

        # Markdown
        markdown_stats = stats["markdown"]
        logger.info("--- Markdown ---")
        logger.info(f"Traités: {markdown_stats['processed']}")
        logger.info(f"Nettoyés: {markdown_stats['cleaned']}")
        logger.info(f"Filtrés: {markdown_stats['filtered']}")
        logger.info(f"Caractères nettoyés: {markdown_stats['chars_cleaned']}")

        # LLM
        llm_stats = stats["llm"]
        logger.info("--- LLM ---")
        logger.info(f"Tentatives: {llm_stats['attempted']}")
        logger.info(f"JSON réussis: {llm_stats['successful_json']}")
        logger.info(
            f"OSM réussis: {llm_stats['successful_osm']} ({llm_stats['success_rate']})"
        )
        logger.info(f"Échecs: {llm_stats['failed']}")
        logger.info(f"Émissions CO2: {llm_stats['total_co2_emissions']}")

        # Comparaisons
        comp_stats = stats["comparisons"]
        logger.info("--- Comparaisons ---")
        logger.info(f"Total: {comp_stats['total']}")
        logger.info(f"Identiques: {comp_stats['identical']}")
        logger.info(f"Différents: {comp_stats['different']}")
        logger.info(f"Non comparés: {comp_stats['not_compared']}")
        logger.info(f"Précision: {comp_stats['accuracy_rate']}")

        # Global
        global_stats = stats["global"]
        logger.info("--- Global ---")
        logger.info(f"Enregistrements: {global_stats['total_records']}")
        logger.info(f"Avec erreurs: {global_stats['records_with_errors']}")
        logger.info(f"Modèle: {global_stats['llm_model']}")
        logger.info(f"Émissions totales: {global_stats['total_co2_emissions']}")
        logger.info("=== FIN STATISTIQUES ===")
