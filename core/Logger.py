"""
Système de logging configurable pour le projet smart_watch
Permet d'écrire vers la console et/ou un fichier
"""

import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class LogLevel(Enum):
    """Niveaux de log disponibles"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogOutput(Enum):
    """Types de sortie pour les logs"""

    CONSOLE = "console"
    FILE = "file"


class SmartWatchLogger:
    """
    Logger configurable pour le projet smart_watch
    """

    def __init__(
        self,
        outputs: list[LogOutput] = None,
        log_file: Optional[Path] = None,
        module_name: str = "main",
    ):
        """
        Initialise le logger

        Args:
            outputs: Liste des sorties (console, file). Par défaut: [CONSOLE]
            log_file: Chemin vers le fichier de log
            module_name: Nom du module utilisant le logger
        """
        self.outputs = outputs or [LogOutput.CONSOLE]
        self.log_file = log_file
        self.module_name = module_name

        # Configuration du logging fichier si nécessaire
        if LogOutput.FILE in self.outputs and log_file:
            self._setup_file_logging()

    def _setup_file_logging(self):
        """Configure le logging vers fichier"""
        try:
            # Créer le répertoire si nécessaire
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

            # Configuration du logger fichier avec nom simplifié
            self.file_logger = logging.getLogger(self.module_name)
            self.file_logger.setLevel(logging.DEBUG)

            # Éviter les doublons de handlers
            if not self.file_logger.handlers:
                handler = logging.FileHandler(self.log_file, encoding="utf-8")
                formatter = logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
                handler.setFormatter(formatter)
                self.file_logger.addHandler(handler)

            self.file_available = True
        except Exception as e:
            print(f"Erreur lors de la configuration du fichier de log: {e}")
            self.file_available = False

    def _log_to_console(self, level: LogLevel, message: str):
        """Écrit le log vers la console"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = (
            f"[{timestamp}] {level.value} - {self.module_name}: {message}"
        )
        print(formatted_message)

    def _log_to_file(self, level: LogLevel, message: str):
        """Écrit le log vers le fichier"""
        if not hasattr(self, "file_available") or not self.file_available:
            return

        try:
            # Mapper les niveaux personnalisés vers les niveaux logging standard
            level_mapping = {
                LogLevel.DEBUG: logging.DEBUG,
                LogLevel.INFO: logging.INFO,
                LogLevel.WARNING: logging.WARNING,
                LogLevel.ERROR: logging.ERROR,
                LogLevel.CRITICAL: logging.CRITICAL,
            }

            log_level = level_mapping.get(level, logging.INFO)
            self.file_logger.log(log_level, message)
        except Exception as e:
            print(f"Erreur lors de l'écriture dans le fichier de log: {e}")

    def log(self, level: LogLevel, message: str):
        """
        Écrit un message de log selon la configuration

        Args:
            level: Niveau du log
            message: Message à logger
        """
        for output in self.outputs:
            if output == LogOutput.CONSOLE:
                self._log_to_console(level, message)
            elif output == LogOutput.FILE:
                self._log_to_file(level, message)

    def debug(self, message: str):
        """Log de niveau DEBUG"""
        self.log(LogLevel.DEBUG, message)

    def info(self, message: str):
        """Log de niveau INFO"""
        self.log(LogLevel.INFO, message)

    def warning(self, message: str):
        """Log de niveau WARNING"""
        self.log(LogLevel.WARNING, message)

    def error(self, message: str):
        """Log de niveau ERROR"""
        self.log(LogLevel.ERROR, message)

    def critical(self, message: str):
        """Log de niveau CRITICAL"""
        self.log(LogLevel.CRITICAL, message)

    def section(self, title: str, level: LogLevel = LogLevel.INFO):
        """Log une section avec formatage spécial"""
        separator = "=" * len(title)
        full_message = f"{separator}\n{title}\n{separator}"
        self.log(level, full_message)


def create_logger(
    outputs: list[LogOutput] = None,
    log_file: Optional[Path] = None,
    module_name: str = "main",
) -> SmartWatchLogger:
    """
    Factory function pour créer un logger configuré avec nom de fichier basé sur CSV_URL_HORAIRES

    Returns:
        Instance configurée de SmartWatchLogger
    """
    # Si aucun fichier de log spécifié, utiliser CSV_URL_HORAIRES depuis .env
    if log_file is None:
        import os

        from dotenv import load_dotenv

        load_dotenv()
        csv_name = os.getenv("CSV_URL_HORAIRES")

        # Construire le chemin du fichier de log
        from pathlib import Path

        project_root = Path(__file__).parent.parent
        log_file = project_root / "logs" / f"{csv_name}.log"

    return SmartWatchLogger(
        outputs=outputs,
        log_file=log_file,
        module_name=module_name,
    )
