# Système de logging pour le projet smart_watch
# https://datagora-erasme.github.io/smart_watch/source/modules/core/logger.html

import logging
import os
import sys
from enum import Enum
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import List

from dotenv import load_dotenv


class LogLevel(Enum):
    """
    Enumération des niveaux de journalisation pour le module Logger.

    Cette classe définit les différents niveaux de gravité utilisés pour la journalisation
    des messages dans l'application. Chaque niveau correspond à une constante du module
    `logging` de Python.

    Attributes:
        DEBUG (int): Niveau de débogage, utilisé pour les informations détaillées utiles au diagnostic.
        INFO (int): Niveau d'information, utilisé pour les messages informatifs généraux.
        WARNING (int): Niveau d'avertissement, utilisé pour signaler des situations inattendues ou potentiellement problématiques.
        ERROR (int): Niveau d'erreur, utilisé pour les erreurs qui empêchent le fonctionnement normal de l'application.
        CRITICAL (int): Niveau critique, utilisé pour les erreurs graves nécessitant une attention immédiate.
    """

    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class LogOutput(Enum):
    """
    Enumération représentant les types de sortie pour les logs.

    Attributes:
        FILE (LogOutput): Sortie des logs dans un fichier.
        CONSOLE (LogOutput): Sortie des logs dans la console.
    """

    FILE = "file"
    CONSOLE = "console"


