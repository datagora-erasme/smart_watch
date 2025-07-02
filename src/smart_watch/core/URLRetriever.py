import ssl

import urllib3

from ..utils.HtmlToMarkdown import HtmlToMarkdown
from .ErrorHandler import ErrorCategory, ErrorHandler, ErrorSeverity, handle_errors
from .Logger import create_logger

# Initialize logger for this module
logger = create_logger(
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


@handle_errors(
    category=ErrorCategory.NETWORK,
    severity=ErrorSeverity.MEDIUM,
    user_message="Erreur lors de la récupération de l'URL",
)
def retrieve_url(
    row: dict,
    sortie: str = "html",
    encoding_errors: str = "ignore",
    config=None,
) -> dict:
    """
    Récupère le contenu HTML d'une URL avec gestion d'erreurs centralisée.
    Note: Le nettoyage avancé du markdown est maintenant géré par MarkdownCleaner.
    """
    row_dict = dict(row)
    url = row.get("url", "")
    identifiant = row.get("identifiant", "N/A")

    if not url:
        # Créer un contexte d'erreur spécifique
        context = error_handler.create_error_context(
            module="URLRetriever",
            function="retrieve_url",
            operation="Validation URL",
            data={"row_keys": list(row.keys()), "identifiant": identifiant},
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
        logger.debug(f"[{identifiant}] Récupération URL: {url}")

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
                logger.warning(f"[{identifiant}] Trop de redirections: {url}")
                return row_dict
            elif "CERTIFICATE_VERIFY_FAILED" in error_str:
                logger.debug(
                    f"[{identifiant}] Erreur certificat, nouvelle tentative sans vérification"
                )
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
                logger.debug(
                    f"[{identifiant}] Erreur DH_KEY, nouvelle tentative avec sécurité réduite"
                )
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
                    f"[{identifiant}] Erreur SSL, nouvelle tentative avec mitigations complètes"
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
            logger.warning(f"[{identifiant}] Erreur HTTP {response.status}: {url}")
        else:
            # Decode content
            content_type = response.headers.get("Content-Type", "")
            encoding = None
            if "charset=" in content_type:
                encoding = content_type.split("charset=")[-1].strip()
            else:
                encoding = "utf-8"

            html_content = response.data.decode(encoding, errors=encoding_errors)
            logger.debug(
                f"[{identifiant}] Contenu décodé ({encoding}): {len(html_content)} caractères"
            )

            if sortie == "html":
                row_dict[sortie] = html_content
            elif sortie == "markdown":
                converter = HtmlToMarkdown(
                    html=html_content,
                    config=config,
                )
                try:
                    markdown_content = converter.convert()
                    row_dict[sortie] = markdown_content
                except Exception as e:
                    logger.error(f"[{identifiant}] Erreur conversion Markdown: {e}")
                    row_dict[sortie] = html_content

            # Convert HTML to Markdown if HTML content is available
            if row_dict.get("html") and row_dict["html"].strip():
                converter = HtmlToMarkdown(
                    html=row_dict["html"],
                    config=config,
                )
                markdown_content = converter.convert()
                row_dict["markdown"] = markdown_content

            row_dict["statut"] = "ok"
            row_dict["code_http"] = response.status
            row_dict["message"] = ""
            logger.info(f"[{identifiant}] Récupération réussie: {url}")

    except urllib3.exceptions.TimeoutError as e:
        context = error_handler.create_error_context(
            module="URLRetriever",
            function="retrieve_url",
            operation=f"Récupération URL {url}",
            data={"url": url, "timeout": 30, "identifiant": identifiant},
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
            data={"url": url, "identifiant": identifiant},
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
