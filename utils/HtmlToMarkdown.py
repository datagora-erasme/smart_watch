from html_to_markdown import convert_to_markdown


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

    def convert(self):
        """
        Convert HTML to Markdown using the specified library.

        Returns:
            str: The converted Markdown content
        """
        if self.library_type == "html_to_markdown":
            try:
                return convert_to_markdown(self.html)
            except ImportError:
                raise ImportError("html_to_markdown library not found")

        elif self.library_type == "bs4":
            try:
                import bs4

                soup = bs4.BeautifulSoup(self.html, self.bs4_parser)
                return convert_to_markdown(soup)
            except ImportError:
                raise ImportError("Required librarie bs4 not found")
            except bs4.exceptions.FeatureNotFound:
                raise ImportError(
                    f"BeautifulSoup feature '{self.bs4_parser}' not found. Ensure you have the correct parser installed, or that the 'self.bs4_option' is correct."
                )

        else:
            raise ValueError(
                f"Unsupported library type: {self.library_type}. Use 'pyhtml2md', 'html_to_markdown', or 'bs4'"
            )


# Example usage
if __name__ == "__main__":
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
    print("\nUsing html_to_markdown:")
    print(converter1.convert())

    converter2 = HtmlToMarkdown(HTML, library_type="bs4")
    print("\nUsing BeautifulSoup + html_to_markdown:")
    print(converter2.convert())

    # Enregistrer le résultat dans un fichier Markdown
    with open("output.md", "w", encoding="utf-8") as md_file:
        md_file.write(converter2.convert())
