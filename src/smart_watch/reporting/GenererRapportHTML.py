"""
Générateur de rapport HTML pour l'analyse des extractions d'horaires.

Ce module génère des rapports HTML détaillés à partir des données stockées
en base de données, avec support des comparaisons d'horaires.
"""

import base64
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

from jinja2 import Environment, FileSystemLoader

from ..core.DatabaseManager import DatabaseManager
from ..core.ErrorHandler import ErrorCategory, ErrorSeverity, handle_errors
from ..core.Logger import create_logger

# Initialize logger for this module
logger = create_logger(
    module_name="GenererRapportHTML",
)


def to_json(value) -> Optional[str]:
    """
    Convertit une valeur en chaîne JSON encodée en base64.

    Cette fonction prend une valeur de n'importe quel type et la transforme en chaîne JSON,
    puis l'encode en base64 pour éviter les problèmes d'échappement dans les templates HTML.

    Args:
        value: La valeur à convertir et encoder

    Returns:
        str: Chaîne JSON encodée en base64, ou None si la valeur d'entrée est None
    """
    if value is None:
        return None

    try:
        # Si c'est déjà une chaîne JSON valide, la retourner
        if isinstance(value, str):
            # Vérifier si c'est un JSON valide
            json.loads(value)
            json_str = value
        else:
            # Sinon, essayer de convertir en JSON avec ensure_ascii=False pour préserver les caractères UTF-8
            json_str = json.dumps(value, ensure_ascii=False, indent=2)

        # Encoder en base64 en s'assurant que l'UTF-8 est préservé
        return base64.b64encode(json_str.encode("utf-8")).decode("ascii")
    except Exception as e:
        logger.warning(f"Erreur conversion JSON pour template: {e}")
        # En cas d'erreur, convertir en chaîne puis encoder en base64
        json_str = json.dumps(str(value), ensure_ascii=False, indent=2)
        return base64.b64encode(json_str.encode("utf-8")).decode("ascii")


@handle_errors(
    category=ErrorCategory.UNKNOWN,
    severity=ErrorSeverity.HIGH,
    user_message="Erreur lors de la génération du rapport HTML",
)
def generer_rapport_html(
    db_file: str,
    titre_rapport: str,
    model_info: Optional[Dict] = None,
) -> Tuple[str, str]:
    """
    Génère un rapport HTML complet à partir des données de la base SQLite.

    Args:
        db_file: Chemin vers le fichier de base de données SQLite.
        titre_rapport: Titre du rapport.
        model_info: Informations sur le modèle utilisé.

    Returns:
        Tuple contenant (résumé_html, chemin_fichier_html)

    Raises:
        FileNotFoundError: Si le fichier de base de données n'existe pas.
        RuntimeError: Si les templates ne sont pas trouvés.
    """
    logger.info(f"Génération rapport HTML depuis: {db_file}")

    # Vérification de l'existence de la base de données
    db_path = Path(db_file)
    if not db_path.exists():
        raise FileNotFoundError(f"Base de données non trouvée: {db_file}")

    # Configuration du moteur de templates
    templates_dir = Path(__file__).parent.parent / "assets" / "templates"
    if not templates_dir.exists():
        raise FileNotFoundError(f"Répertoire des templates non trouvé: {templates_dir}")

    env = Environment(loader=FileSystemLoader(str(templates_dir)))
    env.filters["tojson"] = to_json

    try:
        template = env.get_template("ReportTemplate.html")
        simple_template = env.get_template("SimpleReportTemplate.html")
        logger.debug("Templates chargés avec succès")
    except Exception as e:
        raise RuntimeError(f"Erreur chargement templates: {e}")

    # Extraction des données depuis la base de données
    db_manager = DatabaseManager(db_file=db_file)
    donnees_urls = _extract_data_from_database(db_manager)
    logger.info(f"Données extraites : {len(donnees_urls)} enregistrements")

    # Extraire les données de l'exécution
    execution_data = _extract_execution_data(db_manager)

    # Traitement des données
    _process_data(donnees_urls)

    # Classification et calcul des statistiques
    stats_globales, statuts_disponibles = _group_by_status_and_calculate_stats(
        donnees_urls
    )
    types_lieu_stats = _calculate_type_stats(donnees_urls)
    codes_http_stats = _calculate_http_stats(donnees_urls)

    # Préparation des données pour le template
    donnees_template = {
        "titre_rapport": titre_rapport,
        "date_generation": datetime.now().strftime("%d/%m/%Y à %H:%M"),
        "stats_globales": stats_globales,
        "statuts_disponibles": statuts_disponibles,
        "types_lieu_stats": types_lieu_stats,
        "codes_http_stats": codes_http_stats,
        "model_info": model_info,
        "execution_data": execution_data,
    }

    # Génération des rapports
    try:
        resume_html = simple_template.render(**donnees_template)
        html_content = template.render(**donnees_template)
        logger.debug("Templates rendus avec succès")
    except Exception as e:
        raise RuntimeError(f"Erreur rendu template: {e}")

    # Sauvegarde du fichier
    fichier_rapport_html = _save_report(html_content)

    logger.info(f"Rapport généré avec succès: {fichier_rapport_html}")
    return resume_html, fichier_rapport_html


