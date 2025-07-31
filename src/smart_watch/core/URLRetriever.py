from playwright.sync_api import (
    Error as PlaywrightError,
)
from playwright.sync_api import (
    TimeoutError as PlaywrightTimeoutError,
)
from playwright.sync_api import (
    sync_playwright,
)

from ..utils import convert_html_to_markdown
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
    "Accept-Language": "fr-FR,fr;q=0.7",
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
    index: int = 0,
    total: int = 0,
) -> dict:
    """Récupère le contenu d'une URL et le retourne sous forme de dictionnaire.

    Args:
        row (dict): dictionnaire contenant les informations de l'URL et d'autres métadonnées.
        sortie (str): format de sortie souhaité, par défaut "html".
        encoding_errors (str): stratégie de gestion des erreurs d'encodage, par défaut "ignore".
        config (dict, optional): configuration supplémentaire, non utilisée dans cette fonction.
        index (int): index de l'URL dans une liste, utilisé pour le logging.
        total (int): nombre total d'URLs à traiter, utilisé pour le logging.

    Returns:
        dict: dictionnaire contenant :
            - toutes les clés d'entrée du paramètre `row`
            - 'statut' (str) : état de la récupération ('ok', 'warning', 'critical')
            - 'message' (str) : message d'erreur ou d'information
            - 'code_http' (int) : code HTTP de la réponse (0 si non disponible)
            - 'html' (str) : contenu HTML récupéré (si succès)
            - 'markdown' (str) : contenu converti en markdown (si sortie == "markdown" et succès)
    """
    row_dict = dict(row)
    url = row.get("url", "")
    identifiant = row.get("identifiant", "N/A")

    if not url:
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
        if total > 0:
            logger.info(f"*{identifiant}* URL {index}/{total} en cours : {url}")
        else:
            logger.debug(f"*{identifiant}* Récupération URL avec Playwright: {url}")

        # Stratégies SSL/TLS progressives avec Playwright
        # 'low_security' et 'full_mitigation' sont gérés par 'ignore_https_errors=True'
        ssl_strategies = ["default", "no_verify"]
        response = None
        html_content = ""

        with sync_playwright() as p:
            for strategy in ssl_strategies:
                browser = None
                try:
                    browser = p.chromium.launch()
                    ignore_https = strategy == "no_verify"
                    context = browser.new_context(ignore_https_errors=ignore_https)
                    page = context.new_page()
                    page.set_extra_http_headers(HEADERS)

                    # Utilisation de 'networkidle' pour attendre la fin des requêtes réseau,
                    # ce qui est plus fiable pour les pages avec chargement dynamique.
                    response = page.goto(url, timeout=30000, wait_until="networkidle")

                    if response:
                        html_content = page.content()
                        if strategy != "default":
                            logger.debug(
                                f"*{identifiant}* Succès avec la stratégie Playwright '{strategy}'"
                            )
                        break  # Success, exit the loop

                except PlaywrightError as e:
                    error_str = str(e).lower()
                    if "ssl" in error_str or "certificate" in error_str:
                        logger.warning(
                            f"*{identifiant}* Échec avec la stratégie '{strategy}': {e}"
                        )
                        if strategy == ssl_strategies[-1]:
                            raise  # Re-raise if it's the last strategy
                    elif "net::err_too_many_redirects" in error_str:
                        row_dict.update(
                            statut="warning",
                            message="too many redirects",
                            code_http=310,
                        )
                        logger.warning(f"*{identifiant}* Trop de redirections: {url}")
                        return row_dict
                    else:
                        raise  # Re-raise other Playwright errors
                finally:
                    if browser:
                        browser.close()

        if not response:
            raise ValueError(
                "La réponse de Playwright est nulle après toutes les tentatives."
            )

        if response.status != 200:
            row_dict.update(
                statut="warning",
                code_http=response.status,
                message=f"HTTP error {response.status}",
            )
            logger.warning(f"*{identifiant}* Erreur HTTP {response.status} pour {url}")
        else:
            logger.debug(
                f"*{identifiant}* Contenu récupéré : {len(html_content)} caractères"
            )
            row_dict["html"] = html_content
            if sortie == "markdown":
                row_dict["markdown"] = convert_html_to_markdown(
                    html=html_content, identifiant=identifiant
                )

            row_dict.update(statut="ok", code_http=response.status, message="")
            logger.info(f"*{identifiant}* Récupération réussie : {url}")

    except PlaywrightTimeoutError as e:
        error_handler.handle_error(
            exception=e,
            context=error_handler.create_error_context(
                module="URLRetriever",
                function="retrieve_url",
                operation=f"Timeout pour {url}",
                data={"url": url, "timeout": 30000, "identifiant": identifiant},
            ),
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
        )
        row_dict.update(statut="warning", message="Timeout", code_http=0)

    except PlaywrightError as e:
        error_handler.handle_error(
            exception=e,
            context=error_handler.create_error_context(
                module="URLRetriever",
                function="retrieve_url",
                operation=f"Erreur Playwright pour {url}",
                data={"url": url, "identifiant": identifiant},
            ),
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
        )
        row_dict.update(statut="critical", message=str(e), code_http=0)

    return row_dict
