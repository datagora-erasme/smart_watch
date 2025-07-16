# SmartWatch est un programme permettant l'extraction d'horaires d'ouverture par LLM depuis des sites web,
# et leur comparaison avec des données de référence issues de data.grandlyon.com.
#
# Chaque module de ce projet est commenté dans la documentation officielle,
# accessible par un lien indiqué au début de chaque fichier :
#
# https://datagora-erasme.github.io/smart_watch/index.html

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
    DatabaseProcessor,
    LLMProcessor,
    URLProcessor,
)
from src.smart_watch.processing.setup_processor import SetupProcessor
from src.smart_watch.reporting import ReportManager
from src.smart_watch.stats import StatsManager
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
        self.db_manager = DatabaseProcessor(self.config, self.logger)
        self.setup_processor = SetupProcessor(self.config, self.logger)
        self.url_processor = URLProcessor(self.config, self.logger)
        self.markdown_cleaner = MarkdownCleaner(self.config, self.logger)
        self.markdown_processor = MarkdownProcessor(self.config, self.logger)
        self.llm_processor = LLMProcessor(self.config, self.logger)
        self.comparison_processor = ComparisonProcessor(self.config, self.logger)
        self.report_manager = ReportManager(self.config, self.logger)
        self.stats_manager = StatsManager(self.config, self.logger)

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
            # 1. Création de la base de données
            self.db_manager.create_database()

            # 2. Configuration et chargement des données
            execution_id = self.setup_processor.setup_execution(self.db_manager)

            # 3. Pipeline de traitement séquentiel
            # a. Extraction des URLs
            self.url_processor.process_urls(self.db_manager, execution_id)

            # b. Nettoyage du contenu Markdown
            self.markdown_cleaner.process_markdown_cleaning(
                self.db_manager, execution_id
            )

            # c. Filtrage sémantique du Markdown
            self.markdown_processor.process_markdown_filtering(
                self.db_manager, execution_id
            )

            # d. Extraction des horaires via LLM
            self.llm_processor.process_llm_extractions(self.db_manager, execution_id)

            # e. Comparaison des horaires extraits
            self.comparison_processor.process_comparisons(self.db_manager)

            # 5. Génération et envoi du rapport
            self.report_manager.generate_and_send_report(execution_id)

            # 6. Affichage des statistiques finales
            self.stats_manager.display_stats()

            # 7. Résumé final
            processing_time = time.time() - start_time
            self.logger.info(f"Pipeline terminé en {processing_time:.2f}s")

            self.logger.section("FIN PIPELINE EXTRACTION HORAIRES")

        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"Pipeline échoué après {processing_time:.2f}s: {e}")
            raise


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
