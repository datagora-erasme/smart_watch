from src.smart_watch.core.DatabaseManager import DatabaseManager
from src.smart_watch.core.ErrorHandler import (
    ErrorCategory,
    ErrorSeverity,
    handle_errors,
)
from src.smart_watch.utils.CSVToPolars import CSVToPolars


class SetupProcessor:
    """Gestionnaire de l'initialisation (chargement CSV et DB)."""

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        # Instancie DatabaseManager à partir de la config
        self.db_manager = DatabaseManager(
            db_file=self.config.database.db_file,
            table_name="resultats_extraction",
        )

    @handle_errors(
        category=ErrorCategory.CONFIGURATION,
        severity=ErrorSeverity.HIGH,
        user_message="Erreur lors de la configuration du pipeline",
        reraise=True,
    )
    def setup_execution(self) -> int:
        """
        Charge le CSV depuis la config et initialise la base de données.

        Returns:
            int: Code de retour de l'initialisation de la base de données.
        """
        self.logger.section("CONFIGURATION PIPELINE")
        csv_loader = CSVToPolars(
            source=self.config.database.csv_url,
            separator="auto",
            has_header=True,
        )

        df_csv = csv_loader.load_csv()

        if isinstance(df_csv, str):
            raise ValueError(f"Erreur chargement CSV: {df_csv}")

        # Initialise la base avec DatabaseManager et le DataFrame chargé
        self.db_manager.initialize(df_csv, if_exists="replace")
