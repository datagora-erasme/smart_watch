"""
Système de logging pour le projet smart_watch
Écrit uniquement vers un fichier logs/SmartWatch.log
"""

import logging
from enum import Enum
from pathlib import Path


class LogLevel(Enum):
    """Niveaux de log disponibles"""

    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class SmartWatchLogger:
    """
    Logger simplifié pour le projet smart_watch (log fichier uniquement)
    """

    def __init__(
        self,
        module_name: str = "main",
    ):
        """
        Initialise le logger

        Args:
            module_name: Nom du module utilisant le logger
        """
        self.module_name = module_name
        self.log_file = Path(__file__).parent.parent / "logs" / "SmartWatch.log"
        self._setup_file_logging()

    def _setup_file_logging(self):
        """Configure le logging vers fichier"""
        try:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
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

    def _log_to_file(self, level: LogLevel, message: str):
        """Écrit le log vers le fichier"""
        if not hasattr(self, "file_available") or not self.file_available:
            return
        try:
            self.file_logger.log(level.value, f"{self.module_name}: {message}")
        except Exception as e:
            print(f"Erreur lors de l'écriture dans le fichier de log: {e}")

    def log(self, level: LogLevel, message: str):
        """Log avec niveau spécifique"""
        self._log_to_file(level, message)

    def debug(self, message: str):
        self._log_to_file(LogLevel.DEBUG, message)

    def info(self, message: str):
        self._log_to_file(LogLevel.INFO, message)

    def warning(self, message: str):
        self._log_to_file(LogLevel.WARNING, message)

    def error(self, message: str):
        self._log_to_file(LogLevel.ERROR, message)

    def critical(self, message: str):
        self._log_to_file(LogLevel.CRITICAL, message)

    def section(self, title: str, level: LogLevel = LogLevel.INFO):
        """Log une section avec formatage spécial"""
        separator = "=" * len(title)
        full_message = f"{separator}\n{title}\n{separator}"
        self._log_to_file(level, full_message)


def create_logger(
    module_name: str = "main",
) -> SmartWatchLogger:
    """
    Factory function pour créer un logger configuré (log fichier uniquement)
    Returns:
        Instance configurée de SmartWatchLogger
    """
    return SmartWatchLogger(module_name=module_name)