@handle_errors(
    category=ErrorCategory.DATABASE,
    severity=ErrorSeverity.HIGH,
    user_message="Erreur lors de l'extraction des données d'exécution.",
    default_return=None,
)
def _extract_execution_data(db_manager: DatabaseManager) -> Optional[dict]:
    """Extrait les données agrégées de toutes les exécutions."""
    query = """
    SELECT SUM(llm_consommation_execution) as llm_consommation_execution
    FROM executions 
    """
    logger.debug(f"Exécution de la requête : {query}")
    results = db_manager.execute_query(query)
    logger.debug(f"Données extraites : {len(results)} enregistrements")
    if results and len(results) > 0 and results[0][0] is not None:
        # results est une liste de tuples, on convertit en dict,
        # et on multiplie par 1000 pour avoir la consommation en g et pas en kg
        return {"llm_consommation_execution": results[0][0] * 1000}
    return None


@handle_errors(
    category=ErrorCategory.DATABASE,
    severity=ErrorSeverity.HIGH,
    user_message="Erreur lors de l'extraction des données depuis la base.",
    default_return=[],
)
def _extract_data_from_database(db_manager: DatabaseManager) -> list:
    """Extrait les données depuis la base de données."""
    query = """
    SELECT 
        l.type_lieu, 
        l.identifiant, 
        l.nom, 
        l.url, 
        l.horaires_data_gl,
        r.statut_url AS statut, 
        r.message_url AS message, 
        r.markdown_brut,
        r.markdown_nettoye,
        r.markdown_filtre,
        r.llm_horaires_json, 
        r.llm_horaires_osm, 
        r.code_http,
        r.horaires_identiques,
        r.differences_horaires,
        r.erreurs_pipeline,
        r.llm_consommation_requete
    FROM resultats_extraction AS r 
    JOIN lieux AS l ON r.lieu_id = l.identifiant 
    ORDER BY l.identifiant
    """
    logger.debug(f"Exécution de la requête : {query}")
    results = db_manager.execute_query(query)
    logger.debug(f"Données extraites : {len(results)} enregistrements")
    # Conversion en liste de dicts (en supposant que les colonnes sont fixes)
    columns = [
        "type_lieu",
        "identifiant",
        "nom",
        "url",
        "horaires_data_gl",
        "statut",
        "message",
        "markdown_brut",
        "markdown_nettoye",
        "markdown_filtre",
        "llm_horaires_json",
        "llm_horaires_osm",
        "code_http",
        "horaires_identiques",
        "differences_horaires",
        "erreurs_pipeline",
        "llm_consommation_requete",
    ]
    return [dict(zip(columns, row)) for row in results]