class SmartWatchLogger:
    def __init__(
        self,
        module_name: str = "main",
        outputs: List[LogOutput] = None,
    ):
        """
        Initialise une instance du logger pour le module spécifié, avec les sorties désirées.

        Cette méthode configure le système de journalisation pour le module donné,
        en chargeant les variables d'environnement, en définissant les sorties de log
        (fichier et/ou console), et en préparant le fichier de log dans le dossier approprié.

        Args:
            module_name (str, optional): Nom du module à logger. Par défaut "main".
            outputs (List[LogOutput], optional): Liste des sorties de log à utiliser
                (par exemple fichier, console). Par défaut [LogOutput.FILE, LogOutput.CONSOLE].

        Attributes:
            module_name (str): Nom du module associé au logger.
            outputs (List[LogOutput]): Sorties de log configurées.
            log_file (Path): Chemin vers le fichier de log.
        """
        load_dotenv()
        self.module_name = module_name
        self.outputs = (
            outputs if outputs is not None else [LogOutput.FILE, LogOutput.CONSOLE]
        )
        self.log_file = Path(__file__).resolve().parents[3] / "logs" / "SmartWatch.log"
        self._setup_logging()

    def _setup_logging(self):
        """
        Configure le système de journalisation pour le module courant.

        Cette méthode initialise le logger en fonction du niveau de log spécifié dans la variable d'environnement
        `LOG_LEVEL` (par défaut à "INFO"). Elle configure les handlers pour la sortie console et/ou fichier selon
        les options définies dans `self.outputs`. Le dossier de logs est créé si nécessaire, et la rotation des fichiers
        est gérée pour limiter la taille et le nombre de sauvegardes. Si le logger possède déjà des handlers, la
        configuration est ignorée.

        En cas d'erreur lors de la configuration, le logger est désactivé et une erreur est affichée.

        Raises:
            Exception: Si une erreur survient lors de la configuration du logger.
        """
        try:
            log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
            log_level = LogLevel[log_level_str].value

            self.logger = logging.getLogger(self.module_name)
            self.logger.setLevel(log_level)

            if self.logger.hasHandlers():
                return

            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
            )

            # Créer le dossier logs s'il n'existe pas
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

            handler_map = {
                LogOutput.FILE: RotatingFileHandler(
                    self.log_file,
                    maxBytes=50 * 1024 * 1024,  # 50 MB par fichier
                    backupCount=5,  # Garder 5 fichiers de sauvegarde
                    encoding="utf-8",
                ),
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
        """
        Enregistre un message dans le journal selon le niveau spécifié.

        Cette méthode vérifie d'abord si le logger est disponible avant d'essayer d'écrire le message.
        En cas d'échec lors de l'écriture, une erreur est affichée dans la sortie standard.

        Args:
            level (LogLevel): Le niveau de log à utiliser (ex: INFO, WARNING, ERROR).
            message (str): Le message à enregistrer dans le journal.

        Returns:
            None

        Raises:
            Affiche une erreur dans la sortie standard si l'écriture dans le journal échoue.
        """
        if not hasattr(self, "available") or not self.available:
            return
        try:
            self.logger.log(level.value, f"{message}")
        except Exception as e:
            print(f"Erreur lors de l'écriture du log: {e}")

    def log(self, level: LogLevel, message: str):
        """
        Enregistre un message de journalisation avec un niveau spécifié.

        Args:
            level (LogLevel): Le niveau de journalisation (ex. INFO, WARNING, ERROR).
            message (str): Le message à enregistrer dans le journal.
        """
        self._log(level, message)

    # Les méthodes de journalisation pour les niveaux spécifiques
    # Elles permettent d'utiliser les niveaux de log directement, exemple :
    # logger.debug("Ceci est un message de débogage")
    # logger.info("Ceci est un message d'information")
    def debug(self, message: str):
        """
        Enregistre un message de débogage dans le journal.

        Args:
            message (str): Le message à enregistrer au niveau DEBUG.
        """
        self._log(LogLevel.DEBUG, message)

    def info(self, message: str):
        """
        Enregistre un message d'information dans le journal.

        Args:
            message (str): Le message à enregistrer au niveau INFO.
        """
        self._log(LogLevel.INFO, message)

    def warning(self, message: str):
        """
        Enregistre un message d'alerte dans le journal.

        Args:
            message (str): Le message à enregistrer au niveau WARNING.
        """
        self._log(LogLevel.WARNING, message)

    def error(self, message: str):
        """
        Enregistre un message d'erreur dans le journal.

        Args:
            message (str): Le message à enregistrer au niveau ERROR.
        """
        self._log(LogLevel.ERROR, message)

    def critical(self, message: str):
        """
        Enregistre un message d'alerte critique dans le journal.

        Args:
            message (str): Le message à enregistrer au niveau CRITICAL.
        """
        self._log(LogLevel.CRITICAL, message)

    def section(self, title: str, level: LogLevel = LogLevel.INFO):
        """
        Affiche une section formatée dans les logs, entourée de séparateurs pour mettre en valeur le titre.

        Args:
            title (str): Le titre de la section à afficher dans les logs.
            level (LogLevel, optionnel): Le niveau de log à utiliser pour cette section. Par défaut, LogLevel.INFO.
        """
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
    Crée et retourne une instance de SmartWatchLogger pour le module spécifié.

    Cette fonction permet de configurer les sorties du logger (fichier, console)
    en fonction de la liste fournie. Si aucune liste n'est donnée, toutes les sorties
    disponibles sont utilisées par défaut. Les sorties non reconnues sont ignorées
    avec un avertissement.

    Args:
        module_name (str, optionnel): Nom du module pour lequel le logger est créé.
            Par défaut "main".
        outputs (List[str], optionnel): Liste des sorties désirées pour le logger.
            Les valeurs acceptées sont "file" et "console". Si None, toutes les sorties
            sont activées.

    Returns:
        SmartWatchLogger: Instance configurée du logger pour le module spécifié.

    Warns:
        Affiche un avertissement dans la console si certains éléments de `outputs`
        ne sont pas reconnus.
    """
    output_map = {"file": LogOutput.FILE, "console": LogOutput.CONSOLE}

    if outputs is None:
        log_outputs = list(output_map.values())
    else:
        log_outputs = [output_map[out] for out in outputs if out in output_map]
        if len(log_outputs) != len(outputs or []):
            print("Warning: Certains outputs non reconnus ont été ignorés.")

    return SmartWatchLogger(module_name=module_name, outputs=log_outputs)
