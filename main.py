###############################################################
#                         IMPORTS                             #
###############################################################
# Imports standards
import concurrent.futures
import json
import os
from datetime import datetime
from pathlib import Path

# Libraries externes
import polars as pl
from dotenv import load_dotenv

from core.EnvoyerMail import envoyer_mail_html
from core.GenererRapportHTML import generer_rapport_html
from core.GetPrompt import get_prompt
from core.LLMClient import (
    get_mistral_response_format,
    get_structured_response_format,
    llm_local,
    llm_mistral,
)
from core.URLRetriever import retrieve_url
from utils.CSVToPolars import csv_to_polars

###############################################################
#                        VARIALBES                            #
###############################################################
# Chargement des variables d'environnement depuis le fichier .env
load_dotenv()

# Répertoires et fichiers
SCRIPT_DIR = Path(__file__).parent.resolve()

# Profil d'utilisation
DATA_DIR = SCRIPT_DIR / "data"

# Fichier CSV contenant les URL
NOM_FIC = "alerte_modif_horaire_lieu"
NOM_FIC = "alerte_modif_horaire_lieu_short"
CSV_FILE = DATA_DIR / f"{NOM_FIC}.csv"

# Base de données SQLite
DB_FILE = DATA_DIR / f"{NOM_FIC}.db"

# Colonnes à ajouter au dataframe
COLS_SUPPL = ["statut", "message", "markdown", "horaires_llm"]

# Nombre de threads concurrents pour le traitement des URL
NB_THREADS = 100

# Appel à quel LLM ?
LLM = "mistral"  # "local" ou "mistral"

# Modèle LLM à utiliser
MODELE_LLM = "gemma3" if LLM == "local" else "mistral-large-latest"

# Clé API pour l'appel au LLM
CLE_API = (
    os.environ["API_KEY_LOCAL"] if LLM == "local" else os.environ["API_KEY_MISTRAL"]
)

# Envoi mail
MAIL_EMETTEUR = os.getenv("MAIL_EMETTEUR")
MAIL_RECEPTEUR = os.getenv("MAIL_RECEPTEUR")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_PORT = int(SMTP_PORT) if SMTP_PORT else 587
MDP_EMETTEUR = os.getenv("MDP_EMETTEUR")

# Fichier de schéma JSON
SCHEMA_FILE = SCRIPT_DIR / "assets" / "opening_hours_schema_template.json"


###############################################################
#                        FUNCTIONS                            #
###############################################################
def load_opening_hours_schema() -> dict:
    """
    Charge le schéma JSON depuis le fichier template.

    Returns:
        dict: Schéma JSON pour les horaires d'ouverture

    Raises:
        FileNotFoundError: Si le fichier template n'existe pas
        json.JSONDecodeError: Si le fichier JSON est malformé
    """
    try:
        with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
            schema = json.load(f)
        print(f"Schéma JSON chargé depuis : {SCHEMA_FILE}")
        return schema
    except FileNotFoundError:
        raise FileNotFoundError(f"Fichier de schéma non trouvé : {SCHEMA_FILE}")
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Erreur de format JSON dans {SCHEMA_FILE}: {e}")


