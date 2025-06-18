###############################################################
#                         IMPORTS                             #
###############################################################
# Imports standards
import concurrent.futures
import json
import os
import time
from datetime import datetime
from pathlib import Path

# Libraries externes
import polars as pl
from dotenv import dotenv_values, load_dotenv

# Librairies du projet
# from assets.model import Horaires
from core.DatabaseManager import DatabaseManager
from core.EnvoyerMail import envoyer_mail_html
from core.GenererRapportHTML import generer_rapport_html
from core.GetPrompt import get_prompt
from core.LLMClient import (
    get_mistral_tool_format,
    get_structured_response_format,
    llm_mistral,
    llm_openai,
)
from core.URLRetriever import retrieve_url
from utils.CSVToPolars import CSVToPolars
from utils.CustomJsonToOSM import OSMConverter

# Initialiser le convertisseur
converter = OSMConverter()


###############################################################
#                        VARIABLES                            #
###############################################################
# Remettre à zéro les variables d'environnement,
# pour éviter les conflits avec les anciennes valeurs
os.environ.pop("API_KEY_OPENAI", None)
os.environ.pop("API_KEY_MISTRAL", None)
dotenv_vars = dotenv_values()
for key in dotenv_vars.keys():
    os.environ.pop(key, None)

# Chargement des variables d'environnement depuis le fichier .env
load_dotenv()

# Répertoires et fichiers
SCRIPT_DIR = Path(__file__).parent.resolve()

# Profil d'utilisation
DATA_DIR = SCRIPT_DIR / "data"

# Fichier CSV contenant les URL
NOM_FIC = "alerte_modif_horaire_lieu_unique"
NOM_FIC = "alerte_modif_horaire_lieu"

CSV_FILE = DATA_DIR / f"{NOM_FIC}.csv"

# Colonnes à ajouter au dataframe pour stocker les résultats
COLS_SUPPL = [
    "code_http",
    "statut",
    "message",
    "markdown",
    "horaires_llm",
    "horaires_osm",
]

# Nombre de threads concurrents pour le traitement des URL
NB_THREADS_URL = 100

# Remplacements de caractères pour le markdown (optionnel)
CHAR_REPLACEMENTS = {
    "-": " ",
    "*": " ",
    "_": " ",
    "`": " ",
    "+": " ",
    "\\": " ",
    "\n\n\n": "\n",
    "\n\n\n\n": "\n",
}

# Température pour les appels LLM
TEMPERATURE = 0

# Délai entre les appels LLM (en secondes)
DELAI_ENTRE_APPELS = 2
DELAI_EN_CAS_ERREUR = 600

# timeout pour les appels LLM (en secondes)
# mettre plus que DELAI_EN_CAS_ERREUR pour éviter les timeouts
TIMEOUT = DELAI_EN_CAS_ERREUR + 10

# Envoi mail
MAIL_EMETTEUR = os.getenv("MAIL_EMETTEUR")
MAIL_RECEPTEUR = os.getenv("MAIL_RECEPTEUR")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_PORT = int(SMTP_PORT) if SMTP_PORT else 587
LOGIN_SMTP = os.getenv("LOGIN_SMTP")
MDP_MAIL = os.getenv("MDP_MAIL")

# Fichier de schéma JSON
SCHEMA_FILE = SCRIPT_DIR / "assets" / "opening_hours_schema.json"

# Détection automatique du LLM basée sur les clés API disponibles
fournisseur_LLM = None
API_KEY = None
MODELE = None
BASE_URL = None

# Détection du fournisseur LLM
if os.getenv("API_KEY_OPENAI"):
    fournisseur_LLM = "OPENAI"
    API_KEY = os.getenv("API_KEY_OPENAI")
    MODELE = os.getenv("MODELE_OPENAI")
    BASE_URL = os.getenv("BASE_URL_OPENAI")
    print(f"Clé API OPENAI détectée pour {MODELE}.")
elif os.getenv("API_KEY_MISTRAL"):
    fournisseur_LLM = "MISTRAL"
    API_KEY = os.getenv("API_KEY_MISTRAL")
    MODELE = os.getenv("MODELE_MISTRAL")
    print(f"Clé API MISTRAL détectée pour {MODELE}.")
