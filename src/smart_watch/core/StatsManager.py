# Gestionnaire de statistiques pour le projet smart_watch
# Documentation: https://datagora-erasme.github.io/smart_watch/source/modules/core/StatsManager.html

from datetime import datetime
from typing import Any, Dict

from .ConfigManager import ConfigManager
from .DatabaseManager import DatabaseManager
from .Logger import SmartWatchLogger, create_logger

logger = create_logger("StatsManager")


class StatItem:
    """Représente un élément de statistique avec sa valeur, son libellé et son unité."""

    def __init__(
        self,
        value: Any,
        label: str,
        unit: str = "",
        format_str: str = "{}",
    ) -> None:
        """
        Initialise un élément de statistique.

        Args:
            value (Any): La valeur de la statistique.
            label (str): Le libellé descriptif de la statistique.
            unit (str, optionnel): L'unité de mesure de la statistique. Par défaut "".
            format_str (str, optionnel): La chaîne de formatage pour la valeur. Par défaut "{}".

        Attributes:
            value (Any): La valeur brute de la statistique.
            label (str): Le libellé de la statistique.
            unit (str): L'unité de la statistique.
            format_str (str): La chaîne de formatage pour l'affichage.
        """
        self.value = value
        self.label = label
        self.unit = unit
        self.format_str = format_str

    def formatted_value(self) -> str:
        """
        Retourne la valeur de la statistique formatée pour l'affichage.

        La valeur est formatée en utilisant `format_str` et l'unité est ajoutée si elle est définie.
        Si la valeur est `None`, la méthode retourne "N/A".

        Returns:
            str: La valeur formatée, incluant l'unité si disponible.
        """
        if self.value is None:
            return "N/A"
        formatted = self.format_str.format(self.value)
        return f"{formatted} {self.unit}" if self.unit else formatted

    def __str__(self) -> str:
        """
        Retourne une représentation textuelle de l'élément de statistique.

        Le format est "Libellé: Valeur formatée".

        Returns:
            str: La représentation de l'élément sous forme de chaîne de caractères.
        """
        return f"{self.label}: {self.formatted_value()}"


class StatsSection:
    """Représente une section de statistiques."""

    def __init__(self, title: str, items: Dict[str, StatItem]) -> None:
        """
        Initialise une section de statistiques, qui regroupe plusieurs `StatItem`.

        Args:
            title (str): Le titre de la section (ex: "URLs", "LLM").
            items (Dict[str, StatItem]): Un dictionnaire d'éléments de statistique.

        Attributes:
            title (str): Le titre de la section.
            items (Dict[str, StatItem]): Les éléments de statistique de la section.
        """
        self.title = title
        self.items = items

    def get_item_value(self, key: str) -> Any:
        """
        Récupère la valeur brute d'un élément de statistique par sa clé.

        Args:
            key (str): La clé de l'élément de statistique à récupérer.

        Returns:
            Any: La valeur brute de l'élément, ou "N/A" si la clé n'existe pas.
        """
        return self.items.get(key, StatItem("N/A", "")).value

    def get_formatted_value(self, key: str) -> str:
        """
        Récupère la valeur formatée d'un élément de statistique par sa clé.

        Args:
            key (str): La clé de l'élément de statistique à récupérer.

        Returns:
            str: La valeur formatée de l'élément, ou "N/A" si la clé n'existe pas.
        """
        return self.items.get(key, StatItem("N/A", "")).formatted_value()


