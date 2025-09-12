import os
import sys

# Ajouter le répertoire src au chemin Python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Import direct pour éviter les imports circulaires
from smart_watch.utils.HtmlToMarkdown import convert_html_to_markdown


def test_convert_html_to_markdown_simple():
    html = "<h1>Titre</h1><p>Ceci est un paragraphe.</p>"
    markdown = "Titre\n\nCeci est un paragraphe."
    assert convert_html_to_markdown(html).strip() == markdown


def test_convert_html_to_markdown_with_links():
    html = '<p>Visitez <a href="https://www.example.com">notre site</a>.</p>'
    markdown = "Visitez notre site."
    assert convert_html_to_markdown(html).strip() == markdown


def test_convert_html_to_markdown_empty():
    html = ""
    markdown = ""
    assert convert_html_to_markdown(html) == markdown


def test_convert_html_to_markdown_nested_tags():
    html = "<div><p><span>Texte</span> important.</p></div>"
    markdown = "Texte important."
    assert convert_html_to_markdown(html).strip() == markdown


def test_convert_html_to_markdown_special_characters():
    html = "<p>Caractères spéciaux : & < ></p>"
    markdown = "Caractères spéciaux : & < >"
    assert convert_html_to_markdown(html).strip() == markdown