else:
    print(
        "Aucune clé API trouvée. Veuillez définir API_KEY_OPENAI ou API_KEY_MISTRAL dans vos variables d'environnement."
    )

# Base de données SQLite
DB_FILE = DATA_DIR / f"{NOM_FIC}_{MODELE.split('/')[-1]}.db"


###############################################################
#                          MAIN                               #
###############################################################
def main():
    """
    Fonction principale du programme de vérification et extraction d'horaires depuis des URLs.
    Cette fonction exécute un pipeline complet en plusieurs étapes :
        1. Chargement des données
        2. Extraction concurrente des URLs (si nécessaire)
        3. Extraction des horaires par LLM (reprise possible)
        4. Conversion au format OSM
        5. Sauvegarde incrémentale en base de données
        6. Génération de rapport HTML
        7. Envoi par email
    """
    # Initialisation du gestionnaire de base de données
    bdd = DatabaseManager(DB_FILE, NOM_FIC)

    #
    # Chargement des données
    #
    # Vérifier si la base de données existe déjà
    if bdd.exists():
        # Charger les données existantes
        df = bdd.load_data()
    else:
        # Dans ce cas on lance le chargement du fichier CSV,
        # et on crée les enregistrements dans la foulée.
        # L'extraction des URLs se fera à l'étape suivante

        # Chargement du CSV
        CSVToDF = CSVToPolars(file_path=CSV_FILE, separator=";", has_header=True)
        df_csv = CSVToDF.load_csv()

        # En cas d'erreur de lecture du fichier, afficher un message et quitter
        if isinstance(df_csv, str):
            print(f"Erreur lors du chargement du fichier CSV '{CSV_FILE}' : '{df_csv}'")
            return

        # Ajout des nouvelles colonnes
        for col in COLS_SUPPL:
            if col == "code_http":
                df_csv = df_csv.with_columns(pl.lit(0).cast(pl.Int64).alias(col))
            else:
                df_csv = df_csv.with_columns(pl.lit("").alias(col))

        df = df_csv

        # Initialiser la base de données
        bdd.initialize(df, if_exists="fail")

    #
    # Extraction URL par appels concurrents (si markdown manquant ou statut != "ok")
    #
    print("=== EXTRACTION DU CONTENU DES URLs ===")
    # Sélectionner les lignes à traiter : soit markdown manquant, soit statut différent de 'ok'
    url_to_retry_df = df.filter(
        (pl.col("statut") != "ok")
        | (pl.col("markdown") == "")
        | (pl.col("markdown").is_null())
    )

    if not url_to_retry_df.is_empty():
        rows_to_fetch = list(url_to_retry_df.iter_rows(named=True))
        print(
            f"{len(rows_to_fetch)} URLs à traiter pour l'extraction de contenu (statut != 'ok' ou markdown manquant)."
        )

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=NB_THREADS_URL
        ) as executor:
            future_to_row = {
                executor.submit(
                    retrieve_url,
                    row,
                    sortie="markdown",
                    encoding_errors="ignore",
                    char_replacements=CHAR_REPLACEMENTS,
                ): row
                for row in rows_to_fetch
            }

            # Sauvegarde des résultats dans la BDD
            for future in concurrent.futures.as_completed(future_to_row):
                row_dict = future.result()

                # Mise à jour en base de données : écraser statut, message, markdown, horaires_llm, horaires_osm
                where_conditions = {"identifiant": row_dict["identifiant"]}
                update_values = {
                    "statut": row_dict["statut"],
                    "code_http": int(row_dict["code_http"])
                    if row_dict["code_http"] not in ("", None)
                    else 0,
                    "message": row_dict["message"],
                    "markdown": row_dict["markdown"],
                    "horaires_llm": "",
                    "horaires_osm": "",
                }
                bdd.update_record(where_conditions, update_values)

        # Recharger les données depuis la BDD pour avoir un état à jour
        df = bdd.load_data()
    else:
        print("Aucune extraction de contenu d'URL nécessaire.")

    #
    # Extraction des horaires par LLM (avec reprise)
    #
    print("=== EXTRACTION DES HORAIRES PAR LLM ===")

    # Filtrer les enregistrements à traiter par le LLM
    llm_missing_df = df.filter(
        (pl.col("statut") == "ok")
        & ((pl.col("horaires_llm") == "") | (pl.col("horaires_llm").is_null()))
    )
    remaining_records = list(llm_missing_df.iter_rows(named=True))

    if remaining_records:
        # Afficher les statistiques de filtrage
        print(
            f"{len(remaining_records)} enregistrements à traiter par le LLM (statut 'ok' et sans horaires)"
        )

        # Chargement du schéma JSON depuis le fichier template
        try:
            with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
                opening_hours_schema = json.load(f)
            print(f"Schéma JSON chargé depuis : {SCHEMA_FILE}")
        except FileNotFoundError:
            print(f"Fichier de schéma non trouvé : {SCHEMA_FILE}")
            return
        except json.JSONDecodeError as e:
            print(f"Erreur de format JSON dans {SCHEMA_FILE}: {e}")
            return

        # Configuration du client LLM basé sur le fournisseur détecté
        if fournisseur_LLM == "OPENAI":
            print(
                f"Utilisation du LLM OpenAI-compatible sur '{BASE_URL}', modèle '{MODELE}'"
            )
            llm_client = llm_openai(
                api_key=API_KEY,
                model=MODELE,
                base_url=BASE_URL,
                temperature=TEMPERATURE,
                timeout=TIMEOUT,
            )
            structured_format = get_structured_response_format(
                schema=opening_hours_schema, name="opening_hours_extraction"
            )
        elif fournisseur_LLM == "MISTRAL":
            print(f"Utilisation de Mistral AI. Modèle '{MODELE}'")
            llm_client = llm_mistral(
                api_key=API_KEY,
                model=MODELE,
                temperature=TEMPERATURE,
                timeout=TIMEOUT,
            )
            # Le schéma est maintenant directement compatible avec Mistral.
            structured_format = get_mistral_tool_format(
                schema=opening_hours_schema, function_name="opening_hours_extraction"
            )

        else:
            print("Fournisseur LLM non supporté ou non configuré.")
            print("Seuls OPENAI et MISTRAL sont actuellement implémentés.")
            return

        # Traitement des enregistrements restants
        total = len(remaining_records)

        for i, row in enumerate(remaining_records, 1):
            # Affichage de la progression
            print(f"Appel {i}/{total} au LLM pour '{row.get('nom', 'Lieu inconnu')}'")

            # Traitement de l'enregistrement avec gestion d'erreur
            try:
                # Construction des messages en incluant le schéma pour guider le LLM
                messages = get_prompt(row, opening_hours_schema)

                # Appel au LLM avec les paramètres appropriés pour chaque fournisseur
                if fournisseur_LLM == "OPENAI":
                    result = llm_client.call_llm(
                        messages, response_format=structured_format
                    )
                elif fournisseur_LLM == "MISTRAL":
                    result = llm_client.call_llm(
                        messages, tool_params=structured_format
                    )
                else:
                    # Appel générique sans format structuré
                    result = llm_client.call_llm(messages)

                # Mise à jour immédiate en base de données
                where_conditions = {"identifiant": row["identifiant"]}
                update_values = {"horaires_llm": result}
                bdd.update_record(where_conditions, update_values)
                print(f"Enregistrement '{row['identifiant']}' sauvegardé")

                # Délai normal entre les appels
                if i < total:  # Pas de pause après le dernier appel
                    time.sleep(DELAI_ENTRE_APPELS)

            except Exception as e:
                print(
                    f"Erreur lors de l'appel au LLM pour '{row.get('nom', 'Lieu inconnu')}': {e}"
                )
                # Mise à jour avec l'erreur
                where_conditions = {"identifiant": row["identifiant"]}
                update_values = {"horaires_llm": f"Erreur LLM: {e}"}
                bdd.update_record(where_conditions, update_values)
                print(f"Erreur pour '{row['identifiant']}' sauvegardée")

                # Délai en cas d'erreur
                if i < total:
                    time.sleep(DELAI_EN_CAS_ERREUR)
    else:
        print(
            "Tous les enregistrements avec statut 'ok' ont déjà été traités par le LLM."
        )

    print("=== EXTRACTION DES HORAIRES TERMINÉE ===")

    # Recharger les données depuis la BDD pour avoir un état à jour
    df = bdd.load_data()

    #
    # Conversion au format OSM (si nécessaire)
    #
    print("=== CONVERSION AU FORMAT OSM ===")
    missing_osm_df = df.filter(
        (pl.col("statut") == "ok")
        & (pl.col("horaires_llm") != "")
        & (pl.col("horaires_llm").is_not_null())
        & ((pl.col("horaires_osm") == "") | (pl.col("horaires_osm").is_null()))
    )
    missing_osm_records = list(missing_osm_df.iter_rows(named=True))

    if missing_osm_records:
        print(
            f"{len(missing_osm_records)} enregistrements nécessitent une conversion OSM"
        )

        for i, row in enumerate(missing_osm_records, 1):
            print(
                f"Conversion OSM {i}/{len(missing_osm_records)} pour '{row.get('nom', 'Lieu inconnu')}'"
            )

            try:
                # Convertir les horaires LLM en format OSM
                horaires_json = json.loads(row["horaires_llm"])

                # Utiliser la nouvelle interface du convertisseur
                conversion_result = converter.convert_to_osm(horaires_json)

                # Préparer le résultat OSM avec les détails par période
                if conversion_result.osm_periods:
                    result_osm = " / ".join(
                        [
                            f"{period}: {osm_format}"
                            for period, osm_format in conversion_result.osm_periods.items()
                        ]
                    )
                else:
                    result_osm = "No periods found"

                # Mise à jour en base de données
                where_conditions = {"identifiant": row["identifiant"]}
                update_values = {"horaires_osm": result_osm}
                bdd.update_record(where_conditions, update_values)
                print(f"Conversion OSM pour '{row['identifiant']}' sauvegardée")

            except json.JSONDecodeError as e:
                print(
                    f"Erreur de parsing JSON pour '{row.get('nom', 'Lieu inconnu')}': {e}"
                )
                where_conditions = {"identifiant": row["identifiant"]}
                update_values = {"horaires_osm": f"Erreur JSON: {e}"}
                bdd.update_record(where_conditions, update_values)
                continue
            except Exception as e:
                print(
                    f"Erreur lors de la conversion OSM pour '{row.get('nom', 'Lieu inconnu')}': {e}"
                )
                where_conditions = {"identifiant": row["identifiant"]}
                update_values = {"horaires_osm": f"Erreur Conversion OSM: {e}"}
                bdd.update_record(where_conditions, update_values)
                continue
    else:
        print(
            "Tous les enregistrements avec horaires_llm ont déjà leur conversion OSM."
        )

    #
    # Générer le rapport HTML à partir de la base de données SQLite
    #
    print("=== GÉNÉRATION DU RAPPORT HTML ===")

    # Préparer les informations du modèle pour le titre
    model_info = {
        "modele": MODELE,
        "base_url": BASE_URL if fournisseur_LLM == "OPENAI" else None,
        "fournisseur": fournisseur_LLM,
    }

    resume_html, fichier_html = generer_rapport_html(
        db_file=DB_FILE,
        table_name=NOM_FIC,
        titre_rapport="Rapport de vérification des URLs",
        model_info=model_info,
    )

    #
    # Envoyer le rapport par mail
    #
    print("=== ENVOI DU RAPPORT PAR EMAIL ===")
    texte = f"""
    Rapport de vérification des URLs généré le {datetime.now().strftime("%d/%m/%Y à %H:%M")}

    {"Consultez le fichier HTML joint pour le rapport complet avec onglets interactifs." if fichier_html else "Consultez le contenu HTML ci-dessous pour le rapport complet."}
    """
    try:
        envoyer_mail_html(
            emetteur=MAIL_EMETTEUR,
            recepteur=MAIL_RECEPTEUR,
            smtp_server=SMTP_SERVER,
            smtp_port=SMTP_PORT,
            mdp=MDP_MAIL,
            login_smtp=LOGIN_SMTP or MAIL_EMETTEUR,
            sujet=f"Rapport de vérification URLs - {datetime.now().strftime('%d/%m/%Y')}",
            texte=texte,
            html_content=resume_html,
            fichier_joint=fichier_html,
        )
        print(f"Email envoyé avec le rapport '{fichier_html}'")

        # Suppression du fichier HTML après envoi
        if fichier_html and os.path.exists(fichier_html):
            os.remove(fichier_html)
            print(f"Fichier temporaire '{fichier_html}' supprimé après envoi.")
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email : {e}")
        return


if __name__ == "__main__":
    main()
