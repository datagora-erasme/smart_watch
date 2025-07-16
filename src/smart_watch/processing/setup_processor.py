from src.smart_watch.core.ErrorHandler import (
    ErrorCategory,
    ErrorSeverity,
    handle_errors,
)
from src.smart_watch.utils.CSVToPolars import CSVToPolars


class SetupProcessor:
    """Gestionnaire de l'initialisation (chargement CSV et DB)."""

    def __init__(self, config, logger):
        """
        Initialise le processeur avec la configuration et le logger spécifiés.

        Args:
            config (Config): Objet de configuration contenant les paramètres nécessaires, y compris la base de données.
            logger (Logger): Instance du logger pour la journalisation des événements.
        """
        self.config = config
        self.logger = logger

    @handle_errors(
        category=ErrorCategory.CONFIGURATION,
        severity=ErrorSeverity.HIGH,
        user_message="Erreur lors de la configuration du pipeline",
        reraise=True,
    )
    def setup_execution(self, db_manager):
        """
        Initialise la pipeline de configuration en chargeant le CSV depuis la configuration
        et en initialisant la base de données avec les données chargées.

        Étapes :
            - Charge le fichier CSV spécifié dans la configuration.
            - Vérifie le succès du chargement du CSV.
            - Initialise la base de données avec le DataFrame obtenu.

        Raises:
            ValueError: Si le chargement du CSV échoue.
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
        return db_manager.setup_execution(df_csv)