###############################################################
#                          MAIN                               #
###############################################################
def main():
    """
    Fonction principale du programme de vérification et extraction d'horaires depuis des URLs.
    Cette fonction exécute un pipeline complet en plusieurs étapes :
        1. Chargement des données
        2. Extraction concurrente des URLs
        3. Extraction des horaires par LLM
        4. Sauvegarde en base de données
        5. Génération de rapport HTML
        6. Envoi par email
    Note:
        Cette fonction utilise plusieurs variables globales pour la configuration :
        - CSV_FILE, COLS_SUPPL, NB_THREADS pour le traitement des données
        - LLM, MODELE_LLM, CLE_API pour la configuration du LLM
        - DB_FILE, NOM_FIC pour la base de données
        - Variables MAIL_* pour l'envoi d'emails
    """
    #
    # Chargement des données
    #
    # Convertisseur csv -> df Polars
    CSVToDF = csv_to_polars(file_path=CSV_FILE, separator=";", has_header=True)

    # Chargement des données dans le df
    df = CSVToDF.load_csv()

    # En cas d'erreur de lecture du fichier, afficher un message et quitter
    if isinstance(df, str):
        print(f"Erreur lors du chargement du fichier CSV '{CSV_FILE}' : '{df}'")
        return

    #
    # Ajout des nouvelles colonnes
    #
    for col in COLS_SUPPL:
        df = df.with_columns(
            pl.lit("").alias(col)
        )  # Avec un str vide par défaut : pl.lit("")

    # Extraction des enregistrements à partir du dataframe
    rows = list(df.iter_rows(named=True))

    #
    # Extraction URL par appels concurrents
    #
    with concurrent.futures.ThreadPoolExecutor(max_workers=NB_THREADS) as executor:
        future_to_row = {
            executor.submit(
                retrieve_url, row, sortie="markdown", encoding_errors="ignore"
            ): row
            for row in rows
        }

        # Sauvegarde des résultats dans le nouveau dataframe
        new_rows = []
        for future in concurrent.futures.as_completed(future_to_row):
            row_dict = future.result()
            new_rows.append(row_dict)

    # Puis mise à jour du dataframe Polars avec les nouvelles lignes
    df = pl.DataFrame(new_rows)

    #
    # Extraction des horaires par LLM
    #
    print(
        f"Début de l'extraction des horaires avec le LLM '{LLM}', modèle '{MODELE_LLM}'"
    )

    # Chargement du schéma JSON depuis le fichier template
    try:
        opening_hours_schema = load_opening_hours_schema()
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Erreur lors du chargement du schéma : {e}")
        return

    # Préparation du client LLM
    if LLM == "local":
        llm_client = llm_local(
            api_key=CLE_API,
            model=MODELE_LLM,
            base_url="https://api.erasme.homes/v1",
            temperature=0.1,
        )
        # Configuration du format de réponse structuré pour OpenAI-compatible
        structured_format = get_structured_response_format(
            schema=opening_hours_schema, name="opening_hours_extraction"
        )
    elif LLM == "mistral":
        llm_client = llm_mistral(
            api_key=CLE_API,
            model=MODELE_LLM,
            temperature=0.1,
        )
        # Configuration du format de réponse structuré pour Mistral
        structured_format = get_mistral_response_format(schema=opening_hours_schema)

    # Appel au LLM
    total = len(df)
    for i, row in enumerate(df.iter_rows(named=True), start=1):
        # Affichage de la progression
        print(f"Appel {i}/{total} au LLM pour '{row.get('nom', 'Lieu inconnu')}'")

        # Traitement de l'enregistrement
        # Construction des messages
        messages = get_prompt(row)
        # Appel au LLM
        result = llm_client.call_llm(messages, response_format=structured_format)

        # Mise à jour du dataframe
        df = df.with_columns(
            pl.when(pl.col("identifiant") == row["identifiant"])
            .then(pl.lit(result))
            .otherwise(pl.col("horaires_llm"))
            .alias("horaires_llm")
        )
    print("Extraction des horaires terminée.")

    #
    # Enregistrer le df dans une base SQLite
    #
    try:
        # Suppression de l'ancien fichier de base de données s'il existe
        if DB_FILE.exists():
            print(f"Suppression du fichier SQLite '{DB_FILE}'")
            DB_FILE.unlink(missing_ok=True)

        # Enregistrement du dataframe dans la base de données SQLite
        df.write_database(
            table_name=NOM_FIC,
            connection=f"sqlite:///{DB_FILE}",
            if_table_exists="replace",
        )
        print(f"DataFrame saved to SQLite database '{DB_FILE}' in table '{NOM_FIC}'")
    except Exception as err:
        print(
            f"Erreur lors de l'enregistrement du dataframe dans la base de données '{DB_FILE}': '{err}'"
        )

    #
    # Générer le rapport HTML à partir de la base de données SQLite
    #
    resume_html, fichier_html = generer_rapport_html(
        db_file=DB_FILE,
        table_name=NOM_FIC,
        titre_rapport="Rapport de vérification des URLs",
    )

    #
    # Envoyer le rapport par mail
    #
    texte = f"""
    Rapport de vérification des URLs généré le {datetime.now().strftime("%d/%m/%Y à %H:%M")}
    
    {"Consultez le fichier HTML joint pour le rapport complet avec onglets interactifs." if fichier_html else "Consultez le contenu HTML ci-dessous pour le rapport complet."}
    """
    envoyer_mail_html(
        emetteur=MAIL_EMETTEUR,
        recepteur=MAIL_RECEPTEUR,
        mdp_emetteur=MDP_EMETTEUR,
        smtp_server=SMTP_SERVER,
        smtp_port=SMTP_PORT,
        sujet=f"Rapport de vérification URLs - {datetime.now().strftime('%d/%m/%Y')}",
        texte=texte,
        html_content=resume_html,
        fichier_joint=fichier_html,
    )
    print(f"Email envoyé avec le rapport '{fichier_html}'")


if __name__ == "__main__":
    main()
