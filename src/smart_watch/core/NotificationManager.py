import os
import zipfile
from datetime import datetime
from typing import Dict

from ..reporting.GenererRapportHTML import generer_rapport_html
from .ConfigManager import ConfigManager
from .DatabaseManager import DatabaseManager
from .EnvoyerMail import EmailSender
from .Logger import SmartWatchLogger


class NotificationManager:
    """Gère la création et l'envoi de notifications par email avec pièces jointes."""

    def __init__(
        self,
        config_manager: ConfigManager,
        db_manager: DatabaseManager,
        logger: SmartWatchLogger,
    ):
        self.config_manager = config_manager
        self.db_manager = db_manager
        self.logger = logger
        self.email_sender = EmailSender(config_manager)

    def send_report_email(self, stats: Dict):
        """Génère le rapport, compresse les logs et envoie l'email."""
        report_path = self._generate_report()
        zip_log_path = self._zip_log_file()

        attachments = []
        if report_path:
            attachments.append(report_path)
        if zip_log_path:
            attachments.append(zip_log_path)

        if not attachments:
            self.logger.warning("Aucun rapport ou log à envoyer par email.")
            return

        try:
            subject = (
                f"Rapport SmartWatch - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            body = f"Rapport d'exécution ci-joint.<br/><br/>{stats}"
            self.email_sender.send_email(subject, body, attachments)
            self.logger.info("Email de rapport envoyé avec succès.")
        finally:
            # Nettoyage des fichiers temporaires
            if report_path and os.path.exists(report_path):
                os.remove(report_path)
                self.logger.debug("Fichier de rapport temporaire supprimé.")
            if zip_log_path and os.path.exists(zip_log_path):
                os.remove(zip_log_path)
                self.logger.debug("Fichier de log zippé temporaire supprimé.")

    def _generate_report(self) -> str:
        """Génère le rapport HTML."""
        try:
            # Utiliser la fonction generer_rapport_html du module GenererRapportHTML
            model_info = {
                "modele": self.config_manager.llm.modele,
                "fournisseur": self.config_manager.llm.fournisseur,
                "base_url": getattr(self.config_manager.llm, "base_url", None),
            }

            resume_html, fichier_html = generer_rapport_html(
                db_file=str(self.config_manager.database.db_file),
                table_name="resultats_extraction",
                titre_rapport=f"Rapport SmartWatch - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                model_info=model_info,
            )

            return fichier_html
        except Exception as e:
            self.logger.error(f"Erreur lors de la génération du rapport: {e}")
            return ""

    def _zip_log_file(self) -> str:
        """Compresse le fichier de log et retourne le chemin du fichier zip."""
        log_file_path = str(self.logger.log_file)
        if not os.path.exists(log_file_path):
            self.logger.warning("Fichier de log non trouvé, ne peut pas être zippé.")
            return ""

        try:
            zip_path = f"{os.path.splitext(log_file_path)[0]}_{datetime.now().strftime('%Y%m%d_%H%M')}.zip"
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(log_file_path, os.path.basename(log_file_path))
            self.logger.info(f"Fichier de log compressé avec succès: {zip_path}")
            return zip_path
        except Exception as e:
            self.logger.error(f"Erreur lors de la compression du fichier de log: {e}")
            return ""
