# Documentation:
# https://datagora-erasme.github.io/smart_watch/source/modules/utils/MarkdownCleaner.html

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Sequence, Tuple

from sqlalchemy.engine import Row

from ..core.DatabaseManager import DatabaseManager
from ..core.ErrorHandler import ErrorCategory, ErrorSeverity, handle_errors
from ..core.Logger import SmartWatchLogger, create_logger
from ..data_models.schema_bdd import Lieux, ResultatsExtraction

if TYPE_CHECKING:
    from ..processing.database_processor import DatabaseProcessor

logger: SmartWatchLogger = create_logger(module_name="MarkdownCleaner")


@dataclass
class CleaningStats:
    """
    Dataclass pour stocker les statistiques de nettoyage du Markdown.

    Attributes:
        texts_processed (int) : nombre total de textes traités.
        texts_successful (int) : nombre de textes nettoyés avec succès.
        chars_replaced (int) : nombre total de caractères remplacés.
    """

    texts_processed: int = 0
    texts_successful: int = 0
    chars_replaced: int = 0

    def get_summary(self) -> Dict[str, int]:
        """
        Retourne un résumé des statistiques de nettoyage.

        Returns:
            Dict[str, int] : un dictionnaire contenant les statistiques.
        """
        return {
            "texts_processed": self.texts_processed,
            "texts_successful": self.texts_successful,
            "chars_replaced": self.chars_replaced,
        }


