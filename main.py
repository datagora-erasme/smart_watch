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
    get_mistral_response_format,
    get_structured_response_format,
    llm_mistral,
    llm_openai,
)
from core.URLRetriever import retrieve_url
from utils.CSVToPolars import CSVToPolars
from utils.CustomJsonToOSM import OSMConverter

# Initialiser le convertisseur avec l'option d'override
# True = outrepasser ouvert=False si des créneaux sont présents
# False = respecter strictement ouvert=False
converter = OSMConverter(creneaux_prioritaires=True)


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
NOM_FIC = "alerte_modif_horaire_lieu"
NOM_FIC = "alerte_modif_horaire_lieu_unique"

CSV_FILE = DATA_DIR / f"{NOM_FIC}.csv"

# Colonnes à ajouter au dataframe pour stocker les résultats
COLS_SUPPL = ["statut", "message", "markdown", "horaires_llm", "horaires_osm"]

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
TEMPERATURE = 0.1

# Délai entre les appels LLM (en secondes)
DELAI_ENTRE_APPELS = 20 / 100
DELAI_EN_CAS_ERREUR = 600

# timeout pour les appels LLM (en secondes)
TIMEOUT = 610  # mettre plus que le DELAI_EN_CAS_ERREUR pour éviter les timeouts

# Envoi mail
MAIL_EMETTEUR = os.getenv("MAIL_EMETTEUR")
MAIL_RECEPTEUR = os.getenv("MAIL_RECEPTEUR")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_PORT = int(SMTP_PORT) if SMTP_PORT else 587
LOGIN_SMTP = os.getenv("LOGIN_SMTP")
MDP_MAIL = os.getenv("MDP_MAIL")

# Fichier de schéma JSON
SCHEMA_FILE = SCRIPT_DIR / "assets" / "opening_hours_schema_template.json"

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
#                        FONCTIONS                            #
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
        2. Extraction concurrente des URLs (si nécessaire)
        3. Extraction des horaires par LLM (reprise possible)
        4. Sauvegarde incrémentale en base de données
        5. Génération de rapport HTML
        6. Envoi par email
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
        # et on crée les enregistrements dans la foulée, en
        # extrayant les URLs par appels concurrents.

        # Chargement du CSV
        CSVToDF = CSVToPolars(file_path=CSV_FILE, separator=";", has_header=True)
        df_csv = CSVToDF.load_csv()

        # En cas d'erreur de lecture du fichier, afficher un message et quitter
        if isinstance(df_csv, str):
            print(f"Erreur lors du chargement du fichier CSV '{CSV_FILE}' : '{df_csv}'")
            return

        # Ajout des nouvelles colonnes
        for col in COLS_SUPPL:
            df_csv = df_csv.with_columns(pl.lit("").alias(col))

        # Extraction des enregistrements à partir du dataframe
        rows = list(df_csv.iter_rows(named=True))

        #
        # Extraction URL par appels concurrents (seulement si nouvelle exécution)
        #
        print("=== EXTRACTION DES URLs ===")
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
                for row in rows
            }

            # Sauvegarde des résultats dans le nouveau dataframe
            new_rows = []
            for future in concurrent.futures.as_completed(future_to_row):
                row_dict = future.result()
                new_rows.append(row_dict)

        # Mise à jour du dataframe Polars avec les nouvelles lignes
        df = pl.DataFrame(new_rows)

        # Initialiser la base de données
        if_exists = "skip" if bdd.exists() else "fail"
        bdd.initialize(df, if_exists)

    #
    # Extraction des horaires par LLM (avec reprise)
    #
    print("=== EXTRACTION DES HORAIRES PAR LLM ===")

    # Obtenir les enregistrements restants à traiter directement
    # Filtrer d'abord par statut 'ok', puis par horaires_llm vides
    remaining_df = df.filter(
        (pl.col("statut") == "ok")
        & ((pl.col("horaires_llm") == "") | (pl.col("horaires_llm").is_null()))
    )
    remaining_records = list(remaining_df.iter_rows(named=True))

    # Afficher les statistiques de filtrage
    print(
        f"{len(remaining_records)} enregistrements à traiter (statut 'ok' et sans horaires)"
    )

    if not remaining_records:
        print(
            "Tous les enregistrements avec statut 'ok' ont déjà été traités par le LLM."
        )
    else:
        # Chargement du schéma JSON depuis le fichier template
        try:
            opening_hours_schema = load_opening_hours_schema()
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Erreur lors du chargement du schéma : {e}")
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
            # Utiliser le modèle Pydantic pour Mistral
            # structured_format = Horaires
            structured_format = get_mistral_response_format(schema=opening_hours_schema)

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
                # Construction des messages
                messages = get_prompt(row)
                # Appel au LLM
                result = llm_client.call_llm(
                    messages, response_format=structured_format
                )

                # Convert to OSM format
                result_osm = converter.convert_to_osm(json.loads(result))

                # Mise à jour immédiate en base de données
                where_conditions = {"identifiant": row["identifiant"]}
                update_values = {"horaires_llm": result, "horaires_osm": result_osm}
                bdd.update_record(where_conditions, update_values)
                print(f"Enregistrement '{row['identifiant']}' sauvegardé")

                # Délai normal entre les appels
                if i < total:  # Pas de pause après le dernier appel
                    time.sleep(DELAI_ENTRE_APPELS)

            except Exception as e:
                print(
                    f"Erreur lors de l'appel au LLM pour '{row.get('nom', 'Lieu inconnu')}': {e}"
                )

                # Pause plus longue en cas d'erreur (rate limiting, etc.)
                if "429" in str(e) or "capacity exceeded" in str(e).lower():
                    print(
                        f"Rate limiting détecté - Pause de {DELAI_EN_CAS_ERREUR}s avant de réessayer"
                    )
                    time.sleep(DELAI_EN_CAS_ERREUR)
                    # Réessayer le même enregistrement en ne pas incrementant i
                    continue
                else:
                    # Pour les autres erreurs, passer au suivant
                    print(f"Erreur pour '{row['identifiant']}', passage au suivant")
                    continue

    print("=== EXTRACTION DES HORAIRES TERMINÉE ===")

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
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email : {e}")
        return


if __name__ == "__main__":
    main()
