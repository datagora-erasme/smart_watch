# Module de traitement pour SmartWatch.
# Documentation : https://datagora-erasme.github.io/smart_watch/source/modules/utils/index.html

from .CSVToPolars import CSVToPolars
from .CustomJsonToOSM import JsonToOsmConverter
from .HtmlToMarkdown import convert_html_to_markdown
from .JoursFeries import get_jours_feries
from .MarkdownCleaner import MarkdownCleaner
from .OSMToCustomJson import OsmToJsonConverter
from .VacancesScolaires import get_vacances_scolaires

__all__ = [
    "CSVToPolars",
    "JsonToOsmConverter",
    "convert_html_to_markdown",
    "get_jours_feries",
    "MarkdownCleaner",
    "OsmToJsonConverter",
    "get_vacances_scolaires",
]