class MarkdownCleaner:
    """
    Classe pour nettoyer et normaliser le contenu Markdown brut.

    Cette classe fournit un pipeline de nettoyage configurable pour préparer
    le texte Markdown à un traitement ultérieur, notamment par des modèles de langage.
    """

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
    _RE_MULTI_NEWLINES = re.compile(r"(\r\n|\n|\r){3,}")

    # Regex pour les lignes composées uniquement de caractères de formatage
    _RE_FORMATTING_LINES = re.compile(r"^[\s#\-\"=_\(\[\]\)\.]+$", re.MULTILINE)

    def __init__(self, config: Any, logger: SmartWatchLogger):
        """
        Initialise le MarkdownCleaner.

        Args:
            config (Any) : l'objet de configuration de l'application.
            logger (SmartWatchLogger) : l'instance du logger à utiliser.
        """
        self.config: Any = config
        self.logger: SmartWatchLogger = logger
        self.char_replacements: Dict[str, str] = (
            self.config.processing.char_replacements
        )

    def _get_pending_cleaning(
        self, db_manager: DatabaseManager, execution_id: int
    ) -> Sequence[Row[Tuple[ResultatsExtraction, Lieux]]]:
        """
        Récupère les enregistrements nécessitant un nettoyage du markdown.

        Args:
            db_manager (DatabaseManager) : le gestionnaire de base de données.
            execution_id (int) : l'ID de l'exécution à traiter.

        Returns:
            Sequence[Row[Tuple[ResultatsExtraction, Lieux]]] : une séquence de résultats à nettoyer.
        """
        session = db_manager.Session()
        try:
            return (
                session.query(ResultatsExtraction, Lieux)
                .join(Lieux, ResultatsExtraction.lieu_id == Lieux.identifiant)
                .filter(
                    ResultatsExtraction.id_execution == execution_id,
                    ResultatsExtraction.statut_url == "ok",
                    ResultatsExtraction.markdown_brut != "",
                    ResultatsExtraction.markdown_brut.isnot(None),
                    ResultatsExtraction.markdown_nettoye == "",
                )
                .all()
            )
        finally:
            session.close()

    def process_markdown_cleaning(
        self, db_processor: "DatabaseProcessor", execution_id: int
    ) -> None:
        """
        Nettoie le markdown brut pour tous les résultats d'une exécution donnée.

        Args:
            db_processor (DatabaseProcessor) : le processeur de base de données.
            execution_id (int) : l'ID de l'exécution.
        """
        pending_results = db_processor.get_results_with_raw_markdown(execution_id)

        for result in pending_results:
            markdown_content = getattr(result, "markdown_brut", "") or ""
            cleaned_markdown = self.clean_markdown_content(markdown_content)
            resultat_id = getattr(result, "id_resultats_extraction", None)

            if resultat_id is not None:
                if not isinstance(resultat_id, int):
                    resultat_id = int(resultat_id)
                db_processor.update_cleaned_markdown(resultat_id, cleaned_markdown)
            else:
                self.logger.warning(
                    "Impossible de trouver l'ID pour un résultat de nettoyage"
                )

    @handle_errors(
        category=ErrorCategory.CONVERSION,
        severity=ErrorSeverity.LOW,
        user_message="Erreur lors du nettoyage du contenu Markdown.",
        reraise=True,
    )
    def clean_markdown_content(self, text: str) -> str:
        """
        Applique un pipeline complet de nettoyage sur un contenu Markdown.

        Args:
            text (str) : le contenu Markdown à nettoyer.

        Returns:
            str : le contenu Markdown nettoyé et normalisé.
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
        category=ErrorCategory.CONVERSION, severity=ErrorSeverity.LOW, reraise=True
    )
    def _remove_markdown_links(self, text: str) -> str:
        """
        Supprime tous les types de liens Markdown, en ne conservant que le texte visible.

        Args:
            text (str) : le texte contenant des liens Markdown.

        Returns:
            str : le texte sans les liens Markdown.
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
        category=ErrorCategory.CONVERSION, severity=ErrorSeverity.LOW, reraise=True
    )
    def _apply_char_replacements(self, text: str) -> str:
        """
        Applique les remplacements de caractères définis dans la configuration.

        Args:
            text (str) : le texte à traiter.

        Returns:
            str : le texte avec les caractères remplacés.
        """
        if not self.char_replacements or not text:
            return text

        replacements = self.char_replacements.copy()
        keys_to_preserve = ["\t", "    ", "   ", "  ", " \n"]
        for key in keys_to_preserve:
            if key in replacements:
                del replacements[key]

        for _ in range(3):
            for source, target in replacements.items():
                text = text.replace(source, target)
        return text

    @handle_errors(
        category=ErrorCategory.CONVERSION, severity=ErrorSeverity.LOW, reraise=True
    )
    def _clean_multiple_newlines(self, text: str) -> str:
        """
        Remplace les séquences de 3 sauts de ligne ou plus par exactement 2.

        Args:
            text (str) : le texte à nettoyer.

        Returns:
            str : le texte avec des sauts de ligne normalisés.
        """
        return self._RE_MULTI_NEWLINES.sub("\n\n", text) if text else ""

    @handle_errors(
        category=ErrorCategory.CONVERSION, severity=ErrorSeverity.LOW, reraise=True
    )
    def _remove_formatting_lines(self, text: str) -> str:
        """
        Supprime les lignes composées uniquement de caractères de formatage.

        Args:
            text (str) : le texte à nettoyer.

        Returns:
            str : le texte sans les lignes de formatage inutiles.
        """
        if not text:
            return ""
        lines = text.split("\n")
        cleaned_lines = [
            line for line in lines if not self._RE_FORMATTING_LINES.match(line)
        ]
        return "\n".join(cleaned_lines)

    @handle_errors(
        category=ErrorCategory.CONVERSION, severity=ErrorSeverity.LOW, reraise=True
    )
    def _remove_consecutive_duplicate_lines(self, text: str) -> str:
        """
        Supprime les lignes consécutives qui sont identiques après nettoyage des espaces.

        Args:
            text (str) : le texte à nettoyer.

        Returns:
            str : le texte sans les lignes dupliquées consécutives.
        """
        if not text:
            return ""

        lines: List[str] = text.split("\n")
        cleaned_lines: List[str] = []
        last_non_empty_line: Optional[str] = None

        for line in lines:
            stripped_line = line.strip()
            if not stripped_line:
                if cleaned_lines and cleaned_lines[-1].strip() != "":
                    cleaned_lines.append(line)
            else:
                if stripped_line != last_non_empty_line:
                    cleaned_lines.append(line)
                    last_non_empty_line = stripped_line

        while cleaned_lines and cleaned_lines[-1].strip() == "":
            cleaned_lines.pop()

        return "\n".join(cleaned_lines)
