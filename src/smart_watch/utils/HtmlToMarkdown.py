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
def convert_html_to_markdown(html: str) -> str:
    """
    Convertit une chaîne HTML en Markdown.

    Utilise BeautifulSoup pour un parsing robuste avant la conversion,
    ce qui permet de nettoyer le HTML et de gérer les balises mal formées.

    Args:
        html (str): Le contenu HTML à convertir.

    Returns:
        str: Le contenu converti en Markdown.
    """
    if not html:
        return ""
    logger.debug("Conversion HTML vers Markdown avec BeautifulSoup + lxml")
    # Utiliser BeautifulSoup pour parser et nettoyer le HTML
    soup = bs4.BeautifulSoup(html, "lxml").get_text()  # n'extraire que le texte
    # Convertir l'objet Soup en Markdown
    return convert_to_markdown(str(soup))