class StatsManager:
    """Gestionnaire de statistiques basé sur les requêtes SQL."""

    def __init__(self, config: ConfigManager, logger: SmartWatchLogger) -> None:
        """
        Initialise le gestionnaire de statistiques.

        Args:
            config (ConfigManager): L'instance du gestionnaire de configuration.
            logger (SmartWatchLogger): L'instance du logger pour l'enregistrement des messages.

        Attributes:
            config (ConfigManager): Le gestionnaire de configuration.
            logger (SmartWatchLogger): Le logger.
            db_manager (DatabaseManager): Le gestionnaire de base de données pour exécuter les requêtes.
        """
        self.config = config
        self.logger = logger
        self.db_manager = DatabaseManager(db_file=config.database.db_file)

    def get_pipeline_stats(self) -> Dict[str, StatsSection]:
        """
        Génère un rapport complet des statistiques du pipeline.

        Cette méthode agrège les statistiques de chaque étape du pipeline (URLs, Markdown, LLM, etc.)
        en appelant les méthodes dédiées pour chaque section.

        Returns:
            Dict[str, StatsSection]: Un dictionnaire où chaque clé est le nom d'une section
                                     et la valeur est un objet `StatsSection` contenant les statistiques.
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
        """
        Crée la section de statistiques pour l'en-tête du rapport.

        Cette section contient des informations générales sur l'exécution, comme son ID et l'horodatage.

        Returns:
            StatsSection: Un objet `StatsSection` contenant les statistiques de l'en-tête.
                          Les clés disponibles sont :
                          - `execution_id`
                          - `timestamp`
        """
        return StatsSection(
            "En-tête",
            {
                "execution_id": StatItem("global", "ID d'exécution"),
                "timestamp": StatItem(datetime.now().isoformat(), "Horodatage"),
            },
        )

    def _get_url_stats(self) -> StatsSection:
        """
        Calcule et retourne les statistiques sur le traitement des URLs.

        Interroge la base de données pour obtenir des métriques telles que le nombre total d'URLs,
        les succès, les échecs, le taux de réussite, la taille moyenne du contenu, et les types d'erreurs.

        Returns:
            StatsSection: Un objet `StatsSection` contenant les statistiques des URLs.
                          Les clés disponibles sont :
                          - `total`
                          - `successful`
                          - `failed`
                          - `success_rate`
                          - `avg_content_length`
                          - `http_errors`
                          - `timeout_errors`
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
        """
        Calcule et retourne les statistiques sur le traitement des contenus Markdown.

        Fournit des informations sur le nombre de documents traités, nettoyés et filtrés,
        la taille moyenne après filtrage, et le volume de caractères supprimés.

        Returns:
            StatsSection: Un objet `StatsSection` contenant les statistiques Markdown.
                          Les clés disponibles sont :
                          - `processed`
                          - `cleaned`
                          - `filtered`
                          - `avg_filtered_length`
                          - `chars_cleaned`
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
        """
        Calcule et retourne les statistiques sur les extractions du LLM.

        Analyse les performances du LLM, incluant le nombre d'extractions tentées, réussies (JSON et OSM),
        et échouées, le taux de réussite, la taille moyenne des extractions et les émissions de CO2.

        Returns:
            StatsSection: Un objet `StatsSection` contenant les statistiques du LLM.
                          Les clés disponibles sont :
                          - `attempted`
                          - `successful_json`
                          - `successful_osm`
                          - `failed`
                          - `success_rate`
                          - `avg_schedule_length`
                          - `total_co2_emissions`
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
        """
        Calcule et retourne les statistiques sur la comparaison des horaires.

        Évalue la précision des extractions en comparant les horaires générés avec les données de référence,
        en comptabilisant les correspondances identiques, différentes et les cas non comparés.

        Returns:
            StatsSection: Un objet `StatsSection` contenant les statistiques de comparaison.
                          Les clés disponibles sont :
                          - `total`
                          - `identical`
                          - `different`
                          - `not_compared`
                          - `accuracy_rate`
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
        """
        Calcule et retourne les statistiques globales de l'exécution.

        Récapitule les informations clés de l'ensemble du pipeline, telles que le nombre total
        d'enregistrements, les erreurs, la date, le modèle LLM utilisé et les émissions de CO2.

        Returns:
            StatsSection: Un objet `StatsSection` contenant les statistiques globales.
                          Les clés disponibles sont :
                          - `execution_id`
                          - `total_records`
                          - `records_with_errors`
                          - `execution_date`
                          - `llm_model`
                          - `llm_provider`
                          - `total_co2_emissions`
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

    def display_stats(self) -> None:
        """
        Affiche les statistiques complètes du pipeline dans le logger.

        Cette méthode récupère toutes les sections de statistiques et les affiche de manière
        formatée et lisible dans les logs.
        """
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
        Génère un texte personnalisé à partir d'un template et des statistiques.

        Remplace les placeholders dans la chaîne de template (ex: `{urls.total}`) par les valeurs
        de statistiques correspondantes.

        Args:
            template (str): La chaîne de template contenant des placeholders.

        Returns:
            str: Le texte généré avec les valeurs des statistiques insérées.
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
        Formate les statistiques pour une utilisation via une API.

        Convertit les objets `StatsSection` et `StatItem` en un dictionnaire sérialisable (JSON),
        facilitant ainsi leur exposition via un endpoint d'API.

        Returns:
            Dict[str, Any]: Un dictionnaire contenant toutes les statistiques formatées pour l'API.
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
