# Module pour le nettoyage et la normalisation de contenu Markdown
# https://datagora-erasme.github.io/smart_watch/source/modules/utils/MarkdownCleaner.html

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ..core.DatabaseManager import DatabaseManager
from ..core.ErrorHandler import ErrorCategory, ErrorSeverity, handle_errors
from ..core.Logger import create_logger
from ..data_models.schema_bdd import Lieux, ResultatsExtraction

# Initialize logger for this module
logger = create_logger(
    module_name="MarkdownCleaner",
)


@dataclass
class CleaningStats:
    """Dataclass pour stocker les statistiques de nettoyage à chaque étape.

    Attributs :
        texts_processed (int) : Nombre total de textes traités.
        texts_successful (int) : Nombre de textes nettoyés avec succès.
        chars_replaced (int) : Nombre total de caractères remplacés lors du nettoyage.
    """

    texts_processed: int = 0
    texts_successful: int = 0
    chars_replaced: int = 0

    def get_summary(self) -> Dict[str, int]:
        """Retourne un résumé des statistiques de nettoyage.

        Returns:
            Dict[str, int] : Un dictionnaire contenant les statistiques.
        """
        return {
            "texts_processed": self.texts_processed,
            "texts_successful": self.texts_successful,
            "chars_replaced": self.chars_replaced,
        }


