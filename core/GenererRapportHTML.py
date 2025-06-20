import base64
import json
import os
from datetime import datetime

import polars as pl
from jinja2 import Environment, FileSystemLoader


# Fonction personnalisée pour Jinja2 pour convertir en JSON
def to_json(value: any) -> str:
    """
    Convertit une valeur en chaîne JSON encodée en base64.

    Cette fonction prend une valeur de n'importe quel type et la transforme en chaîne JSON,
    puis l'encode en base64 pour éviter les problèmes d'échappement dans les templates HTML.

    Argument :
        value: La valeur à convertir et encoder

    Renvoie :
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
    except Exception:
        # En cas d'erreur, convertir en chaîne puis encoder en base64
        json_str = json.dumps(str(value), ensure_ascii=False, indent=2)
        return base64.b64encode(json_str.encode("utf-8")).decode("ascii")


def generer_rapport_html(
    db_file: str, table_name: str, titre_rapport: str, model_info: dict = None
) -> tuple[str, str]:
    """
    Génère un rapport HTML analysant les URLs stockées dans une base de données SQLite.
    Cette fonction interroge une base de données contenant des informations sur des URLs,
    calcule diverses statistiques (statuts, types de lieux, codes HTTP) et génère un
    rapport HTML formaté à partir d'un template.

    Arguments :
        db_file (str): Chemin vers le fichier de base de données SQLite.
        table_name (str): Nom de la table contenant les données des URLs.
        titre_rapport (str): Titre à afficher dans le rapport généré.
        model_info (dict): Informations sur le modèle LLM utilisé.

    Renvoie :
        tuple[str, str]: Un tuple contenant:
            - Le contenu HTML du rapport généré.
            - Le nom du fichier HTML sauvegardé.

    Notes:
        - Le rapport est sauvegardé dans le répertoire courant avec un nom basé sur la date et l'heure.
        - La fonction utilise un template HTML situé dans le répertoire "../assets" relatif à ce script.
        - Les données sont regroupées par statut (ok, warning, critical, unknown) et par type de lieu.
    """
    # Configuration du moteur de templates
    assets_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "assets"
    )
    env = Environment(loader=FileSystemLoader(assets_dir))

    # Ajouter la fonction personnalisée tojson au template
    env.filters["tojson"] = to_json

    template = env.get_template("ReportTemplate.html")
    simple_template = env.get_template("SimpleReportTemplate.html")

    # Extraction des données depuis la base de données
    uri = f"sqlite:///{db_file}"
    query = """
    SELECT 
        l.type_lieu, 
        l.identifiant, 
        l.nom, 
        l.url, 
        r.statut_url as statut, 
        r.message_url as message, 
        r.llm_horaires_json, 
        r.llm_horaires_osm, 
        r.code_http
    FROM resultats_extraction r
    JOIN lieux l ON r.lieu_id = l.identifiant
    ORDER BY l.identifiant
    """
    df = pl.read_database_uri(query=query, uri=uri, engine="connectorx")

    # Convertir le DataFrame Polars en dictionnaire pour faciliter le traitement
    donnees_urls = df.to_dicts()

    # Traiter les données JSON
    for url in donnees_urls:
        # Convertir llm_horaires_json en objet Python si c'est une chaîne JSON
        if "llm_horaires_json" in url and url["llm_horaires_json"]:
            try:
                if isinstance(url["llm_horaires_json"], str):
                    url["llm_horaires_json"] = json.loads(url["llm_horaires_json"])
            except json.JSONDecodeError:
                # Si ce n'est pas un JSON valide, le garder comme une chaîne
                pass

        # S'assurer que les champs requis existent avec des valeurs par défaut
        url.setdefault("llm_horaires_json", None)
        url.setdefault("llm_horaires_osm", None)
        url.setdefault("code_http", 0)
        url.setdefault("message", "")
        url.setdefault("url", "")
        url.setdefault("nom", "")
        url.setdefault("identifiant", "")
        url.setdefault("type_lieu", "")

    # Calculer les statistiques globales
    total_urls = len(donnees_urls)

    # Compter par statut
    statuts_count = (
        df.group_by("statut").agg(pl.len().alias("count")).to_dict(as_series=False)
    )
    statuts_dict = {
        statut: count
        for statut, count in zip(statuts_count["statut"], statuts_count["count"])
    }

    # Compter par type de lieu
    types_lieu_count = (
        df.group_by("type_lieu").agg(pl.len().alias("count")).to_dict(as_series=False)
    )
    types_lieu_dict = {
        type_lieu: count
        for type_lieu, count in zip(
            types_lieu_count["type_lieu"], types_lieu_count["count"]
        )
    }

    # Compter par code HTTP
    codes_http_count = (
        df.group_by("code_http").agg(pl.len().alias("count")).to_dict(as_series=False)
    )

    stats_globales = {
        "total_urls": total_urls,
    }

    # Définir les statuts et leurs propriétés (simplifié)
    statuts_config = {
        "ok": {
            "nom": "Succès",
            "emoji": "✅",
            "type": "success",
            "description": "URLs avec horaires OSM extraits",
        },
        "error": {
            "nom": "Erreur",
            "emoji": "❌",
            "type": "error",
            "description": "URLs sans horaires OSM (problème d'extraction, URL inaccessible, etc.)",
        },
    }

    # Reclassifier les données selon le nouveau critère : présence d'horaires OSM
    for url in donnees_urls:
        # Reclassifier basé uniquement sur la présence d'horaires OSM
        if url.get("llm_horaires_osm") and url["llm_horaires_osm"].strip():
            url["statut"] = "ok"
        else:
            url["statut"] = "error"

    # Regrouper les URLs par statut
    statuts_disponibles = []
    for statut_code, config in statuts_config.items():
        urls_du_statut = [u for u in donnees_urls if u["statut"] == statut_code]
        if urls_du_statut:
            statuts_disponibles.append(
                {
                    "code": statut_code,
                    "nom": config["nom"],
                    "emoji": config["emoji"],
                    "type": config["type"],
                    "description": config["description"],
                    "count": len(urls_du_statut),
                    "urls": urls_du_statut,
                }
            )

    # Regroupement par type de lieu
    types_lieu_stats = []
    for type_lieu, count in types_lieu_dict.items():
        types_lieu_stats.append(
            {
                "type": type_lieu,
                "count": count,
            }
        )

    # Regroupement par code HTTP avec tri
    codes_http_stats = []
    for code_http, count in zip(
        codes_http_count["code_http"], codes_http_count["count"]
    ):
        codes_http_stats.append(
            {
                "code": code_http,
                "count": count,
            }
        )
    codes_http_stats.sort(key=lambda x: x["code"])

    # Construire le titre enrichi avec les informations du modèle
    titre_enrichi = titre_rapport
    if model_info:
        modele = model_info.get("modele", "")
        base_url = model_info.get("base_url", "")
        fournisseur = model_info.get("fournisseur", "")

        if modele:
            titre_enrichi += f" - Modèle: {modele}"
        if base_url:
            titre_enrichi += f" - URL: {base_url}"
        elif fournisseur:
            titre_enrichi += f" - Fournisseur: {fournisseur}"

    # Données à passer au template
    donnees_template = {
        "titre_rapport": titre_rapport,  # Titre principal sans modification
        "date_generation": datetime.now().strftime("%d/%m/%Y à %H:%M"),
        "stats_globales": stats_globales,
        "statuts_disponibles": statuts_disponibles,
        "types_lieu_stats": types_lieu_stats,
        "codes_http_stats": codes_http_stats,
        "model_info": model_info,  # Ajouter les infos du modèle pour usage dans le template
    }

    # Génération du HTML simple pour l'email
    resume_html = simple_template.render(**donnees_template)

    # Génération du rapport HTML complet
    html_content = template.render(**donnees_template)

    # Sauvegarde du fichier
    fichier_rapport_html = f"rapport_urls_{datetime.now().strftime('%Y%m%d_%H%M')}.html"
    with open(fichier_rapport_html, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Rapport généré : {fichier_rapport_html}")
    return resume_html, fichier_rapport_html


# Exemple d'utilisation de la fonction
if __name__ == "__main__":
    from pathlib import Path

    SCRIPT_DIR = Path(r"C:\Users\beranger\Documents\GitHub\smart_watch\data")
    DATA_DIR = SCRIPT_DIR
    NOM_FIC = "alerte_modif_horaire_lieu_devstral"
    DB_FILE = DATA_DIR / f"{NOM_FIC}.db"

    # générer le rapport HTML à partir de la base de données
    html_content, nom_fichier = generer_rapport_html(
        db_file=DB_FILE,
        table_name="_".join(NOM_FIC.split("_")[:-1]),
        titre_rapport="Rapport de vérification des URLs",
    )
