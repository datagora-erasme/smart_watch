"""
Gestionnaire de statistiques basé sur les requêtes SQL.
Refactorisation avec libellés et unités pour un affichage flexible.
"""

from datetime import datetime
from typing import Any, Dict

from .ConfigManager import ConfigManager
from .DatabaseManager import DatabaseManager
from .Logger import create_logger

logger = create_logger("StatsManager")


class StatItem:
    """Représente un élément de statistique avec sa valeur, son libellé et son unité."""

    def __init__(self, value: Any, label: str, unit: str = "", format_str: str = "{}"):
        """
        Initialise un élément de statistique.

        Args:
            value (Any): la valeur de la statistique.
            label (str): le libellé de la statistique.
            unit (str): l'unité de la statistique.
            format_str (str): le format de la valeur, par défaut "{}".
        """
        self.value = value
        self.label = label
        self.unit = unit
        self.format_str = format_str

    def formatted_value(self) -> str:
        """Retourne la valeur formatée avec son unité.

        Si l'unité est vide, retourne juste la valeur formatée.
        Si la valeur est None, retourne "N/A".

        Returns:
            str: la valeur formatée avec son unité ou juste la valeur.
        """
        if self.value is None:
            return "N/A"
        formatted = self.format_str.format(self.value)
        return f"{formatted} {self.unit}" if self.unit else formatted

    def __str__(self) -> str:
        """Retourne une représentation en chaîne de l'élément de statistique.

        Returns:
            str: la représentation de l'élément de statistique.
        """
        return f"{self.label}: {self.formatted_value()}"


class StatsSection:
    """Représente une section de statistiques."""

    def __init__(self, title: str, items: Dict[str, StatItem]):
        """
        Initialise une section de statistiques.
        Args:
            title (str): le titre de la section.
            items (Dict[str, StatItem]): les éléments de statistique dans la section.
        """
        self.title = title
        self.items = items

    def get_item_value(self, key: str) -> Any:
        """Récupère la valeur d'un élément de statistique.

        Args:
            key (str): la clé de l'élément de statistique.

        Returns:
            Any: la valeur de l'élément de statistique, ou "N/A"
        """
        return self.items.get(key, StatItem("N/A", "")).value

    def get_formatted_value(self, key: str) -> str:
        """Récupère la valeur formatée d'un élément de statistique.

        Args:
            key (str): la clé de l'élément de statistique.

        Returns:
            str: la valeur formatée de l'élément de statistique, ou "N/A"
        """
        return self.items.get(key, StatItem("N/A", "")).formatted_value()


