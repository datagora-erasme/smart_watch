import ssl

import urllib3

from ..utils.HtmlToMarkdown import convert_html_to_markdown
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


def _create_ssl_context(strategy: str = "default") -> ssl.SSLContext:
    """Crée un contexte SSL selon la stratégie spécifiée."""
    ctx = ssl.create_default_context()

    if strategy == "no_verify":
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    elif strategy == "low_security":
        ctx.set_ciphers("DEFAULT@SECLEVEL=1")
    elif strategy == "full_mitigation":
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ctx.set_ciphers("DEFAULT@SECLEVEL=1")

    return ctx


def _make_request(url: str, strategy: str = "default") -> urllib3.HTTPResponse:
    """Effectue une requête HTTP avec la stratégie SSL spécifiée."""
    if strategy == "default":
        http = urllib3.PoolManager(timeout=30.0)
    else:
        ssl_context = _create_ssl_context(strategy)
        cert_reqs = (
            ssl.CERT_NONE
            if strategy in ["no_verify", "full_mitigation"]
            else ssl.CERT_REQUIRED
        )
        http = urllib3.PoolManager(
            cert_reqs=cert_reqs, ssl_context=ssl_context, timeout=30.0
        )

    return http.request(
        "GET",
        url,
        headers=HEADERS,
        redirect=True,
        retries=10,
        timeout=30.0,
    )


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

        # Stratégies SSL progressives
        ssl_strategies = ["default", "no_verify", "low_security", "full_mitigation"]
        response = None

        for strategy in ssl_strategies:
            try:
                response = _make_request(url, strategy)
                if strategy != "default":
                    logger.debug(
                        f"[{identifiant}] Succès avec stratégie SSL: {strategy}"
                    )
                break
            except urllib3.exceptions.MaxRetryError as max_retry_err:
                error_str = str(max_retry_err)

                # Gestion spéciale pour les redirections
                if "too many redirects" in error_str:
                    row_dict["statut"] = "warning"
                    row_dict["message"] = "too many redirects"
                    row_dict["code_http"] = 310
                    logger.warning(f"[{identifiant}] Trop de redirections: {url}")
                    return row_dict

                # Si ce n'est pas un problème SSL ou si c'est la dernière stratégie, on relance
                if (
                    not any(
                        ssl_error in error_str
                        for ssl_error in [
                            "CERTIFICATE_VERIFY_FAILED",
                            "DH_KEY_TOO_SMALL",
                        ]
                    )
                    or strategy == ssl_strategies[-1]
                ):
                    raise

        if response.status != 200:
            row_dict["statut"] = "warning"
            row_dict["code_http"] = response.status
            row_dict["message"] = f"HTTP error {response.status}"
            logger.warning(f"[{identifiant}] Erreur HTTP {response.status}: {url}")
        else:
            # Decode content
            content_type = response.headers.get("Content-Type", "")
            encoding = "utf-8"
            if "charset=" in content_type:
                encoding = content_type.split("charset=")[-1].strip()

            html_content = response.data.decode(encoding, errors=encoding_errors)
            logger.debug(
                f"[{identifiant}] Contenu décodé ({encoding}): {len(html_content)} caractères"
            )

            # Stockage du contenu selon le format demandé
            if sortie == "html":
                row_dict["html"] = html_content
            elif sortie == "markdown":
                markdown_content = convert_html_to_markdown(html=html_content)
                # Si la conversion échoue, elle renvoie une chaîne vide.
                # On utilise le HTML comme fallback, préservant l'ancien comportement.
                if not markdown_content and html_content:
                    logger.warning(
                        f"[{identifiant}] La conversion Markdown a échoué (voir logs précédents). Utilisation du HTML brut comme fallback."
                    )
                    row_dict["markdown"] = html_content
                else:
                    row_dict["markdown"] = markdown_content

            # Conversion automatique vers Markdown si HTML disponible
            if (
                row_dict.get("html")
                and row_dict["html"].strip()
                and "markdown" not in row_dict
            ):
                row_dict["markdown"] = convert_html_to_markdown(html=row_dict["html"])

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
