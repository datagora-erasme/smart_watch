import bs4
from html_to_markdown import convert_to_markdown

from ..core.Logger import create_logger

# Initialize logger for this module
logger = create_logger(
    module_name="HtmlToMarkdown",
)


class HtmlToMarkdown:
    """
    A class to convert HTML to Markdown using BeautifulSoup and html-to-markdown.
    """

    def __init__(self, html: str, config=None):
        """
        Initialize the HtmlToMarkdown instance.

        Args:
            html (str): The HTML content to convert.
            config: Configuration manager instance (ConfigManager ou BaseConfig).
        """
        self.html = html
        self.config = config
        logger.debug("HtmlToMarkdown initialisé")

    def convert(self) -> str:
        """
        Convert HTML to Markdown.

        Returns:
            str: The converted Markdown content.
        """
        try:
            logger.debug("Conversion avec BeautifulSoup + lxml")
            soup = bs4.BeautifulSoup(self.html, "lxml")
            return convert_to_markdown(str(soup))
        except Exception as e:
            logger.error(f"Erreur conversion HTML: {e}")
            raise


# Example usage
if __name__ == "__main__":
    logger.section("TEST HTML TO MARKDOWN")

    HTML = """
    <article>
        <h1>Welcome</h1>
        <p>This is a <strong>sample</strong> with a <a href="https://example.com">link</a>.</p>
        <ul>
            <li>Item 1</li>
            <li>Item 2</li>
        </ul>
        <script>console.log('test');</script>
        <style>body { color: red; }</style>
        <hr>
    </article>
    """

    converter = HtmlToMarkdown(HTML)
    logger.info("Test de conversion")
    print("--- Résultat ---")
    markdown_content = converter.convert()
    print(markdown_content)

    # Enregistrer le résultat dans un fichier Markdown
    with open("output.md", "w", encoding="utf-8") as md_file:
        md_file.write(markdown_content)
        logger.info("Résultat sauvegardé dans output.md")

    def convert(self) -> str:
        """
        Convert HTML to Markdown.

        Returns:
            str: The converted Markdown content.
        """
        try:
            logger.debug("Conversion avec BeautifulSoup + lxml")
            soup = bs4.BeautifulSoup(self.html, "lxml")
            return convert_to_markdown(str(soup))
        except Exception as e:
            logger.error(f"Erreur conversion HTML: {e}")
            raise
