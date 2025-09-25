# Récupérateur de contenu URL pour le projet smart_watch
# Documentation: https://datagora-erasme.github.io/smart_watch/source/modules/core/URLRetriever.html
import time
from typing import Any, Dict, Optional

from playwright.sync_api import (
    Error as PlaywrightError,
)
from playwright.sync_api import (
    Page,
    sync_playwright,
)
from playwright.sync_api import (
    TimeoutError as PlaywrightTimeoutError,
)
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


def _expand_all_accordions(page: Page, identifiant: str):
    """
    Force l'affichage des contenus d'accordions identifiés sur une page Playwright.
    Cette fonction tente d'ouvrir et de rendre visibles les panneaux d'accordions
    en ciblant une liste modérée de sélecteurs courants (IDs, classes CSS et
    rôles ARIA). Pour chaque élément trouvé, elle applique via JavaScript des
    modifications de style (display, visibility, opacity, height, maxHeight,
    overflow), supprime certaines classes masquantes courantes et force
    l'attribut ARIA approprié afin de révéler le contenu. Les éléments déjà
    traités sont évités grâce à un suivi par identifiant. Les erreurs
    locales sur des éléments ou des sélecteurs sont consignées mais n'interrompent
    pas le déroulement global.
    Args:
        page (Page): Instance Playwright Page sur laquelle opérer (par ex.
            playwright.sync_api.Page). L'objet est utilisé pour localiser les
            éléments et exécuter le JavaScript d'altération du DOM.
        identifiant (str): Chaîne utilisée pour le contexte des logs afin de
            faciliter le traçage des actions et des erreurs.
    Returns:
        None: Aucun résultat n'est retourné. La fonction applique des effets
        secondaires sur la page et journalise le nombre d'éléments forcés à
        l'affichage.
    Raises:
        Aucun: Les exceptions locales (par sélecteur ou par élément) sont capturées
        et consignées. En pratique, la fonction ne propage pas d'exceptions
        issues des opérations sur les éléments du DOM.
    """
    logger.debug(
        f"*{identifiant}* Recherche et affichage forcé du contenu des accordions..."
    )

    try:
        # Liste ciblée de sélecteurs pour les contenus d'accordions les plus courants
        accordion_content_selectors = [
            # --- Sélecteurs basés sur les IDs (les plus fiables) ---
            '[id*="accordion-item-content"]',  # ACF/WordPress
            '[id*="accordion-content"]',  # Pattern générique
            '[id*="collapse"]',  # Bootstrap
            # --- Sélecteurs basés sur les classes CSS (courants) ---
            ".accordion-item-content",  # Standard moderne
            ".accordion-content",  # Pattern simple
            ".accordion-body",  # Bootstrap 5
            ".collapse",  # Bootstrap (tous)
            ".panel-collapse",  # Bootstrap 3
            ".collapsible-content",  # Materialize CSS
            # --- Sélecteurs ARIA ciblés ---
            '[role="tabpanel"]',  # ARIA standard
            '[aria-labelledby*="accordion"]',  # Référencé par accordion
        ]

        total_revealed = 0
        processed_elements = (
            set()
        )  # Pour éviter de traiter le même élément plusieurs fois

        for selector in accordion_content_selectors:
            try:
                # Trouver tous les éléments de contenu correspondants
                content_elements = page.locator(selector).all()
                count = len(content_elements)

                if count > 0:
                    logger.debug(
                        f"*{identifiant}* Trouvé {count} panneau(x) de contenu avec le sélecteur '{selector}'"
                    )

                    # Forcer l'affichage de chaque panneau via JavaScript
                    for i, element in enumerate(content_elements):
                        try:
                            # Obtenir un identifiant unique pour éviter les doublons
                            element_id = (
                                element.get_attribute("id") or f"{selector}_{i}"
                            )

                            if element_id in processed_elements:
                                continue  # Skip si déjà traité

                            processed_elements.add(element_id)

                            element.evaluate(
                                """
                                element => {
                                    // Styles d'affichage essentiels
                                    element.style.display = 'block';
                                    element.style.visibility = 'visible';
                                    element.style.opacity = '1';
                                    element.style.height = 'auto';
                                    element.style.maxHeight = 'none';
                                    element.style.overflow = 'visible';
                                    
                                    // Supprimer les classes qui masquent le contenu
                                    const hiddenClasses = ['collapsed', 'hidden', 'hide'];
                                    hiddenClasses.forEach(cls => element.classList.remove(cls));
                                    
                                    // Forcer l'attribut ARIA
                                    element.setAttribute('aria-hidden', 'false');
                                }
                            """,
                                timeout=5000,
                            )  # Timeout 5 secondes
                            total_revealed += 1
                        except Exception as e:
                            logger.debug(
                                f"*{identifiant}* Impossible de modifier l'élément {i + 1}: {type(e).__name__}"
                            )

            except Exception as e:
                logger.debug(
                    f"*{identifiant}* Erreur avec le sélecteur '{selector}': {e}"
                )

        if total_revealed > 0:
            logger.info(
                f"*{identifiant}* {total_revealed} panneau(x) de contenu ont été forcés à l'affichage."
            )
            # Attendre que les modifications CSS prennent effet
            page.wait_for_timeout(500)
        else:
            logger.warning(
                f"*{identifiant}* Aucun panneau de contenu d'accordions n'a été trouvé pour l'affichage forcé."
            )

    except Exception as e:
        logger.warning(
            f"*{identifiant}* Échec de l'affichage forcé: {type(e).__name__}: {e}"
        )


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
    """Récupère le contenu d'une URL avec des stratégies et tentatives multiples.

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
                page.set_extra_http_headers(HEADERS)

                # Navigation vers l'URL avec timeout
                response = page.goto(url, timeout=PAGE_TIMEOUT, wait_until="load")

                # Expansion des volets interactifs
                _expand_all_accordions(page, identifiant)

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
                        page_no_ssl.set_extra_http_headers(HEADERS)

                        # Application de la même stratégie de navigation
                        page_no_ssl.goto(url, timeout=PAGE_TIMEOUT, wait_until="load")

                        # Expansion des volets interactifs (fallback sans SSL)
                        _expand_all_accordions(page_no_ssl, identifiant)

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

    # Gestion des erreurs spécifiques
    if "ERR_NAME_NOT_RESOLVED" in str(last_error):
        return {
            "statut": "erreur",
            "message": "Domaine non résolu (DNS)",
            "code_http": 0,
            "markdown_brut": "",
            "erreurs_pipeline": f"Impossible de résoudre le domaine: {url}",
        }

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
