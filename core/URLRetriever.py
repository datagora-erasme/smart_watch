import os
import re
import ssl
from pathlib import Path

import urllib3
from dotenv import load_dotenv

from core.ErrorHandler import ErrorCategory, ErrorHandler, ErrorSeverity, handle_errors
from core.Logger import LogOutput, create_logger
from utils.HtmlToMarkdown import HtmlToMarkdown

# Charger la variable d'environnement pour le nom du fichier log
load_dotenv()
csv_name = os.getenv("CSV_URL_HORAIRES")

# Initialize logger for this module
logger = create_logger(
    outputs=[LogOutput.CONSOLE, LogOutput.FILE],
    log_file=Path(__file__).parent.parent / "data" / "logs" / f"{csv_name}.log",
    module_name="URLRetriever",
)

# Initialisation du gestionnaire d'erreurs pour ce module
error_handler = ErrorHandler()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "fr-FR,fr;q=0.7",
    "Connection": "keep-alive",
}


def _apply_char_replacements(text: str, char_replacements: dict) -> str:
    """
    Applique efficacement les remplacements de caractères selon une table de remplacement.
    Optimisé pour économiser CPU et mémoire en traitant d'abord les remplacements simples
    avec str.translate(), puis les remplacements de chaînes multiples.

    Arguments:
        text (str): Texte à traiter
        char_replacements (dict): Dictionnaire {source: cible} pour les remplacements

    Renvoie:
        str: Texte avec les remplacements appliqués
    """
    if not char_replacements or not text:
        return text

    # Séparer les remplacements de caractères uniques des remplacements de chaînes
    single_char_replacements = {}
    multi_char_replacements = {}

    for source, target in char_replacements.items():
        if len(source) == 1:
            single_char_replacements[source] = target
        else:
            multi_char_replacements[source] = target

    # Appliquer d'abord les remplacements de caractères uniques avec str.translate()
    if single_char_replacements:
        translation_table = str.maketrans(single_char_replacements)
        text = text.translate(translation_table)

    # Appliquer ensuite les remplacements de chaînes multiples
    for source, target in multi_char_replacements.items():
        text = text.replace(source, target)

    return text


