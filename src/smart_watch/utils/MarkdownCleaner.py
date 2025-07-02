"""
Module pour le nettoyage et la normalisation de contenu Markdown.
Ce module nettoie le markdown issu du téléchargement d'URLs.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Tuple

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
    _RE_MARKDOWN_LINKS = re.compile(
        r"\[([^\]]*)\]\([^)]*(?: \"[^\"]*\")?\)"
    )  # [texte](url) ou [texte](url "titre")
    _RE_AUTO_LINKS = re.compile(r"<(https?://[^>]+)>")  # <http://example.com>
    # Regex pour les liens avec images (liens complexes)
    _RE_IMAGE_LINKS = re.compile(
        r"\[!\[[^\]]*\]\([^)]*\)\]\([^)]*(?: \"[^\"]*\")?\)"
    )  # [![alt](img_url)](link_url "titre")
    # Regex pour les images standalone
    _RE_STANDALONE_IMAGES = re.compile(r"!\[[^\]]*\]\([^)]*\)")  # ![alt](img_url)
    # Regex pour les sauts de ligne multiples
    _RE_MULTI_NEWLINES = re.compile(r"\n{3,}")  # 3 sauts de ligne ou plus
    # Regex pour les lignes composées uniquement de caractères de formatage
    _RE_FORMATTING_LINES = re.compile(r"^[\s#\-\"=_\(\[\]\)\.]+$", re.MULTILINE)

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        # Utiliser la configuration des caractères de remplacement
        self.char_replacements = self.config.processing.char_replacements

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

            try:
                original_markdown = resultat.markdown or ""
                if not original_markdown.strip():
                    continue

                # Nettoyer le markdown
                cleaned_markdown = self.clean_markdown_content(original_markdown)

                # Compter les modifications
                if cleaned_markdown != original_markdown:
                    stats.chars_replaced += len(original_markdown) - len(
                        cleaned_markdown
                    )

                # Mettre à jour en base
                self._update_cleaned_markdown(
                    db_manager, resultat.id_resultats_extraction, cleaned_markdown
                )
                stats.texts_successful += 1

            except Exception as e:
                self.logger.error(f"Erreur nettoyage markdown {lieu.nom}: {e}")

        self.logger.info(
            f"Markdown nettoyé: {stats.texts_successful}/{stats.texts_processed} réussies"
        )
        return stats

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
                    ResultatsExtraction.markdown != "",
                    ResultatsExtraction.markdown != None,
                )
                .all()
            )
        finally:
            session.close()

    def _update_cleaned_markdown(
        self, db_manager, resultat_id: int, cleaned_markdown: str
    ):
        """Met à jour le markdown nettoyé en base de données."""
        session = db_manager.Session()
        try:
            resultat = session.get(ResultatsExtraction, resultat_id)
            if resultat:
                resultat.markdown = cleaned_markdown
                session.commit()
        finally:
            session.close()

    def clean_markdown_content(self, text: str) -> str:
        """
        Nettoie un contenu markdown en appliquant les remplacements de caractères et suppression des liens.

        Args:
            text: Contenu markdown à nettoyer

        Returns:
            str: Contenu markdown nettoyé
        """
        if not text:
            return text

        # 1. Supprimer les liens markdown
        text = self._remove_markdown_links(text)

        # 2. Supprimer les lignes de formatage (avant les remplacements de caractères)
        text = self._remove_formatting_lines(text)

        # 3. Appliquer tous les remplacements de caractères depuis la configuration
        text = self._apply_char_replacements(text)

        # 4. Nettoyer les sauts de ligne multiples
        text = self._clean_multiple_newlines(text)

        # 5. Supprimer les lignes en double successives (après tout le nettoyage)
        text = self._remove_consecutive_duplicate_lines(text)

        return text.strip()

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
            return text

        try:
            # Compter les liens avant suppression pour debugging
            links_count_before = len(self._RE_MARKDOWN_LINKS.findall(text))
            auto_links_count_before = len(self._RE_AUTO_LINKS.findall(text))
            image_links_count_before = len(self._RE_IMAGE_LINKS.findall(text))
            standalone_images_count_before = len(
                self._RE_STANDALONE_IMAGES.findall(text)
            )

            if any(
                [
                    links_count_before,
                    auto_links_count_before,
                    image_links_count_before,
                    standalone_images_count_before,
                ]
            ):
                logger.debug(
                    f"Liens détectés - Markdown: {links_count_before}, Auto: {auto_links_count_before}, "
                    f"Images+Liens: {image_links_count_before}, Images seules: {standalone_images_count_before}"
                )

            # 1. Supprimer d'abord les liens complexes avec images (ordre important)
            # [![alt](img_url)](link_url "titre") -> suppression complète
            text = self._RE_IMAGE_LINKS.sub("", text)

            # 2. Supprimer les images standalone restantes
            # ![alt](img_url) -> suppression complète
            text = self._RE_STANDALONE_IMAGES.sub("", text)

            # 3. Supprimer les liens texte simples restants
            # [texte](url) ou [texte](url "titre") -> suppression complète
            text = self._RE_MARKDOWN_LINKS.sub("", text)

            # 4. Supprimer complètement les liens automatiques <http://...>
            text = self._RE_AUTO_LINKS.sub("", text)

            return text
        except Exception as e:
            logger.error(f"Erreur lors de la suppression des liens: {e}")
            return text

    def _apply_char_replacements(self, text: str) -> str:
        """Applique les remplacements de caractères depuis la configuration."""
        if not self.char_replacements or not text:
            return text

        try:
            # Remplacements simples et efficaces
            # Appliquer plusieurs fois pour gérer les cas récursifs (espaces multiples)
            for _ in range(3):  # Maximum 3 passes pour traiter les cas complexes
                for source, target in self.char_replacements.items():
                    text = text.replace(source, target)
            return text
        except Exception as e:
            logger.error(f"Erreur lors des remplacements de caractères: {e}")
            return text

    def _clean_multiple_newlines(self, text: str) -> str:
        """
        Nettoie les sauts de ligne multiples en les remplaçant par maximum 2 sauts de ligne.

        Args:
            text: Texte avec potentiellement des sauts de ligne multiples

        Returns:
            str: Texte avec sauts de ligne normalisés
        """
        if not text:
            return text

        try:
            # Remplacer 3 sauts de ligne ou plus par exactement 2
            text = self._RE_MULTI_NEWLINES.sub("\n\n", text)
            return text
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage des sauts de ligne: {e}")
            return text

    def _remove_formatting_lines(self, text: str) -> str:
        """
        Supprime les lignes composées uniquement de caractères de formatage.

        Supprime les lignes qui ne contiennent que des combinaisons de:
        #, -, ", =, _, (, [, ], ), ., espaces, etc.

        Args:
            text: Texte contenant potentiellement des lignes de formatage

        Returns:
            str: Texte sans les lignes de formatage
        """
        if not text:
            return text

        try:
            # Compter les lignes avant suppression pour debugging
            lines_before = len(text.split("\n"))

            # Supprimer les lignes de formatage
            text = self._RE_FORMATTING_LINES.sub("", text)

            lines_after = len(text.split("\n"))
            if lines_before != lines_after:
                logger.debug(
                    f"Lignes de formatage supprimées: {lines_before - lines_after}"
                )

            return text
        except Exception as e:
            logger.error(f"Erreur lors de la suppression des lignes de formatage: {e}")
            return text

    def _remove_consecutive_duplicate_lines(self, text: str) -> str:
        """
        Supprime les lignes en double, même si elles sont séparées par des retours chariot.

        Exemples:
        - "Ligne 1\nLigne 1" -> "Ligne 1"
        - "Ligne 1\n\nLigne 1" -> "Ligne 1"
        - "Ligne 1\n\n\nLigne 1" -> "Ligne 1"

        Args:
            text: Texte contenant potentiellement des lignes dupliquées

        Returns:
            str: Texte sans les lignes dupliquées
        """
        if not text:
            return text

        try:
            lines = text.split("\n")
            lines_before = len(lines)

            cleaned_lines = []
            last_non_empty_line = None

            for line in lines:
                stripped_line = line.strip()

                if not stripped_line:
                    # Ligne vide : ne l'ajoute que si la ligne précédente n'était pas vide
                    if cleaned_lines and cleaned_lines[-1].strip() != "":
                        cleaned_lines.append(line)
                else:
                    # Ligne non vide : ne l'ajoute que si elle est différente de la dernière ligne non vide
                    if stripped_line != last_non_empty_line:
                        cleaned_lines.append(line)
                        last_non_empty_line = stripped_line

            lines_after = len(cleaned_lines)
            if lines_before != lines_after:
                logger.debug(
                    f"Lignes dupliquées ou vides en excès supprimées: {lines_before - lines_after}"
                )

            # Supprimer les lignes vides de fin
            while cleaned_lines and cleaned_lines[-1].strip() == "":
                cleaned_lines.pop()

            return "\n".join(cleaned_lines)

        except Exception as e:
            logger.error(f"Erreur lors de la suppression des lignes dupliquées: {e}")
            return text
