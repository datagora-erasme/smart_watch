# Gestionnaire pour la génération et l'envoi de rapports.
# Documentation : https://datagora-erasme.github.io/smart_watch/source/modules/reporting/report_manager.html

import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..core.ConfigManager import ConfigManager
from ..core.EnvoyerMail import EmailSender
from ..core.ErrorHandler import ErrorCategory, ErrorSeverity, handle_errors
from ..core.Logger import SmartWatchLogger, create_logger
from ..reporting.GenererRapportHTML import generer_rapport_html

# Initialize logger for this module
logger = create_logger(
    module_name="ReportManager",
)


class ReportManager:
    """Gestionnaire pour la génération et l'envoi de rapports."""

    def __init__(self, config: ConfigManager, logger: SmartWatchLogger) -> None:
        """
        Initialise le gestionnaire de rapports avec la configuration et le logger.

        Cette méthode configure les composants nécessaires pour générer et envoyer
        les rapports : configuration du système et logger pour le suivi des opérations.

        Args:
            config (ConfigManager): gestionnaire de configuration du système.
            logger: instance de logger pour la journalisation des événements.
        """
        self.config = config
        self.logger = logger

    @handle_errors(
        category=ErrorCategory.FILE_IO,
        severity=ErrorSeverity.MEDIUM,
        user_message="Erreur lors de la création de l'archive des logs.",
        default_return=None,
    )
    def _create_logs_zip(self) -> Optional[str]:
        """Crée un fichier zip contenant tous les logs et la base de données."""
        # Utiliser le chemin racine du projet depuis la configuration
        project_root = self.config.project_root
        logs_dir = project_root / "logs"
        data_dir = project_root / "data"

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
            db_file = data_dir / self.config.database.db_file.name
            if db_file.exists():
                zip_file.write(db_file, db_file.name)
                files_added += 1
                self.logger.debug(f"Base de données ajoutée au zip: {db_file.name}")
            else:
                self.logger.warning(f"Base de données {db_file.name} introuvable")

        if files_added > 0:
            self.logger.info(f"Zip créé: {zip_path.name} ({files_added} fichiers)")
            return str(zip_path)
        else:
            self.logger.warning("Aucun fichier trouvé pour le zip, archive non créée.")
            if zip_path.exists():
                zip_path.unlink()  # Supprimer le zip vide
            return None

    def generate_and_send_report(self, execution_id: int) -> None:
        """Génère et envoie le rapport par email."""
        self.logger.section("GÉNÉRATION ET ENVOI RAPPORT")

        model_info = {
            "modele": self.config.llm.modele,
            "base_url": getattr(self.config.llm, "base_url", None),
            "fournisseur": self.config.llm.fournisseur,
        }

        resume_html, fichier_html = generer_rapport_html(
            db_file=str(self.config.database.db_file),
            titre_rapport="Rapport de vérification des URLs",
            model_info=model_info,
        )

        # Validation de la configuration email
        if not self.config.email or not self.config.email.emetteur:
            raise ValueError(
                "Configuration email manquante - l'envoi par email est obligatoire"
            )

        # Envoi par email obligatoire
        self._send_email_report(resume_html, fichier_html, execution_id)

    @handle_errors(
        category=ErrorCategory.EMAIL,
        severity=ErrorSeverity.CRITICAL,  # Changé de HIGH à CRITICAL car obligatoire
        user_message="Erreur lors de l'envoi de l'email de rapport.",
        reraise=True,  # Ajouté pour faire remonter l'erreur car critique
    )
    def _send_email_report(
        self, resume_html: str, fichier_html: str, execution_id: int
    ):
        """Envoie le rapport par email."""
        self.logger.section("ENVOI EMAIL")
        logs_zip = None
        try:
            # Créer le contenu de l'email
            subject = f"Rapport URLs Horaires - {datetime.now().strftime('%d/%m/%Y')}"

            # Préparer les pièces jointes
            attachments = []

            # Ajouter le rapport HTML (obligatoire)
            if not fichier_html or not Path(fichier_html).exists():
                raise ValueError("Fichier rapport HTML manquant ou introuvable")

            attachments.append(fichier_html)
            self.logger.info(
                f"Rapport HTML ajouté en pièce jointe: {Path(fichier_html).name}"
            )

            # Ajouter le zip des logs (optionnel)
            logs_zip = self._create_logs_zip()
            if logs_zip:
                attachments.append(logs_zip)
                self.logger.info(
                    f"Archive logs ajoutée en pièce jointe: {Path(logs_zip).name}"
                )

            # Utiliser EmailSender pour envoyer l'email
            email_sender = EmailSender(self.config)
            email_sender.send_email(subject, resume_html, attachments)
            self.logger.info("Email envoyé avec succès")

        finally:
            # Nettoyage des fichiers temporaires, même en cas d'erreur
            if fichier_html and Path(fichier_html).exists():
                Path(fichier_html).unlink()
                self.logger.debug("Fichier HTML temporaire supprimé")

            if logs_zip and Path(logs_zip).exists():
                Path(logs_zip).unlink()
                self.logger.debug("Fichier zip logs temporaire supprimé")
