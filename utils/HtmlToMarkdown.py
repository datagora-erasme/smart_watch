import os
from pathlib import Path

from dotenv import load_dotenv
from html_to_markdown import convert_to_markdown

from core.Logger import LogOutput, create_logger

# Charger la variable d'environnement pour le nom du fichier log
load_dotenv()
csv_name = os.getenv("CSV_URL_HORAIRES")

# Initialize logger for this module
logger = create_logger(
    outputs=[LogOutput.CONSOLE, LogOutput.FILE],
    log_file=Path(__file__).parent.parent / "logs" / f"{csv_name}.log",
    module_name="HtmlToMarkdown",
)


class HtmlToMarkdown:
    """
    A class to convert HTML to Markdown using different libraries.
    """

    def __init__(self, html, library_type="bs4", bs4_parser="lxml"):
        """
        Initialize the Html2Markdown instance.

        Args:
            html (str): The HTML content to convert.
            library_type (str): The library to use for conversion.
            Options are 'html_to_markdown', or 'bs4'.
            bs4 option uses html_to_markdown and a bs4 parser.
            bs4_parser (str): The parser option for BeautifulSoup (default is 'lxml').
            Choose from "lxml", "lxml-xml", "html.parser", or "html5lib".
            You may also choose the type of markup to be used: "html", "html5", "xml".

        Note:
            It's recommended that you name a specific parser, so that Beautiful Soup gives you
            the same results across platforms and virtual environments.
        """
        self.html = html
        self.library_type = library_type
        self.bs4_parser = bs4_parser
        logger.debug(f"HtmlToMarkdown initialisé: {library_type}")

    def convert(self):
        """
        Convert HTML to Markdown using the specified library.

        Returns:
            str: The converted Markdown content
        """
        try:
            if self.library_type == "html_to_markdown":
                logger.debug("Conversion avec html_to_markdown")
                return convert_to_markdown(self.html)

            elif self.library_type == "bs4":
                logger.debug(f"Conversion avec BeautifulSoup + {self.bs4_parser}")
                import bs4

                soup = bs4.BeautifulSoup(self.html, self.bs4_parser)
                return convert_to_markdown(soup)

            else:
                logger.error(f"Type de librairie non supporté: {self.library_type}")
                raise ValueError(
                    f"Unsupported library type: {self.library_type}. Use 'html_to_markdown', or 'bs4'"
                )
        except ImportError as e:
            logger.error(f"Librairie manquante: {e}")
            raise
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
    </article>
    """

    # Using different converters
    converter1 = HtmlToMarkdown(HTML, library_type="html_to_markdown")
    logger.info("Test avec html_to_markdown")
    print(converter1.convert())

    converter2 = HtmlToMarkdown(HTML, library_type="bs4")
    logger.info("Test avec BeautifulSoup + html_to_markdown")
    print(converter2.convert())

    # Enregistrer le résultat dans un fichier Markdown
    with open("output.md", "w", encoding="utf-8") as md_file:
        md_file.write(converter2.convert())
    logger.info("Résultat sauvegardé dans output.md")
