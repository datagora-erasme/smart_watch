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
import time

from src.smart_watch.core.ConfigManager import ConfigManager
from src.smart_watch.core.ErrorHandler import (
    ErrorCategory,
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
from src.smart_watch.reporting import ReportManager
from src.smart_watch.stats import PipelineStats  # Import unifié
from src.smart_watch.utils.CSVToPolars import CSVToPolars
from src.smart_watch.utils.MarkdownCleaner import MarkdownCleaner


class HoraireExtractor:
    """Classe principale pour l'extraction et le traitement d'horaires."""

    def __init__(self):
        """Initialise l'extracteur"""
        self.config = ConfigManager()

        if not self.config.validate():
            raise ValueError("Configuration invalide")

        # Initialisation du logger
        self.logger = create_logger(module_name="Main")

        # Affichage de la configuration
        self.config.display_summary()

        # Initialisation des composants modulaires
        self.db_manager = DatabaseManager(self.config, self.logger)
        self.url_processor = URLProcessor(self.config, self.logger)
        self.markdown_cleaner = MarkdownCleaner(self.config, self.logger)
        self.markdown_processor = MarkdownProcessor(self.config, self.logger)
        self.llm_processor = LLMProcessor(self.config, self.logger)
        self.comparison_processor = ComparisonProcessor(self.config, self.logger)
        self.report_manager = ReportManager(self.config, self.logger)

        # Statistiques globales unifiées
        self.stats = PipelineStats()

        self.logger.info("HoraireExtractor initialisé")

    @handle_errors(
        category=ErrorCategory.CONFIGURATION,
        severity=ErrorSeverity.HIGH,
        user_message="Erreur lors de l'exécution du pipeline",
    )
    def run(self):
        """Exécute le pipeline d'extraction complet"""
        self.logger.section("DÉBUT PIPELINE EXTRACTION HORAIRES")

        start_time = time.time()

        try:
            # 1. Configuration et chargement des données
            execution_id = self._setup_execution()

            # 2. Pipeline de traitement séquentiel
            # a. Extraction des URLs
            self.stats.url_stats = self.url_processor.process_urls(
                self.db_manager, execution_id
            )

            # b. Nettoyage du contenu Markdown
            markdown_cleaning_stats = self.markdown_cleaner.process_markdown_cleaning(
                self.db_manager, execution_id
            )

            # c. Filtrage sémantique du Markdown
            markdown_filtering_stats = (
                self.markdown_processor.process_markdown_filtering(
                    self.db_manager, execution_id
                )
            )

            # Fusionner les statistiques markdown
            self.stats.markdown_stats = markdown_cleaning_stats
            self.stats.markdown_stats.merge(markdown_filtering_stats)

            # d. Extraction des horaires via LLM
            self.stats.llm_stats = self.llm_processor.process_llm_extractions(
                self.db_manager, execution_id
            )

            # e. Comparaison des horaires extraits
            self.stats.comparison_stats = self.comparison_processor.process_comparisons(
                self.db_manager
            )

            # 3. Finalisation des statistiques
            self.stats.total_processing_time = time.time() - start_time
            self.stats.update_co2_emissions()
            self.stats.pipeline_success = True

            # 4. Génération et envoi du rapport
            self.report_manager.generate_and_send_report(self.stats)

            # 5. Résumé final
            self._display_final_summary()

            self.logger.section("FIN PIPELINE EXTRACTION HORAIRES")

        except Exception as e:
            self.stats.pipeline_success = False
            self.stats.total_processing_time = time.time() - start_time
            self.logger.error(f"Erreur pipeline: {e}")
            raise

    def _setup_execution(self) -> int:
        """Configure l'exécution et retourne l'ID."""
        self.logger.section("CONFIGURATION PIPELINE")

        # Chargement du CSV depuis l'URL
        csv_loader = CSVToPolars(
            source=self.config.database.csv_url,
            separator="auto",
            has_header=True,
        )
        df_csv = csv_loader.load_csv()

        if isinstance(df_csv, str):
            raise ValueError(f"Erreur chargement CSV: {df_csv}")

        return self.db_manager.setup_execution(df_csv)

    def _display_final_summary(self):
        """Affiche le résumé final des statistiques."""
        self.logger.section("RÉSUMÉ FINAL")

        summary = self.stats.get_summary_for_report()
        for key, value in summary.items():
            self.logger.info(f"{key}: {value}")

        # Affichage du résumé des erreurs
        error_summary = self.config.error_handler.get_error_summary()
        if error_summary["total_errors"] > 0:
            self.logger.info(f"Total erreurs: {error_summary['total_errors']}")
        else:
            self.logger.info("Aucune erreur détectée")


@handle_errors(
    category=ErrorCategory.UNKNOWN,
    severity=ErrorSeverity.CRITICAL,
    user_message="Erreur dans le programme principal",
    reraise=True,
)
def main():
    """Point d'entrée principal."""
    extractor = HoraireExtractor()
    extractor.run()


if __name__ == "__main__":
    main()