def _process_data(donnees_urls: list) -> None:
    """Traite et normalise les données extraites."""
    for url in donnees_urls:
        try:
            # Multiplier la consommation par 1000 pour avoir des g et pas de kg
            if url.get("llm_consommation_requete") is not None:
                url["llm_consommation_requete"] *= 1000

            # Convertir llm_horaires_json en objet Python si c'est une chaîne JSON
            if "llm_horaires_json" in url and url["llm_horaires_json"]:
                if isinstance(url["llm_horaires_json"], str) and not url[
                    "llm_horaires_json"
                ].startswith("Erreur"):
                    try:
                        url["llm_horaires_json"] = json.loads(url["llm_horaires_json"])
                    except json.JSONDecodeError:
                        logger.warning(
                            f"*{url.get('identifiant', 'inconnu')}* JSON invalide pour '{url.get('nom', 'inconnu')}'"
                        )

            # Créer le champ comparaison_horaires pour compatibilité avec le template
            _create_comparison_field(url)

            # Traiter la chaîne d'erreurs pour affichage
            _process_error_chain(url)

            # S'assurer que les champs requis existent avec des valeurs par défaut
            _set_default_fields(url)

            # NOUVELLE FONCTION : Enrichir le message avec les détails d'erreur
            _enrich_error_message(url)

        except Exception as e:
            logger.warning(
                f"*{url.get('identifiant', 'inconnu')}* Erreur traitement données pour '{url.get('nom', 'inconnu')}' : {e}"
            )


def _enrich_error_message(url: dict) -> None:
    """Enrichit le message d'erreur avec les détails pertinents selon le type d'erreur."""
    statut = url.get("statut", "")
    current_message = url.get("message", "")
    erreurs_pipeline = url.get("erreurs_pipeline", "")

    # Pour les erreurs d'accès, utiliser le message spécifique
    if statut == "access_error":
        if current_message and current_message not in ["", "-"]:
            # Le message est déjà informatif (ex: "URL non fournie", "Domaine non résolu")
            pass
        elif erreurs_pipeline:
            # Utiliser le premier niveau d'erreur de la pipeline
            url["message"] = (
                erreurs_pipeline.split("\n")[0]
                if "\n" in erreurs_pipeline
                else erreurs_pipeline
            )
        else:
            url["message"] = "Accès impossible"

    # Pour les erreurs d'extraction, combiner le message et la première erreur
    elif statut == "extraction_error":
        if erreurs_pipeline and not current_message.startswith("Erreur"):
            # Extraire la première erreur significative
            first_error = (
                erreurs_pipeline.split(" | ")[0]
                if " | " in erreurs_pipeline
                else erreurs_pipeline
            )
            if first_error and len(first_error) < 100:  # Éviter les messages trop longs
                url["message"] = first_error
            else:
                url["message"] = "Extraction échouée"
        elif not current_message or current_message in ["", "-"]:
            url["message"] = "Extraction échouée"

    # Pour les erreurs de comparaison
    elif statut == "compare_error":
        if not current_message or current_message in ["", "-"]:
            url["message"] = "Comparaison impossible"


def _process_error_chain(url: dict) -> None:
    """Traite la chaîne d'erreurs pour l'affichage dans le rapport."""
    erreurs_pipeline = url.get("erreurs_pipeline", "")

    if erreurs_pipeline:
        # Parser les erreurs individuelles
        erreurs_list = erreurs_pipeline.split(" | ")
        url["erreurs_formatees"] = erreurs_list
        url["nombre_erreurs"] = len(erreurs_list)

        # Créer un résumé court pour l'affichage en tableau
        if len(erreurs_list) == 1:
            url["erreurs_resume"] = erreurs_list[0]
        else:
            url["erreurs_resume"] = (
                f"{erreurs_list[0]} (et {len(erreurs_list) - 1} autre{'s' if len(erreurs_list) > 2 else ''})"
            )
    else:
        url["erreurs_formatees"] = []
        url["nombre_erreurs"] = 0
        url["erreurs_resume"] = ""