class MarkdownCleaner:
    """Une classe pour nettoyer et normaliser le contenu Markdown.

    Cette classe fournit un pipeline pour nettoyer du texte Markdown brut,
    le rendant plus adapté au traitement par des modèles de langage.

    Args:
        config (Any): L'objet de configuration, qui doit avoir un attribut `processing`
                      avec `char_replacements`.
        logger (Any): L'instance du logger pour l'enregistrement des messages.
        char_replacements (Dict[str, str]): Un dictionnaire des caractères à remplacer.
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
    _RE_MULTI_NEWLINES = re.compile(r"\n{3,}")

    # Regex pour les lignes composées uniquement de caractères de formatage
    _RE_FORMATTING_LINES = re.compile(r"^[\s#\-\"=_\(\[\]\)\.]+$", re.MULTILINE)

    def __init__(self, config: Any, logger: Any):
        """Initializes the MarkdownCleaner.

        Args:
            config (Any): The application's configuration object.
            logger (Any): The logger for this instance.
        """
        self.config: Any = config
        self.logger: Any = logger
        # Utiliser la configuration des caractères de remplacement
        self.char_replacements: Dict[str, str] = (
            self.config.processing.char_replacements
        )

    def _get_pending_cleaning(
        self, db_manager: DatabaseManager, execution_id: int
    ) -> List[Tuple[ResultatsExtraction, Lieux]]:
        """Récupère les enregistrements de la base de données nécessitant un nettoyage du markdown.

        Args:
            db_manager (DatabaseManager): L'instance du gestionnaire de base de données.
            execution_id (int): L'identifiant de l'exécution en cours.

        Returns:
            List[Tuple[ResultatsExtraction, Lieux]]: Une liste de tuples, chacun
            contenant un objet `ResultatsExtraction` et un objet `Lieux`.
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
                    ResultatsExtraction.markdown_nettoye == "",  # Pas encore nettoyé
                )
                .all()
            )
        finally:
            session.close()

    def process_markdown_cleaning(
        self, db_manager: DatabaseManager, execution_id: int
    ) -> None:
        """Orchestre le processus de nettoyage du markdown pour une exécution donnée.

        Il récupère les enregistrements en attente, nettoie leur contenu markdown,
        et met à jour la base de données avec le texte nettoyé.

        Args:
            db_manager (DatabaseManager): L'instance du gestionnaire de base de données.
            execution_id (int): L'identifiant de l'exécution en cours.
        """
        self.logger.section("NETTOYAGE MARKDOWN")

        resultats_a_nettoyer = self._get_pending_cleaning(db_manager, execution_id)

        if not resultats_a_nettoyer:
            self.logger.info("Aucun markdown à nettoyer")
            return

        self.logger.info(f"{len(resultats_a_nettoyer)} contenus markdown à nettoyer")

        stats = CleaningStats()
        stats.texts_processed = len(resultats_a_nettoyer)

        for i, (resultat, lieu) in enumerate(resultats_a_nettoyer, 1):
            self.logger.debug(
                f"*{lieu.identifiant}* Nettoyage {i}/{len(resultats_a_nettoyer)} pour '{lieu.nom}'"
            )

            original_markdown = resultat.markdown_brut or ""
            if not original_markdown.strip():
                continue

            len_avant = len(original_markdown)
            # Nettoyer le markdown (la gestion d'erreur est dans la méthode)
            cleaned_markdown = self.clean_markdown_content(original_markdown)
            len_apres = len(cleaned_markdown)

            if len_avant > 0:
                reduction = ((len_avant - len_apres) / len_avant) * 100
                self.logger.info(
                    f"*{lieu.identifiant}* Taille avant/après nettoyage: {len_avant} -> {len_apres} "
                    f"caractères (-{reduction:.2f}%)."
                )
            else:
                self.logger.info(
                    f"*{lieu.identifiant}* Pas de contenu à nettoyer (0 caractère)."
                )

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

    @handle_errors(
        category=ErrorCategory.CONVERSION,
        severity=ErrorSeverity.LOW,
        user_message="Erreur lors du nettoyage du contenu Markdown.",
        reraise=True,
    )
    def clean_markdown_content(self, text: str) -> str:
        """Nettoie le contenu markdown en appliquant des remplacements et en supprimant les liens.

        Args:
            text (str): Le contenu markdown à nettoyer.

        Returns:
            str: Le contenu markdown nettoyé.
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
        """Supprime les liens markdown, en conservant uniquement le texte.

        Gère les formats :
        - [texte](url)
        - [texte](url "titre")
        - [![alt](img)](url "titre") - liens avec images
        - ![alt](img) - images seules

        Args:
            text (str): Le texte contenant des liens markdown.

        Returns:
            str: Le texte sans liens markdown.
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
        """Applique les remplacements de caractères indiqués la configuration.

        Args:
            text (str): Le texte auquel appliquer les remplacements.

        Returns:
            str: Le texte avec les caractères remplacés.
        """
        if not self.char_replacements or not text:
            return text
        # Appliquer plusieurs fois pour gérer les cas récursifs (espaces multiples)
        for _ in range(3):
            for source, target in self.char_replacements.items():
                text = text.replace(source, target)
        return text

    @handle_errors(
        category=ErrorCategory.CONVERSION, severity=ErrorSeverity.LOW, reraise=True
    )
    def _clean_multiple_newlines(self, text: str) -> str:
        """Remplace 3 sauts de ligne ou plus par exactement 2.

        Args:
            text (str): Le texte à nettoyer.

        Returns:
            str: Le texte avec des sauts de ligne normalisés.
        """
        return self._RE_MULTI_NEWLINES.sub("\n\n", text) if text else ""

    @handle_errors(
        category=ErrorCategory.CONVERSION, severity=ErrorSeverity.LOW, reraise=True
    )
    def _remove_formatting_lines(self, text: str) -> str:
        """Supprime les lignes composées uniquement de caractères de formatage.

        Args:
            text (str): Le texte à nettoyer.

        Returns:
            str: Le texte sans les lignes de formatage.
        """
        return self._RE_FORMATTING_LINES.sub("", text) if text else ""

    @handle_errors(
        category=ErrorCategory.CONVERSION, severity=ErrorSeverity.LOW, reraise=True
    )
    def _remove_consecutive_duplicate_lines(self, text: str) -> str:
        """Supprime les lignes consécutives dupliquées, même si elles sont séparées par des sauts de ligne.

        Args:
            text (str): Le texte à nettoyer.

        Returns:
            str: Le texte avec les lignes dupliquées supprimées.
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

        # Supprimer les lignes vides de fin
        while cleaned_lines and cleaned_lines[-1].strip() == "":
            cleaned_lines.pop()

        return "\n".join(cleaned_lines)
