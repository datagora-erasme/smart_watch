# Documentation: https://datagora-erasme.github.io/smart_watch/source/modules/core/URLRetriever.html
import time
from typing import Any, Dict, Optional

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

from .ErrorHandler import ErrorCategory, ErrorHandler, ErrorSeverity, handle_errors
from .Logger import create_logger

# Initialize logger for this module
logger = create_logger(
    module_name="URLRetriever",
)

# Initialisation du gestionnaire d'erreurs pour ce module
error_handler = ErrorHandler()

HEADERS: Dict[str, str] = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.7",
}

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5
PAGE_TIMEOUT = 20000  # 20 secondes


@handle_errors(
    category=ErrorCategory.NETWORK,
    severity=ErrorSeverity.MEDIUM,
    user_message="Erreur lors de la récupération de l'URL",
)
def retrieve_url(
    row: Dict[str, Any],
    sortie: str = "html",
    encoding_errors: str = "ignore",
    config: Optional[Dict[str, Any]] = None,
    index: int = 0,
    total: int = 0,
) -> Dict[str, Any]:
    """Récupère le contenu d'une URL avec des stratégies robustes et des tentatives multiples.

    Args:
        row (Dict[str, Any]): Dictionnaire contenant les informations de l'URL.
        sortie (str): Format de sortie souhaité ("html" ou "markdown").
        encoding_errors (str): Gestion des erreurs d'encodage.
        config (Optional[Dict[str, Any]]): Configuration supplémentaire.
        index (int): Index de l'URL pour le logging.
        total (int): Nombre total d'URLs pour le logging.

    Returns:
        Dict[str, Any]: Dictionnaire enrichi avec le statut et le contenu de la page.
    """
    row_dict: Dict[str, Any] = dict(row)
    url: str = row.get("url", "")
    identifiant: str = row.get("identifiant", "N/A")

    if not url:
        # ... (gestion de l'URL manquante, inchangée)
        return row_dict

    if total > 0:
        logger.info(f"*{identifiant}* URL {index}/{total} en cours : {url}")
    else:
        logger.debug(f"*{identifiant}* Récupération URL avec Playwright: {url}")

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            with Stealth().use_sync(sync_playwright()) as p:
                browser = p.chromium.launch(headless=True)
                # Configuration du contexte pour paraître plus humain
                context = browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    locale="fr-FR",
                    ignore_https_errors=False,  # Première tentative avec SSL strict
                )
                page = context.new_page()
                # stealth_sync(page) # Plus nécessaire avec la nouvelle méthode
                page.set_extra_http_headers(HEADERS)

                # Stratégie de navigation robuste
                response = page.goto(url, timeout=PAGE_TIMEOUT, wait_until="load")
                logger.debug(
                    f"*{identifiant}* Pause de 5 secondes pour le rendu JavaScript..."
                )
                page.wait_for_timeout(5000)
                html_content = page.content()

                if response and response.status == 200:
                    logger.info(
                        f"*{identifiant}* Récupération réussie (tentative {attempt + 1}/{MAX_RETRIES})"
                    )
                    row_dict["html"] = html_content
                    if sortie == "markdown":
                        from ..utils.HtmlToMarkdown import convert_html_to_markdown

                        row_dict["markdown"] = convert_html_to_markdown(
                            html=html_content, identifiant=identifiant
                        )
                    row_dict.update(statut="ok", code_http=response.status, message="")
                    return row_dict
                elif response:
                    logger.warning(
                        f"*{identifiant}* Erreur HTTP {response.status} pour {url}"
                    )
                    row_dict.update(
                        statut="warning",
                        code_http=response.status,
                        message=f"HTTP error {response.status}",
                    )
                    return row_dict

        except (PlaywrightTimeoutError, PlaywrightError) as e:
            last_error = e
            logger.warning(
                f"*{identifiant}* Tentative {attempt + 1}/{MAX_RETRIES} échouée pour {url}: {type(e).__name__}"
            )
            if attempt < MAX_RETRIES - 1:
                logger.info(
                    f"Nouvelle tentative dans {RETRY_DELAY_SECONDS} secondes..."
                )
                time.sleep(RETRY_DELAY_SECONDS)
            else:
                # Dernière tentative échouée, on essaie en ignorant les erreurs SSL
                logger.warning(
                    f"*{identifiant}* Toutes les tentatives ont échoué. Dernière tentative en ignorant les erreurs SSL."
                )
                try:
                    with Stealth().use_sync(sync_playwright()) as p_no_ssl:
                        browser_no_ssl = p_no_ssl.chromium.launch(headless=True)
                        context_no_ssl = browser_no_ssl.new_context(
                            ignore_https_errors=True,
                            viewport={"width": 1920, "height": 1080},
                            locale="fr-FR",
                        )
                        page_no_ssl = context_no_ssl.new_page()
                        # stealth_sync(page_no_ssl) # Plus nécessaire
                        page_no_ssl.set_extra_http_headers(HEADERS)

                        # Application de la même stratégie de navigation
                        page_no_ssl.goto(url, timeout=PAGE_TIMEOUT, wait_until="load")
                        logger.debug(
                            f"*{identifiant}* Pause de 5 secondes pour le rendu JavaScript (sans SSL)..."
                        )
                        page_no_ssl.wait_for_timeout(5000)
                        html_content = page_no_ssl.content()

                        # Si on arrive ici, c'est un succès
                        logger.info(
                            f"*{identifiant}* Récupération réussie avec la stratégie 'ignore_https_errors'."
                        )
                        row_dict["html"] = html_content
                        row_dict.update(statut="ok", code_http=200, message="")
                        return row_dict
                except (PlaywrightTimeoutError, PlaywrightError) as e_no_ssl:
                    last_error = e_no_ssl

    # Si toutes les tentatives ont échoué
    error_message = (
        str(last_error) if last_error else "Toutes les tentatives ont échoué"
    )
    error_category = ErrorCategory.NETWORK
    error_severity = (
        ErrorSeverity.MEDIUM
        if isinstance(last_error, PlaywrightTimeoutError)
        else ErrorSeverity.HIGH
    )

    error_handler.handle_error(
        exception=last_error or RuntimeError("Échec de la récupération de l'URL"),
        context=error_handler.create_error_context(
            module="URLRetriever",
            function="retrieve_url",
            operation=f"Échec final pour {url}",
            data={"url": url, "identifiant": identifiant, "attempts": MAX_RETRIES},
        ),
        category=error_category,
        severity=error_severity,
    )

    row_dict.update(
        statut="critical" if error_severity == ErrorSeverity.HIGH else "warning",
        message=error_message,
        code_http=0,
    )
    return row_dict
