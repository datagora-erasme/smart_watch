import re
import ssl

import urllib3

from utils.HtmlToMarkdown import HtmlToMarkdown

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


def retrieve_url(
    row: dict,
    sortie: str = "html",
    encoding_errors: str = "ignore",
    char_replacements: dict = None,
) -> dict:
    """
    Récupère le contenu HTML d'une URL spécifiée dans un dictionnaire de ligne, gère les erreurs SSL et HTTP,
    et convertit le contenu éventuel en Markdown.

    Arguments :
        row (dict): Dictionnaire représentant un enregistrement contenant au moins la clé "url".
        sortie (str, optionnel): Type de sortie souhaité, "html" ou "markdown". Par défaut "html".
        encoding_errors (str, optionnel): Stratégie de gestion des erreurs lors du décodage du contenu. Par défaut "ignore".
        char_replacements (dict, optionnel): Table de remplacement {source: cible}. Par défaut None.

    Renvoie :
        dict: Dictionnaire enrichi avec le statut, le code HTTP, le message d'erreur éventuel,
                et le contenu HTML ou Markdown selon la sortie demandée.
    """
    row_dict = dict(row)
    url = row.get("url", "")

    if not url:
        row_dict["statut"] = "critical"
        row_dict["message"] = "Aucune URL n'a été fournie"
        row_dict["code_http"] = 0
        print("❌ Erreur : Aucune URL n'a été fournie")
        return row_dict

    try:
        print(f"\nFetching HTML content from {url}")

        # First try with normal SSL verification, but NO automatic retries
        try:
            http = urllib3.PoolManager(
                timeout=30.0
            )  # Removed retries to catch original exceptions
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
            print(
                f"ℹ️  Erreur lors du GET initial (avec gestion des certificats): {error_str}"
            )

            if "too many redirects" in error_str:
                row_dict["statut"] = "warning"
                row_dict["message"] = "too many redirects"
                row_dict["code_http"] = 20
                print(f"⚠️  Warning: Too many redirects for {url}")
                return row_dict
            elif "CERTIFICATE_VERIFY_FAILED" in error_str:
                print(
                    "ℹ️  Detected specific error: CERTIFICATE_VERIFY_FAILED. Retrying with disabled certificate verification"
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
                print(
                    "ℹ️  Detected specific error: DH_KEY_TOO_SMALL. Retrying with lower SSL security level"
                )
                # Try with lower security level
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
                # For other SSL errors, try with both mitigations
                print(
                    "ℹ️  Retrying with disabled certificate verification and lower SSL security level"
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
            print(f"⚠️ Warning: HTTP error {response.status} from {url}")
        else:
            # Décoder avec l'encodage précisé dans l'en-tête de la réponse
            content_type = response.headers.get("Content-Type", "")
            encoding = None
            if "charset=" in content_type:
                encoding = content_type.split("charset=")[-1].strip()
                print(f"ℹ️  Detected encoding from Content-Type: {encoding}")
            else:
                encoding = "utf-8"  # Default to utf-8 if no charset is found
                print(
                    "ℹ️  No charset detected in Content-Type header, defaulting to utf-8"
                )

            html_content = response.data.decode(encoding, errors=encoding_errors)
            print(f"✅ Successfully decoded using {encoding}")

            if sortie == "html":
                row_dict[sortie] = html_content
            elif sortie == "markdown":
                converter = HtmlToMarkdown(
                    html=html_content, library_type="bs4", bs4_parser="lxml"
                )
                try:
                    markdown_content = converter.convert()
                    # Épuration des sauts de ligne en double
                    markdown_content = re.sub(r"\n{3,}", "\n\n", markdown_content)
                    # Remplacement des caractères selon la table si spécifiée
                    if char_replacements:
                        markdown_content = _apply_char_replacements(
                            markdown_content, char_replacements
                        )
                    row_dict[sortie] = markdown_content
                except Exception as e:
                    print(f"❌ Error converting HTML to Markdown: {str(e)}")
                    row_dict[sortie] = html_content

            # Convert HTML to Markdown if HTML content is available
            if row_dict.get("html") and row_dict["html"].strip():
                converter = HtmlToMarkdown(
                    html=row_dict["html"], library_type="bs4", bs4_parser="lxml"
                )
                markdown_content = converter.convert()
                # Remplacement des caractères selon la table si spécifiée
                if char_replacements:
                    markdown_content = _apply_char_replacements(
                        markdown_content, char_replacements
                    )
                row_dict["markdown"] = markdown_content

            row_dict["statut"] = "ok"
            row_dict["code_http"] = response.status
            row_dict["message"] = ""
            print(f"✅ Successfully fetched HTML content from {url}")
    except urllib3.exceptions.TimeoutError:
        row_dict["statut"] = "warning"
        row_dict["code_http"] = response.status
        row_dict["message"] = "site inaccessible"
        print(f"⚠️ Warning: Site inaccessible (timeout after 30 seconds) from {url}")
    except Exception as err:
        error_str = str(err)
        row_dict["statut"] = "critical"
        row_dict["code_http"] = 10
        row_dict["message"] = error_str
        print(f"❌ Error fetching content from {url}: {error_str}")

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