@handle_errors(
    category=ErrorCategory.NETWORK,
    severity=ErrorSeverity.MEDIUM,
    user_message="Erreur lors de la récupération de l'URL",
)
def retrieve_url(
    row: dict,
    sortie: str = "html",
    encoding_errors: str = "ignore",
    char_replacements: dict = None,
) -> dict:
    """
    Récupère le contenu HTML d'une URL avec gestion d'erreurs centralisée.
    """
    row_dict = dict(row)
    url = row.get("url", "")

    if not url:
        # Créer un contexte d'erreur spécifique
        context = error_handler.create_error_context(
            module="URLRetriever",
            function="retrieve_url",
            operation="Validation URL",
            data={"row_keys": list(row.keys())},
            user_message="Aucune URL fournie pour la récupération",
        )

        error_handler.handle_error(
            exception=ValueError("URL manquante"),
            context=context,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.HIGH,
        )

        row_dict["statut"] = "critical"
        row_dict["message"] = "Aucune URL n'a été fournie"
        row_dict["code_http"] = 0
        return row_dict

    try:
        logger.debug(f"Récupération URL: {url}")

        # First try with normal SSL verification
        try:
            http = urllib3.PoolManager(timeout=30.0)
            response = http.request(
                "GET",
                url,
                headers=HEADERS,
                redirect=True,
                retries=10,
                timeout=30.0,
            )
        except urllib3.exceptions.MaxRetryError as max_retry_err:
            error_str = str(max_retry_err)

            if "too many redirects" in error_str:
                row_dict["statut"] = "warning"
                row_dict["message"] = "too many redirects"
                row_dict["code_http"] = 310
                logger.warning(f"Trop de redirections: {url}")
                return row_dict
            elif "CERTIFICATE_VERIFY_FAILED" in error_str:
                logger.debug("Erreur certificat, nouvelle tentative sans vérification")
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                http = urllib3.PoolManager(cert_reqs=ssl.CERT_NONE, ssl_context=ctx)
                response = http.request(
                    "GET",
                    url,
                    headers=HEADERS,
                    redirect=True,
                    retries=10,
                    timeout=30.0,
                )
            elif "DH_KEY_TOO_SMALL" in error_str:
                logger.debug("Erreur DH_KEY, nouvelle tentative avec sécurité réduite")
                ctx = ssl.create_default_context()
                ctx.set_ciphers("DEFAULT@SECLEVEL=1")
                http = urllib3.PoolManager(ssl_context=ctx)
                response = http.request(
                    "GET",
                    url,
                    headers=HEADERS,
                    redirect=True,
                    retries=10,
                    timeout=30.0,
                )
            else:
                logger.debug(
                    "Erreur SSL, nouvelle tentative avec mitigations complètes"
                )
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                ctx.set_ciphers("DEFAULT@SECLEVEL=1")

                http = urllib3.PoolManager(cert_reqs=ssl.CERT_NONE, ssl_context=ctx)
                response = http.request(
                    "GET",
                    url,
                    headers=HEADERS,
                    redirect=True,
                    retries=10,
                    timeout=30.0,
                )

        if response.status != 200:
            row_dict["statut"] = "warning"
            row_dict["code_http"] = response.status
            row_dict["message"] = f"HTTP error {response.status}"
            logger.warning(f"Erreur HTTP {response.status}: {url}")
        else:
            # Decode content
            content_type = response.headers.get("Content-Type", "")
            encoding = None
            if "charset=" in content_type:
                encoding = content_type.split("charset=")[-1].strip()
            else:
                encoding = "utf-8"

            html_content = response.data.decode(encoding, errors=encoding_errors)
            logger.debug(f"Contenu décodé ({encoding}): {len(html_content)} caractères")

            if sortie == "html":
                row_dict[sortie] = html_content
            elif sortie == "markdown":
                converter = HtmlToMarkdown(
                    html=html_content, library_type="bs4", bs4_parser="lxml"
                )
                try:
                    markdown_content = converter.convert()
                    markdown_content = re.sub(r"\n{3,}", "\n\n", markdown_content)
                    if char_replacements:
                        markdown_content = _apply_char_replacements(
                            markdown_content, char_replacements
                        )
                    row_dict[sortie] = markdown_content
                except Exception as e:
                    logger.error(f"Erreur conversion Markdown: {e}")
                    row_dict[sortie] = html_content

            # Convert HTML to Markdown if HTML content is available
            if row_dict.get("html") and row_dict["html"].strip():
                converter = HtmlToMarkdown(
                    html=row_dict["html"], library_type="bs4", bs4_parser="lxml"
                )
                markdown_content = converter.convert()
                if char_replacements:
                    markdown_content = _apply_char_replacements(
                        markdown_content, char_replacements
                    )
                row_dict["markdown"] = markdown_content

            row_dict["statut"] = "ok"
            row_dict["code_http"] = response.status
            row_dict["message"] = ""
            logger.info(f"Récupération réussie: {url}")

    except urllib3.exceptions.TimeoutError as e:
        context = error_handler.create_error_context(
            module="URLRetriever",
            function="retrieve_url",
            operation=f"Récupération URL {url}",
            data={"url": url, "timeout": 30},
            user_message=f"Timeout lors de l'accès à {url}",
        )

        error_handler.handle_error(
            exception=e,
            context=context,
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
        )

        row_dict["statut"] = "warning"
        row_dict["code_http"] = 0
        row_dict["message"] = "Timeout"

    except Exception as e:
        context = error_handler.create_error_context(
            module="URLRetriever",
            function="retrieve_url",
            operation=f"Récupération URL {url}",
            data={"url": url},
            user_message=f"Erreur lors de l'accès à {url}",
        )

        error_handler.handle_error(
            exception=e,
            context=context,
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
        )

        row_dict["statut"] = "critical"
        row_dict["code_http"] = 0
        row_dict["message"] = str(e)

    return row_dict


# Exemple depuis une URL
# Enlever "utils."" dans les imports pour exécuter ce code


# row = {
#     "url": "https://www.jeffwinterinsights.com/insights/chatgpt-venn-diagram",
#     "markdown": "",
# }


# resu = RetrieveURL(row, sortie="html", errors="ignore")
# with open("output_from_url.md", "w", encoding="utf-8") as md_file:
#     md_file.write(resu["markdown"])
#     md_file.write(resu["markdown"])
