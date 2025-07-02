"""
Système de logging pour le projet smart_watch
Support flexible pour fichier et/ou console
"""

import logging
import os
import sys
from enum import Enum
from pathlib import Path
from typing import List

from dotenv import load_dotenv


class LogLevel(Enum):
    """Niveaux de log disponibles"""

    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class LogOutput(Enum):
    """Types de sortie de log disponibles"""

    FILE = "file"
    CONSOLE = "console"


class SmartWatchLogger:
    """
    Logger avec outputs configurables (fichier et/ou console)
    """

    def __init__(
        self,
        module_name: str = "main",
        outputs: List[LogOutput] = None,
    ):
        """
        Initialise le logger

        Args:
            module_name: Nom du module utilisant le logger
            outputs: Liste des sorties désirées. Défaut: [FILE, CONSOLE]
        """
        load_dotenv()
        self.module_name = module_name
        self.outputs = (
            outputs if outputs is not None else [LogOutput.FILE, LogOutput.CONSOLE]
        )
        self.log_file = Path(__file__).resolve().parents[3] / "logs" / "SmartWatch.log"
        self._setup_logging()

    def _setup_logging(self):
        """Configure le logging selon les outputs demandés"""
        try:
            log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
            log_level = LogLevel[log_level_str].value

            self.logger = logging.getLogger(self.module_name)
            self.logger.setLevel(log_level)

            if self.logger.hasHandlers():
                return

            formatter = logging.Formatter(
                "%(asctime)s - %(levelname)s - %(name)s : %(message)s"
            )

            handler_map = {
                LogOutput.FILE: logging.FileHandler(self.log_file, encoding="utf-8"),
                LogOutput.CONSOLE: logging.StreamHandler(sys.stdout),
            }

            for output_type in self.outputs:
                if output_type in handler_map:
                    handler = handler_map[output_type]
                    handler.setFormatter(formatter)
                    self.logger.addHandler(handler)

            self.available = True
        except Exception as e:
            print(f"Erreur lors de la configuration du logger: {e}")
            self.available = False

    def _log(self, level: LogLevel, message: str):
        """Écrit le log vers fichier et/ou console"""
        if not hasattr(self, "available") or not self.available:
            return
        try:
            self.logger.log(level.value, f"{message}")
        except Exception as e:
            print(f"Erreur lors de l'écriture du log: {e}")

    def log(self, level: LogLevel, message: str):
        """Log avec niveau spécifique"""
        self._log(level, message)

    def debug(self, message: str):
        self._log(LogLevel.DEBUG, message)

    def info(self, message: str):
        self._log(LogLevel.INFO, message)

    def warning(self, message: str):
        self._log(LogLevel.WARNING, message)

    def error(self, message: str):
        self._log(LogLevel.ERROR, message)

    def critical(self, message: str):
        self._log(LogLevel.CRITICAL, message)

    def section(self, title: str, level: LogLevel = LogLevel.INFO):
        """Log une section avec formatage spécial"""
        separator = "=" * len(title) + "=" * 4
        self._log(level, "")
        self._log(level, separator)
        self._log(level, f"  {title}  ")
        self._log(level, separator)
        self._log(level, "")


def create_logger(
    module_name: str = "main",
    outputs: List[str] = None,
) -> SmartWatchLogger:
    """
    Factory function pour créer un logger configuré avec outputs flexibles

    Args:
        module_name: Nom du module
        outputs: Liste des sorties ["file", "console"]. Défaut: ["file", "console"]

    Returns:
        Instance configurée de SmartWatchLogger
    """
    output_map = {"file": LogOutput.FILE, "console": LogOutput.CONSOLE}

    if outputs is None:
        log_outputs = list(output_map.values())
    else:
        log_outputs = [output_map[out] for out in outputs if out in output_map]
        if len(log_outputs) != len(outputs or []):
            print("Warning: Certains outputs non reconnus ont été ignorés.")

    return SmartWatchLogger(module_name=module_name, outputs=log_outputs)