def _create_comparison_field(url: dict) -> None:
    """Crée le champ de comparaison pour le template."""
    horaires_identiques = url.get("horaires_identiques")
    differences_horaires = url.get("differences_horaires", "")
    erreurs_resume = url.get("erreurs_resume", "")

    if horaires_identiques is None:
        # Ajouter les erreurs si disponibles
        if erreurs_resume:
            url["comparaison_horaires"] = f"Non comparé - {erreurs_resume}"
        elif differences_horaires:
            url["comparaison_horaires"] = differences_horaires
        else:
            url["comparaison_horaires"] = "Non comparé"
    elif horaires_identiques == 1:
        url["comparaison_horaires"] = "IDENTIQUE - Aucune différence détectée"
    elif horaires_identiques == 0:
        url["comparaison_horaires"] = f"DIFFÉRENT - {differences_horaires}"
    else:
        url["comparaison_horaires"] = (
            differences_horaires if differences_horaires else "Erreur de comparaison"
        )


def _set_default_fields(url: dict) -> None:
    """Définit les valeurs par défaut pour les champs requis."""
    defaults = {
        "llm_horaires_json": None,
        "llm_horaires_osm": None,
        "horaires_data_gl": None,
        "code_http": 0,
        "message": "",
        "url": "",
        "nom": "",
        "identifiant": "",
        "type_lieu": "",
        "markdown_brut": "",
        "markdown_nettoye": "",
        "markdown_filtre": "",
        "erreurs_pipeline": "",
        "erreurs_formatees": [],
        "nombre_erreurs": 0,
        "erreurs_resume": "",
        "llm_consommation_requete": 0.0,
    }

    for field, default_value in defaults.items():
        url.setdefault(field, default_value)


