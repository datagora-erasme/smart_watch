# SmartWatch est un programme permettant l'extraction d'horaires d'ouverture par LLM depuis des sites web,
# et leur comparaison avec des données de référence issues de data.grandlyon.com.
#
# Chaque module de ce projet est documenté sur sa page,
# accessible par un lien indiqué au début de chaque fichier source :
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
from src.smart_watch.core.StatsManager import StatsManager
from src.smart_watch.processing import (
    ComparisonProcessor,
    DatabaseProcessor,
    LLMProcessor,
    MarkdownProcessor,
    SetupProcessor,
    URLProcessor,
)
from src.smart_watch.reporting import ReportManager
from src.smart_watch.utils import MarkdownCleaner


class HoraireExtractor:
    """Classe principale pour l'extraction et le traitement d'horaires."""

    def __init__(self):
        """Initialise l'extracteur"""
        # A. Charger de la configuration
        self.config = ConfigManager()

        # Vérification de la configuration
        if not self.config.validate():
            raise ValueError("Configuration invalide")

        # Initialisation du logger
        self.logger = create_logger(module_name="Main")

        # Affichage de la configuration
        self.config.display_summary()

        # B. Instancier les processeurs principaux avec la configuration
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

    # C. Exécuter le pipeline
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

            # 2. Chargement des données, préparation de l'exécution
            execution_id = self.setup_processor.setup_execution(self.db_manager)

            # Traitement
            # 3. Extraction des URLs
            self.url_processor.process_urls(self.db_manager, execution_id)

            # 4. Nettoyage du contenu Markdown brut
            self.markdown_cleaner.process_markdown_cleaning(
                self.db_manager, execution_id
            )

            # 5. Filtrage sémantique du Markdown (par embeddings)
            self.markdown_processor.process_markdown_filtering(
                self.db_manager, execution_id
            )

            # 6. Extraction des horaires via LLM
            self.llm_processor.process_llm_extractions(self.db_manager, execution_id)

            # 7. Comparaison des horaires extraits
            self.comparison_processor.process_comparisons(self.db_manager)

            # 8. Génération et envoi du rapport
            self.report_manager.generate_and_send_report(execution_id)

            # Log interne au programme : Affichage des statistiques
            self.stats_manager.display_stats()

            # Log interne au programme : Résumé final
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

    # C. Exécuter le pipeline
    extractor.run()


if __name__ == "__main__":
    main()
