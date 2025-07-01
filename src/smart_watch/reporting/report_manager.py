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
        """Crée un fichier zip contenant tous les logs."""
        try:
            # Dossier des logs
            logs_dir = Path(__file__).resolve().parents[3] / "logs"

            if not logs_dir.exists():
                self.logger.warning("Dossier logs introuvable")
                return None

            # Créer le nom du fichier zip avec timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_path = logs_dir / f"SmartWatch_logs_{timestamp}.zip"

            # Créer le zip avec tous les fichiers .log
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
                log_files_added = 0
                for log_file in logs_dir.glob("*.log"):
                    if log_file.is_file():
                        zip_file.write(log_file, log_file.name)
                        log_files_added += 1
                        self.logger.debug(f"Log ajouté au zip: {log_file.name}")

            if log_files_added > 0:
                self.logger.info(
                    f"Zip des logs créé: {zip_path.name} ({log_files_added} fichiers)"
                )
                return str(zip_path)
            else:
                self.logger.warning("Aucun fichier log trouvé pour le zip")
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
            subject = f"Rapport URLs - {datetime.now().strftime('%d/%m/%Y')} - {stats.urls_successful} succès"

            body = f"""
            <h2>Rapport de vérification généré</h2>
            <p><strong>Date:</strong> {datetime.now().strftime("%d/%m/%Y à %H:%M")}</p>
            
            <h3>Statistiques:</h3>
            <ul>
                <li>URLs traitées: {stats.urls_successful}/{stats.urls_processed}</li>
                <li>Extractions LLM: {stats.llm_successful}/{stats.llm_processed}</li>
                <li>Comparaisons: {stats.comparisons_successful}/{stats.comparisons_processed}</li>
            </ul>
            
            <p>Consultez les fichiers joints pour le rapport complet et les logs détaillés.</p>
            
            <hr>
            <h3>Résumé du rapport:</h3>
            {resume_html}
            """

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
            email_sender.send_email(subject, body, attachments)
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
