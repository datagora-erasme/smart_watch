"""
Module pour le nettoyage et la normalisation de contenu Markdown.
Ce module nettoie le markdown issu du téléchargement d'URLs.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Tuple

from ..core.ErrorHandler import ErrorCategory, ErrorSeverity, handle_errors
from ..core.Logger import create_logger
from ..data_models.schema_bdd import Lieux, ResultatsExtraction

# Initialize logger for this module
logger = create_logger(
    module_name="MarkdownCleaner",
)


@dataclass
class CleaningStats:
    """Statistiques de nettoyage pour chaque étape."""

    texts_processed: int = 0
    texts_successful: int = 0
    chars_replaced: int = 0

    def get_summary(self) -> Dict[str, int]:
        return {
            "texts_processed": self.texts_processed,
            "texts_successful": self.texts_successful,
            "chars_replaced": self.chars_replaced,
        }


class MarkdownCleaner:
    """Classe pour le nettoyage et la normalisation de contenu Markdown."""

    # Regex pour supprimer les liens markdown (avec ou sans titre)
    # [texte](url) ou [texte](url "titre")
    _RE_MARKDOWN_LINKS = re.compile(r"\[([^\]]*)\]\([^)]*(?: \"[^\"]*\")?\)")

    # <http://example.com>
    _RE_AUTO_LINKS = re.compile(r"<(https?://[^>]+)>")

    # Regex pour les liens avec images (liens complexes)
    # [![alt](img_url)](link_url "titre")
    _RE_IMAGE_LINKS = re.compile(r"\[!\[[^\]]*\]\([^)]*\)\]\([^)]*(?: \"[^\"]*\")?\)")

    # Regex pour les images standalone
    # ![alt](img_url)
    _RE_STANDALONE_IMAGES = re.compile(r"!\[[^\]]*\]\([^)]*\)")

    # Regex pour les sauts de ligne multiples
    # 3 sauts de ligne ou plus
    _RE_MULTI_NEWLINES = re.compile(r"\n{3,}")

    # Regex pour les lignes composées uniquement de caractères de formatage
    _RE_FORMATTING_LINES = re.compile(r"^[\s#\-\"=_\(\[\]\)\.]+$", re.MULTILINE)

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        # Utiliser la configuration des caractères de remplacement
        self.char_replacements = self.config.processing.char_replacements

    def _get_pending_cleaning(self, db_manager, execution_id: int) -> List[Tuple]:
        """Récupère les enregistrements nécessitant un nettoyage de markdown."""
        session = db_manager.Session()
        try:
            return (
                session.query(ResultatsExtraction, Lieux)
                .join(Lieux, ResultatsExtraction.lieu_id == Lieux.identifiant)
                .filter(
                    ResultatsExtraction.id_execution == execution_id,
                    ResultatsExtraction.statut_url == "ok",
                    ResultatsExtraction.markdown_brut != "",
                    ResultatsExtraction.markdown_brut != None,
                    ResultatsExtraction.markdown_nettoye == "",  # Pas encore nettoyé
                )
                .all()
            )
        finally:
            session.close()

    def process_markdown_cleaning(self, db_manager, execution_id: int) -> CleaningStats:
        """Nettoie le contenu markdown pour tous les enregistrements d'une exécution."""
        self.logger.section("NETTOYAGE MARKDOWN")

        stats = CleaningStats()
        resultats_a_nettoyer = self._get_pending_cleaning(db_manager, execution_id)

        if not resultats_a_nettoyer:
            self.logger.info("Aucun markdown à nettoyer")
            return stats

        self.logger.info(f"{len(resultats_a_nettoyer)} contenus markdown à nettoyer")
        stats.texts_processed = len(resultats_a_nettoyer)

        for i, (resultat, lieu) in enumerate(resultats_a_nettoyer, 1):
            self.logger.debug(f"Nettoyage {i}/{len(resultats_a_nettoyer)}: {lieu.nom}")

            original_markdown = resultat.markdown_brut or ""
            if not original_markdown.strip():
                continue

            # Nettoyer le markdown (la gestion d'erreur est dans la méthode)
            cleaned_markdown = self.clean_markdown_content(original_markdown)

            # Compter les modifications
            if cleaned_markdown != original_markdown:
                stats.chars_replaced += len(original_markdown) - len(cleaned_markdown)

            # Mettre à jour en base
            db_manager.update_cleaned_markdown(
                resultat.id_resultats_extraction, cleaned_markdown
            )
            stats.texts_successful += 1

        self.logger.info(
            f"Markdown nettoyé: {stats.texts_successful}/{stats.texts_processed} réussies"
        )
        return stats

    @handle_errors(
        category=ErrorCategory.CONVERSION,
        severity=ErrorSeverity.LOW,
        user_message="Erreur lors du nettoyage du contenu Markdown.",
        default_return_arg_index=0,  # Retourne le premier argument (text) en cas d'erreur
    )
    def clean_markdown_content(self, text: str) -> str:
        """
        Nettoie un contenu markdown en appliquant les remplacements de caractères et suppression des liens.

        Args:
            text: Contenu markdown à nettoyer

        Returns:
            str: Contenu markdown nettoyé
        """
        if not text:
            return ""

        # 1. Supprimer les liens markdown
        text = self._remove_markdown_links(text)

        # 2. Supprimer les lignes de formatage
        text = self._remove_formatting_lines(text)

        # 3. Appliquer les remplacements de caractères
        text = self._apply_char_replacements(text)

        # 4. Nettoyer les sauts de ligne multiples
        text = self._clean_multiple_newlines(text)

        # 5. Supprimer les lignes en double successives
        text = self._remove_consecutive_duplicate_lines(text)

        return text.strip()

    @handle_errors(
        category=ErrorCategory.CONVERSION,
        severity=ErrorSeverity.LOW,
        default_return_arg_index=0,
    )
    def _remove_markdown_links(self, text: str) -> str:
        """
        Supprime les liens markdown en gardant seulement le texte d'affichage.
        Gère les formats:
        - [texte](url)
        - [texte](url "titre")
        - [![alt](img)](url "titre") - liens avec images
        - ![alt](img) - images standalone

        Args:
            text: Texte contenant des liens markdown

        Returns:
            str: Texte sans les liens markdown
        """
        if not text:
            return ""

        # 1. Liens complexes avec images
        text = self._RE_IMAGE_LINKS.sub("", text)

        # 2. Images standalone
        text = self._RE_STANDALONE_IMAGES.sub("", text)

        # 3. Liens texte simples
        text = self._RE_MARKDOWN_LINKS.sub("", text)

        # 4. Liens automatiques <http://...>
        text = self._RE_AUTO_LINKS.sub("", text)

        return text

    @handle_errors(
        category=ErrorCategory.CONVERSION,
        severity=ErrorSeverity.LOW,
        default_return_arg_index=0,
    )
    def _apply_char_replacements(self, text: str) -> str:
        """Applique les remplacements de caractères depuis la configuration."""
        if not self.char_replacements or not text:
            return text
        # Appliquer plusieurs fois pour gérer les cas récursifs (espaces multiples)
        for _ in range(3):
            for source, target in self.char_replacements.items():
                text = text.replace(source, target)
        return text

    @handle_errors(
        category=ErrorCategory.CONVERSION,
        severity=ErrorSeverity.LOW,
        default_return_arg_index=0,
    )
    def _clean_multiple_newlines(self, text: str) -> str:
        """Remplace 3 sauts de ligne ou plus par exactement 2."""
        return self._RE_MULTI_NEWLINES.sub("\n\n", text) if text else ""

    @handle_errors(
        category=ErrorCategory.CONVERSION,
        severity=ErrorSeverity.LOW,
        default_return_arg_index=0,
    )
    def _remove_formatting_lines(self, text: str) -> str:
        """Supprime les lignes composées uniquement de caractères de formatage."""
        return self._RE_FORMATTING_LINES.sub("", text) if text else ""

    @handle_errors(
        category=ErrorCategory.CONVERSION,
        severity=ErrorSeverity.LOW,
        default_return_arg_index=0,
    )
    def _remove_consecutive_duplicate_lines(self, text: str) -> str:
        """Supprime les lignes en double, même si elles sont séparées par des retours chariot."""
        if not text:
            return ""

        lines = text.split("\n")
        cleaned_lines = []
        last_non_empty_line = None

        for line in lines:
            stripped_line = line.strip()
            if not stripped_line:
                if cleaned_lines and cleaned_lines[-1].strip() != "":
                    cleaned_lines.append(line)
            else:
                if stripped_line != last_non_empty_line:
                    cleaned_lines.append(line)
                    last_non_empty_line = stripped_line

        # Supprimer les lignes vides de fin
        while cleaned_lines and cleaned_lines[-1].strip() == "":
            cleaned_lines.pop()

        return "\n".join(cleaned_lines)