class StatsManager:
    """Gestionnaire de statistiques basé sur les requêtes SQL."""

    def __init__(self, config: ConfigManager, logger):
        """
        Initialise le gestionnaire de statistiques.
        Args:
            config (ConfigManager): instance de gestionnaire de configuration.
            logger: instance de logger pour les messages.
        """
        self.config = config
        self.logger = logger
        self.db_manager = DatabaseManager(db_file=config.database.db_file)

    def get_pipeline_stats(self) -> Dict[str, StatsSection]:
        """
        Génère les statistiques du pipeline avec libellés et unités.

        Returns:
            Dict[str, StatsSection]: dictionnaire des sections de statistiques.
        """
        logger.info("Génération des statistiques globales depuis la base de données...")

        return {
            "header": self._get_header_stats(),
            "urls": self._get_url_stats(),
            "markdown": self._get_markdown_stats(),
            "llm": self._get_llm_stats(),
            "comparisons": self._get_comparison_stats(),
            "global": self._get_global_stats(),
        }

    def _get_header_stats(self) -> StatsSection:
        """Crée une section de statistiques pour l'en-tête de l'exécution.

        Returns:
            StatsSection: Un objet StatsSection contenant :
                          - L'ID d'exécution ('global').
                          - L'horodatage actuel de la génération des statistiques.
        """
        return StatsSection(
            "En-tête",
            {
                "execution_id": StatItem("global", "ID d'exécution"),
                "timestamp": StatItem(datetime.now().isoformat(), "Horodatage"),
            },
        )

    def _get_url_stats(self) -> StatsSection:
        """Calcule et retourne les statistiques sur le traitement des URLs.

        Returns:
            StatsSection: Un objet StatsSection contenant les statistiques suivantes :
                          - Le nombre total d'URLs traitées.
                          - Le nombre de succès et d'échecs.
                          - Le taux de réussite.
                          - La taille moyenne du contenu.
                          - Le nombre d'erreurs HTTP et de timeouts.
        """
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
                success_rate = (successful / total * 100) if total > 0 else 0

                return StatsSection(
                    "URLs",
                    {
                        "total": StatItem(total, "Total des URLs"),
                        "successful": StatItem(successful, "URLs réussies"),
                        "failed": StatItem(row[2] or 0, "URLs échouées"),
                        "success_rate": StatItem(
                            success_rate, "Taux de réussite", "%", "{:.1f}"
                        ),
                        "avg_content_length": StatItem(
                            row[3] or 0,
                            "Taille moyenne du contenu",
                            " caractères",
                            "{:.0f}",
                        ),
                        "http_errors": StatItem(row[4] or 0, "Erreurs HTTP"),
                        "timeout_errors": StatItem(row[5] or 0, "Erreurs de timeout"),
                    },
                )
        except Exception as e:
            logger.error(f"Erreur lors du calcul des stats URLs: {e}")

        return StatsSection(
            "URLs",
            {
                "total": StatItem(0, "Total des URLs"),
                "successful": StatItem(0, "URLs réussies"),
                "failed": StatItem(0, "URLs échouées"),
                "success_rate": StatItem(0, "Taux de réussite", "%", "{:.1f}"),
                "avg_content_length": StatItem(
                    0, "Taille moyenne du contenu", " caractères"
                ),
                "http_errors": StatItem(0, "Erreurs HTTP"),
                "timeout_errors": StatItem(0, "Erreurs de timeout"),
            },
        )

    def _get_markdown_stats(self) -> StatsSection:
        """Calcule et retourne les statistiques sur le traitement des fichiers Markdown.

        Returns:
            StatsSection: Un objet StatsSection contenant les statistiques suivantes :
                          - Le nombre de documents traités, nettoyés et filtrés.
                          - La taille moyenne du contenu après filtrage.
                          - Le nombre total de caractères supprimés pendant le nettoyage.
        """
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
                return StatsSection(
                    "Markdown",
                    {
                        "processed": StatItem(row[0] or 0, "Documents traités"),
                        "cleaned": StatItem(row[1] or 0, "Documents nettoyés"),
                        "filtered": StatItem(row[2] or 0, "Documents filtrés"),
                        "avg_filtered_length": StatItem(
                            row[3] or 0,
                            "Taille moyenne après filtrage",
                            " caractères",
                            "{:.0f}",
                        ),
                        "chars_cleaned": StatItem(
                            row[4] or 0, "Caractères supprimés lors du nettoyage"
                        ),
                    },
                )
        except Exception as e:
            logger.error(f"Erreur lors du calcul des stats Markdown: {e}")

        return StatsSection(
            "Markdown",
            {
                "processed": StatItem(0, "Documents traités"),
                "cleaned": StatItem(0, "Documents nettoyés"),
                "filtered": StatItem(0, "Documents filtrés"),
                "avg_filtered_length": StatItem(
                    0, "Taille moyenne après filtrage", " caractères"
                ),
                "chars_cleaned": StatItem(0, "Caractères supprimés lors du nettoyage"),
            },
        )

    def _get_llm_stats(self) -> StatsSection:
        """Calcule et retourne les statistiques sur les extractions faites par le LLM.

        Returns:
            StatsSection: Un objet StatsSection contenant les statistiques suivantes :
                          - Le nombre d'extractions tentées, réussies (JSON et OSM), et échouées.
                          - Le taux de réussite.
                          - La taille moyenne des horaires extraits.
                          - Les émissions totales de CO2.
        """
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
                success_rate = (
                    (successful_osm / attempted * 100) if attempted > 0 else 0
                )

                return StatsSection(
                    "LLM",
                    {
                        "attempted": StatItem(attempted, "Extractions tentées"),
                        "successful_json": StatItem(
                            successful_json, "Extractions JSON réussies"
                        ),
                        "successful_osm": StatItem(
                            successful_osm, "Extractions OSM réussies"
                        ),
                        "failed": StatItem(
                            attempted - successful_osm, "Extractions échouées"
                        ),
                        "success_rate": StatItem(
                            success_rate, "Taux de réussite", "%", "{:.1f}"
                        ),
                        "avg_schedule_length": StatItem(
                            row[3] or 0,
                            "Taille moyenne des horaires",
                            " caractères",
                            "{:.0f}",
                        ),
                        "total_co2_emissions": StatItem(
                            (row[4] or 0) * 1000,
                            "Émissions totales de CO2",
                            "g",
                            "{:.3f}",
                        ),
                    },
                )
        except Exception as e:
            logger.error(f"Erreur lors du calcul des stats LLM: {e}")

        return StatsSection(
            "LLM",
            {
                "attempted": StatItem(0, "Extractions tentées"),
                "successful_json": StatItem(0, "Extractions JSON réussies"),
                "successful_osm": StatItem(0, "Extractions OSM réussies"),
                "failed": StatItem(0, "Extractions échouées"),
                "success_rate": StatItem(0, "Taux de réussite", "%", "{:.1f}"),
                "avg_schedule_length": StatItem(
                    0, "Taille moyenne des horaires", " caractères"
                ),
                "total_co2_emissions": StatItem(
                    0, "Émissions totales de CO2", "g", "{:.3f}"
                ),
            },
        )

    def _get_comparison_stats(self) -> StatsSection:
        """Calcule et retourne les statistiques sur la comparaison des horaires.

        Returns:
            StatsSection: Un objet StatsSection contenant les statistiques suivantes :
                          - Le nombre total de comparaisons.
                          - Le nombre d'horaires identiques ou différents.
                          - Le nombre de cas non comparés.
                          - Le taux de précision global.
        """
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
                accuracy_rate = (identical / total * 100) if total > 0 else 0

                return StatsSection(
                    "Comparaisons",
                    {
                        "total": StatItem(total, "Total des comparaisons"),
                        "identical": StatItem(identical, "Horaires identiques"),
                        "different": StatItem(different, "Horaires différents"),
                        "not_compared": StatItem(not_compared, "Non comparés"),
                        "accuracy_rate": StatItem(
                            accuracy_rate, "Taux de précision", "%", "{:.1f}"
                        ),
                    },
                )
        except Exception as e:
            logger.error(f"Erreur lors du calcul des stats de comparaison: {e}")

        return StatsSection(
            "Comparaisons",
            {
                "total": StatItem(0, "Total des comparaisons"),
                "identical": StatItem(0, "Horaires identiques"),
                "different": StatItem(0, "Horaires différents"),
                "not_compared": StatItem(0, "Non comparés"),
                "accuracy_rate": StatItem(0, "Taux de précision", "%", "{:.1f}"),
            },
        )

    def _get_global_stats(self) -> StatsSection:
        """Calcule et retourne les statistiques globales sur l'ensemble de l'exécution.

        Returns:
            StatsSection: Un objet StatsSection contenant les informations récapitulatives suivantes :
                          - L'ID d'exécution.
                          - Le nombre total d'enregistrements.
                          - Le nombre d'enregistrements avec erreurs.
                          - La date d'exécution.
                          - Le modèle et le fournisseur LLM utilisés.
                          - Les émissions totales de CO2 pour l'ensemble du processus.
        """
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

            items = {
                "execution_id": StatItem("global", "ID d'exécution"),
                "total_records": StatItem(0, "Total des enregistrements"),
                "records_with_errors": StatItem(0, "Enregistrements avec erreurs"),
                "execution_date": StatItem("N/A", "Date d'exécution"),
                "llm_model": StatItem("N/A", "Modèle LLM"),
                "llm_provider": StatItem("N/A", "Fournisseur LLM"),
                "total_co2_emissions": StatItem(
                    0, "Émissions totales de CO2", "g", "{:.3f}"
                ),
            }

            if exec_result and len(exec_result) > 0:
                exec_row = exec_result[0]
                items.update(
                    {
                        "execution_date": StatItem(
                            exec_row[0] or "N/A", "Date d'exécution"
                        ),
                        "llm_model": StatItem(exec_row[1] or "N/A", "Modèle LLM"),
                        "llm_provider": StatItem(
                            exec_row[2] or "N/A", "Fournisseur LLM"
                        ),
                        "total_co2_emissions": StatItem(
                            (exec_row[3] or 0) * 1000,
                            "Émissions totales de CO2",
                            "g",
                            "{:.3f}",
                        ),
                    }
                )

            if results_result and len(results_result) > 0:
                results_row = results_result[0]
                items.update(
                    {
                        "total_records": StatItem(
                            results_row[0] or 0, "Total des enregistrements"
                        ),
                        "records_with_errors": StatItem(
                            results_row[1] or 0, "Enregistrements avec erreurs"
                        ),
                    }
                )

            return StatsSection("Global", items)

        except Exception as e:
            logger.error(f"Erreur lors du calcul des stats globales: {e}")
            return StatsSection(
                "Global",
                {
                    "execution_id": StatItem("global", "ID d'exécution"),
                    "total_records": StatItem(0, "Total des enregistrements"),
                    "records_with_errors": StatItem(0, "Enregistrements avec erreurs"),
                    "execution_date": StatItem("N/A", "Date d'exécution"),
                    "llm_model": StatItem("N/A", "Modèle LLM"),
                    "llm_provider": StatItem("N/A", "Fournisseur LLM"),
                    "total_co2_emissions": StatItem(
                        0, "Émissions totales de CO2", "g", "{:.3f}"
                    ),
                },
            )

    def display_stats(self):
        """Affiche les statistiques de manière formatée en itérant sur les sections."""
        stats = self.get_pipeline_stats()

        logger.info("=== STATISTIQUES DU PIPELINE ===")

        # Affichage de l'en-tête
        header = stats["header"]
        logger.info(f"Exécution: {header.get_formatted_value('execution_id')}")
        logger.info(f"Timestamp: {header.get_formatted_value('timestamp')}")

        # Affichage des autres sections
        for section_key, section in stats.items():
            if section_key == "header":
                continue

            logger.info(f"--- {section.title} ---")
            for item_key, item in section.items.items():
                logger.info(f"{item.label}: {item.formatted_value()}")

        logger.info("=== FIN STATISTIQUES ===")

    def generate_custom_text(self, template: str) -> str:
        """
        Génère un texte personnalisé en remplaçant les variables dans le template.
        Args:
            template (str): le template avec des variables au format {section.item}.

        Returns:
            str: le texte généré avec les variables remplacées par les valeurs des statistiques.
        """
        stats = self.get_pipeline_stats()

        # Dictionnaire pour les remplacements
        replacements = {}

        for section_key, section in stats.items():
            for item_key, item in section.items.items():
                # Clé au format section.item
                key = f"{section_key}.{item_key}"
                replacements[key] = item.formatted_value()

                # Clé au format section.item_value pour avoir juste la valeur
                key_value = f"{section_key}.{item_key}_value"
                replacements[key_value] = str(item.value)

        # Remplacements dans le template
        try:
            return template.format(**replacements)
        except KeyError as e:
            logger.error(f"Variable manquante dans le template: {e}")
            return template

    def get_stats_for_api(self) -> Dict[str, Any]:
        """
        Retourne les statistiques dans un format adapté pour une API.

        Returns:
            Dict[str, Any]: dictionnaire des statistiques avec les sections et leurs éléments.
        """
        stats = self.get_pipeline_stats()

        result = {}
        for section_key, section in stats.items():
            result[section_key] = {"title": section.title, "items": {}}

            for item_key, item in section.items.items():
                result[section_key]["items"][item_key] = {
                    "label": item.label,
                    "value": item.value,
                    "formatted_value": item.formatted_value(),
                    "unit": item.unit,
                }

        return result
