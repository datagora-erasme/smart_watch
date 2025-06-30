"""
Programme principal optimisé pour l'extraction d'horaires d'ouverture.
Architecture modulaire et workflow pipeline optimisé.
"""

# Modules du projet
from core.ConfigManager import ConfigManager
from core.ErrorHandler import ErrorCategory, ErrorHandler, ErrorSeverity, handle_errors
from core.Logger import create_logger
from core.MarkdownProcessor import MarkdownProcessor

# Import des processeurs depuis le module processing
from processing import ComparisonProcessor, DatabaseManager, LLMProcessor, URLProcessor
from processing.url_processor import ProcessingStats

# Import du gestionnaire de rapports
from reporting import ReportManager
from utils.CSVToPolars import CSVToPolars


class HoraireExtractor:
    """Classe principale pour l'extraction et le traitement d'horaires."""

    def __init__(self):
        """Initialise l'extracteur"""
        self.config = ConfigManager()

        if not self.config.validate():
            raise ValueError("Configuration invalide")

        # Initialisation du logger
        self.logger = create_logger(
            module_name="HoraireExtractor",
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
            url_stats = self.url_processor.process_urls(self.db_manager, execution_id)
            markdown_stats = self.markdown_processor.process_markdown_filtering(
                self.db_manager, execution_id
            )  # Nouvelle étape
            llm_stats = self.llm_processor.process_llm_extractions(
                self.db_manager, execution_id
            )
            comp_stats = self.comparison_processor.process_comparisons(self.db_manager)

            # 3. Consolidation des statistiques
            self._consolidate_stats(url_stats, markdown_stats, llm_stats, comp_stats)

            # 4. Génération et envoi du rapport
            self.report_manager.generate_and_send_report(self.stats)

            # 5. Résumé final
            self._display_final_summary()

            self.logger.section("EXTRACTION TERMINÉE AVEC SUCCÈS")

        except Exception as e:
            self.logger.error(f"Erreur pipeline: {e}")
            raise

    def _setup_execution(self) -> int:
        """Configure l'exécution et retourne l'ID."""
        self.logger.section("CONFIGURATION PIPELINE")

        # Chargement du CSV depuis l'URL
        csv_loader = CSVToPolars(
            source=self.config.database.csv_url,  # Utiliser l'URL au lieu du fichier
            separator=";",
            has_header=True,
            cache_dir=str(self.config.database.csv_file.parent),  # Répertoire de cache
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
        # Gestionnaire d'erreurs de dernier recours
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
