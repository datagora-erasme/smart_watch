# Convertisseur HTML vers Markdown
# https://datagora-erasme.github.io/smart_watch/source/modules/utils/HtmlToMarkdown.html

import bs4
from html_to_markdown import convert_to_markdown

from ..core.ErrorHandler import ErrorCategory, ErrorSeverity, handle_errors
from ..core.Logger import create_logger

# Initialize logger for this module
logger = create_logger(
    module_name="HtmlToMarkdown",
)


@handle_errors(
    category=ErrorCategory.CONVERSION,
    severity=ErrorSeverity.LOW,
    user_message="Erreur lors de la conversion HTML vers Markdown",
    default_return="",
)
def convert_html_to_markdown(html: str, identifiant: str = None) -> str:
    """
    Convertit une chaîne HTML en Markdown.

    Utilise BeautifulSoup pour un parsing robuste avant la conversion,
    ce qui permet de nettoyer le HTML et de gérer les balises mal formées.

    Args:
        html (str): Le contenu HTML à convertir.
        identifiant (str, optional): L'identifiant du lieu pour le logging. Defaults to None.

    Returns:
        str: Le contenu converti en Markdown.
    """
    log_prefix = f"*{identifiant}* " if identifiant else ""
    if not html:
        return ""
    logger.debug(f"{log_prefix}Conversion HTML vers Markdown avec BeautifulSoup + lxml")
    len_avant = len(html)

    # Utiliser BeautifulSoup pour parser et nettoyer le HTML
    soup = bs4.BeautifulSoup(html, "lxml").get_text()  # n'extraire que le texte
    cleaned_text = str(soup)
    len_apres = len(cleaned_text)

    if len_avant > 0:
        reduction = ((len_avant - len_apres) / len_avant) * 100
        logger.info(
            f"{log_prefix}Taille avant/après filtrage texte HTML : {len_avant} -> {len_apres} "
            f"caractères (réduction de {reduction:.2f}%)."
        )
    else:
        logger.info(f"{log_prefix}Pas de contenu HTML à nettoyer (0 caractère).")

    # Convertir l'objet Soup en Markdown
    return convert_to_markdown(cleaned_text)
