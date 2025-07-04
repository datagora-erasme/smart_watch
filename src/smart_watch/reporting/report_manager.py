"""
Gestionnaire pour la génération et l'envoi de rapports.
"""

import zipfile
from datetime import datetime
from pathlib import Path

from ..core.ConfigManager import ConfigManager
from ..core.EnvoyerMail import EmailSender
from ..processing.url_processor import ProcessingStats
from ..reporting.GenererRapportHTML import generer_rapport_html


class ReportManager:
    """Gestionnaire pour la génération et l'envoi de rapports."""

    def __init__(self, config: ConfigManager, logger):
        self.config = config
        self.logger = logger

    def _create_logs_zip(self) -> str:
        """Crée un fichier zip contenant tous les logs et la base de données."""
        try:
            # Dossier des logs
            logs_dir = Path(__file__).resolve().parents[3] / "logs"

            # Dossier data pour la base de données
            data_dir = Path(__file__).resolve().parents[3] / "data"

            # Créer le nom du fichier zip avec timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_path = logs_dir / f"SmartWatch_logs_et_bdd_{timestamp}.zip"

            # Créer le zip avec les fichiers log et la base de données
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
                files_added = 0

                # Ajouter le fichier log principal
                log_file = logs_dir / "SmartWatch.log"
                if log_file.exists():
                    zip_file.write(log_file, log_file.name)
                    files_added += 1
                    self.logger.debug(f"Log ajouté au zip: {log_file.name}")
                else:
                    self.logger.warning("Fichier SmartWatch.log introuvable")

                # Ajouter la base de données
                db_file = data_dir / "SmartWatch.db"
                if db_file.exists():
                    zip_file.write(db_file, db_file.name)
                    files_added += 1
                    self.logger.debug(f"Base de données ajoutée au zip: {db_file.name}")
                else:
                    self.logger.warning("Base de données SmartWatch.db introuvable")

            if files_added > 0:
                self.logger.info(f"Zip créé: {zip_path.name} ({files_added} fichiers)")
                return str(zip_path)
            else:
                self.logger.warning("Aucun fichier trouvé pour le zip")
                return None

        except Exception as e:
            self.logger.error(f"Erreur création zip logs: {e}")
            return None

    def generate_and_send_report(self, stats: ProcessingStats):
        """Génère et envoie le rapport par email."""
        self.logger.section("GÉNÉRATION RAPPORT")

        model_info = {
            "modele": self.config.llm.modele,
            "base_url": getattr(self.config.llm, "base_url", None),
            "fournisseur": self.config.llm.fournisseur,
        }

        resume_html, fichier_html = generer_rapport_html(
            db_file=str(self.config.database.db_file),
            table_name="resultats_extraction",
            titre_rapport="Rapport de vérification des URLs",
            model_info=model_info,
        )

        # Envoi par email si configuré
        if self.config.email:
            self._send_email_report(resume_html, fichier_html, stats)
        else:
            self.logger.warning("Email non configuré - rapport sauvegardé localement")

    def _send_email_report(self, resume_html, fichier_html, stats: ProcessingStats):
        """Envoie le rapport par email."""
        self.logger.section("ENVOI EMAIL")

        try:
            # Créer le contenu de l'email
            subject = f"Rapport URLs Horaires - {datetime.now().strftime('%d/%m/%Y')}"

            # Préparer les pièces jointes
            attachments = []

            # Ajouter le rapport HTML
            if fichier_html and Path(fichier_html).exists():
                attachments.append(fichier_html)

            # Ajouter le zip des logs
            logs_zip = self._create_logs_zip()
            if logs_zip:
                attachments.append(logs_zip)

            # Utiliser EmailSender pour envoyer l'email
            email_sender = EmailSender(self.config)
            email_sender.send_email(subject, resume_html, attachments)
            self.logger.info("Email envoyé avec succès")

            # Nettoyage des fichiers temporaires
            if fichier_html and Path(fichier_html).exists():
                Path(fichier_html).unlink()
                self.logger.debug("Fichier HTML temporaire supprimé")

            if logs_zip and Path(logs_zip).exists():
                Path(logs_zip).unlink()
                self.logger.debug("Fichier zip logs temporaire supprimé")

        except Exception as e:
            self.logger.error(f"Erreur envoi email: {e}")
