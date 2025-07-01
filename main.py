"""
SmartWatch est un programme permettant l'extraction d'horaires d'ouverture
par LLM depuis des sites web, et leur comparaison avec des données de référence.

Les données de référence sont issues de data.grandlyon.com.

Les variables d'environnement sont chargées depuis un fichier .env.

Les modules principaux sont :
    - ConfigManager : Gestion de la configuration et des variables d'environnement
    - ErrorHandler : Gestion des erreurs et des logs
    - Logger : Gestion des logs
    - MarkdownProcessor : Traitement des fichiers Markdown
    - URLProcessor : Traitement des URLs et extraction de données
    - LLMProcessor : Interaction avec les modèles de langage pour l'extraction d'horaires
    - ComparisonProcessor : Comparaison des horaires extraits avec les données de référence
    - DatabaseManager : Gestion de la base de données SQLite
    - ReportManager : Génération et envoi de rapports
    - HoraireExtractor : Classe principale orchestrant l'extraction et le traitement des horaires
"""

# Modules du projet
from src.smart_watch.core.ConfigManager import ConfigManager
from src.smart_watch.core.ErrorHandler import (
    ErrorCategory,
    ErrorHandler,
    ErrorSeverity,
    handle_errors,
)
from src.smart_watch.core.Logger import create_logger
from src.smart_watch.core.MarkdownProcessor import MarkdownProcessor
from src.smart_watch.processing import (
    ComparisonProcessor,
    DatabaseManager,
    LLMProcessor,
    URLProcessor,
)
from src.smart_watch.processing.url_processor import ProcessingStats
from src.smart_watch.reporting import ReportManager
from src.smart_watch.utils.CSVToPolars import CSVToPolars


class HoraireExtractor:
    """Classe principale pour l'extraction et le traitement d'horaires."""

    def __init__(self):
        """Initialise l'extracteur"""
        self.config = ConfigManager()

        if not self.config.validate():
            raise ValueError("Configuration invalide")

        # Initialisation du logger
        self.logger = create_logger(
            module_name="Main",
        )

        # Affichage de la configuration
        self.config.display_summary()

        # Initialisation des composants modulaires
        self.db_manager = DatabaseManager(self.config, self.logger)
        self.url_processor = URLProcessor(self.config, self.logger)
        self.markdown_processor = MarkdownProcessor(self.config, self.logger)
        self.llm_processor = LLMProcessor(self.config, self.logger)
        self.comparison_processor = ComparisonProcessor(self.config, self.logger)
        self.report_manager = ReportManager(self.config, self.logger)

        # Statistiques globales
        self.stats = ProcessingStats()

        self.logger.info("HoraireExtractor initialisé")

    @handle_errors(
        category=ErrorCategory.CONFIGURATION,
        severity=ErrorSeverity.HIGH,
        user_message="Erreur lors de l'exécution du pipeline",
    )
    def run(self):
        """Exécute le pipeline d'extraction complet"""
        self.logger.section("DÉBUT PIPELINE EXTRACTION HORAIRES")

        try:
            # 1. Configuration et chargement des données
            execution_id = self._setup_execution()

            # 2. Pipeline de traitement
            # a. Extraction des URLs
            url_stats = self.url_processor.process_urls(self.db_manager, execution_id)
            # b. Traitement des fichiers Markdown
            markdown_stats = self.markdown_processor.process_markdown_filtering(
                self.db_manager, execution_id
            )
            # c. Extraction des horaires via LLM
            llm_stats = self.llm_processor.process_llm_extractions(
                self.db_manager, execution_id
            )
            # d. Comparaison des horaires extraits avec les données de référence
            comp_stats = self.comparison_processor.process_comparisons(self.db_manager)

            # 3. Consolidation des statistiques
            self._consolidate_stats(url_stats, markdown_stats, llm_stats, comp_stats)

            # 4. Génération et envoi du rapport
            self.report_manager.generate_and_send_report(self.stats)

            # 5. Résumé final
            self._display_final_summary()

            self.logger.section("FIN PIPELINE EXTRACTION HORAIRES : SUCCÈS")

        except Exception as e:
            self.logger.error(f"Erreur pipeline: {e}")
            raise

    def _setup_execution(self) -> int:
        """Configure l'exécution et retourne l'ID."""
        self.logger.section("CONFIGURATION PIPELINE")

        # Chargement du CSV depuis l'URL
        csv_loader = CSVToPolars(
            source=self.config.database.csv_url,
            separator=";",
            has_header=True,
        )
        df_csv = csv_loader.load_csv()

        if isinstance(df_csv, str):
            raise ValueError(f"Erreur chargement CSV: {df_csv}")

        return self.db_manager.setup_execution(df_csv)

    def _consolidate_stats(
        self,
        url_stats: ProcessingStats,
        markdown_stats: ProcessingStats,
        llm_stats: ProcessingStats,
        comp_stats: ProcessingStats,
    ):
        """Consolide les statistiques de tous les processeurs."""
        self.stats.urls_processed = url_stats.urls_processed
        self.stats.urls_successful = url_stats.urls_successful
        self.stats.llm_processed = llm_stats.llm_processed
        self.stats.llm_successful = llm_stats.llm_successful
        self.stats.comparisons_processed = comp_stats.comparisons_processed
        self.stats.comparisons_successful = comp_stats.comparisons_successful

    def _display_final_summary(self):
        """Affiche le résumé final des statistiques."""
        self.logger.section("RÉSUMÉ FINAL")

        summary = self.stats.get_summary()
        for key, value in summary.items():
            self.logger.info(f"{key}: {value}")

        # Affichage du résumé des erreurs
        error_summary = self.config.error_handler.get_error_summary()
        if error_summary["total_errors"] > 0:
            self.logger.info(f"Total erreurs: {error_summary['total_errors']}")
        else:
            self.logger.info("Aucune erreur détectée")


def main():
    """Point d'entrée principal avec gestion d'erreurs globale."""
    try:
        extractor = HoraireExtractor()
        extractor.run()
    except Exception as e:
        error_handler = ErrorHandler()
        context = error_handler.create_error_context(
            module="main",
            function="main",
            operation="Exécution du programme principal",
            user_message="Erreur fatale dans le programme principal",
        )

        error_handler.handle_error(
            exception=e,
            context=context,
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.CRITICAL,
        )

        print(f"Erreur fatale: {e}")
        print("Consultez les logs pour plus de détails")
        raise


if __name__ == "__main__":
    main()