def _group_by_status_and_calculate_stats(donnees_urls: list) -> tuple[dict, list]:
    """
    Groupe les URLs par statut et calcule les statistiques globales en une seule passe.
    Ceci garantit la cohérence entre les catégories et les comptes.
    """
    # Configuration des statuts
    statuts_config = {
        "success": {
            "nom": "Succès",
            "emoji": "✅",
            "type": "success",
            "description": "URLs accessibles avec horaires OSM extraits et comparaison réussie (horaires identiques)",
        },
        "schedule_diff": {
            "nom": "Différences horaires",
            "emoji": "⚠️",
            "type": "warning",
            "description": "URLs accessibles avec horaires extraits mais différences détectées lors de la comparaison",
        },
        "compare_error": {
            "nom": "Erreurs de comparaison",
            "emoji": "❓",
            "type": "error",
            "description": "Comparaison impossible ou non effectuée (ex: format de données incompatible)",
        },
        "access_error": {
            "nom": "Erreurs d'accès",
            "emoji": "⛔",
            "type": "error",
            "description": "URLs inaccessibles, codes d'erreur HTTP, problèmes de connexion ou contenu indisponible",
        },
        "extraction_error": {
            "nom": "Erreurs d'extraction",
            "emoji": "❌",
            "type": "error",
            "description": "URLs accessibles mais échec de l'extraction LLM (source non trouvée) ou de la conversion OSM",
        },
    }

    # Classification et comptage
    for url in donnees_urls:
        # Critère 1: Vérifier l'accessibilité de l'URL
        url_accessible = url.get("statut") == "ok" and url.get("code_http", 0) in range(
            200, 300
        )

        # Critère 2: Vérifier si la source a été trouvée par le LLM
        llm_json = url.get("llm_horaires_json", {})
        source_found_llm = True
        if isinstance(llm_json, dict):
            source_found_llm = llm_json.get("extraction_info", {}).get(
                "source_found", True
            )

        # Critère 3: Vérifier la présence d'horaires de référence
        has_reference_hours = url.get("horaires_data_gl") and not url.get(
            "horaires_data_gl", ""
        ).startswith("Erreur")

        # Critère 4: Vérifier la présence d'horaires LLM OSM extraits
        has_osm_hours = (
            url.get("llm_horaires_osm")
            and url["llm_horaires_osm"].strip()
            and not url["llm_horaires_osm"].startswith("Erreur")
        )

        # Critère 5: Vérifier le résultat de la comparaison
        comparison_result = url.get("horaires_identiques")

        # Classification hiérarchique
        if comparison_result == 1:
            url["statut"] = "success"
        elif comparison_result == 0:
            url["statut"] = "schedule_diff"
        elif not url_accessible:
            url["statut"] = "access_error"
        elif not source_found_llm or not has_osm_hours or not has_reference_hours:
            url["statut"] = "extraction_error"
        else:  # comparison_result is None et les autres conditions sont fausses
            url["statut"] = "compare_error"

    # Regroupement et calcul des statistiques
    statuts_disponibles = []
    ordre_statuts = [
        "success",
        "schedule_diff",
        "compare_error",
        "extraction_error",
        "access_error",
    ]
    stats = {
        "total_urls": len(donnees_urls),
        "comparisons_done": 0,
        "comparisons_identical": 0,
        "comparisons_different": 0,
        "comparisons_not_done": 0,
    }

    for statut_code in ordre_statuts:
        config = statuts_config[statut_code]
        urls_du_statut = [u for u in donnees_urls if u["statut"] == statut_code]
        count = len(urls_du_statut)

        if count > 0:
            statuts_disponibles.append(
                {
                    "code": statut_code,
                    "nom": config["nom"],
                    "emoji": config["emoji"],
                    "type": config["type"],
                    "description": config["description"],
                    "count": count,
                    "urls": urls_du_statut,
                }
            )
        # Mise à jour des statistiques globales basées sur la classification
        if statut_code == "success":
            stats["comparisons_identical"] += count
        elif statut_code == "schedule_diff":
            stats["comparisons_different"] += count

    stats["comparisons_done"] = (
        stats["comparisons_identical"] + stats["comparisons_different"]
    )
    stats["comparisons_not_done"] = stats["total_urls"] - stats["comparisons_done"]

    return stats, statuts_disponibles


def _calculate_type_stats(donnees_urls: list) -> list:
    """Calcule les statistiques par type de lieu."""
    type_counts = {}
    for url in donnees_urls:
        type_lieu = url.get("type_lieu", "Non défini")
        type_counts[type_lieu] = type_counts.get(type_lieu, 0) + 1

    return [
        {"type": type_lieu, "count": count} for type_lieu, count in type_counts.items()
    ]


def _calculate_http_stats(donnees_urls: list) -> list:
    """Calcule les statistiques par code HTTP."""
    code_counts = {}
    for url in donnees_urls:
        code_http = url.get("code_http", 0)
        code_counts[code_http] = code_counts.get(code_http, 0) + 1

    return sorted(
        [{"code": code, "count": count} for code, count in code_counts.items()],
        key=lambda x: x["code"],
    )


def _save_report(html_content: str) -> str:
    """Sauvegarde le rapport HTML et retourne le nom du fichier."""
    try:
        fichier_rapport_html = (
            f"Rapport_SmartWatch_{datetime.now().strftime('%Y%m%d_%H%M')}.html"
        )

        with open(fichier_rapport_html, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.debug(f"Rapport sauvegardé: {fichier_rapport_html}")
        return fichier_rapport_html

    except Exception as e:
        logger.error(f"Erreur sauvegarde rapport: {e}")
        raise RuntimeError(f"Erreur lors de la sauvegarde: {e}")
