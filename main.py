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
from dotenv import dotenv_values, load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Librairies du projet
from assets.schema_bdd import Base, Executions, Lieux, ResultatsExtraction
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


# Fonction utilitaire pour télécharger un CSV depuis une URL et le charger avec polars
def download_csv(url, separator=";", has_header=True):
    import polars as pl

    try:
        return pl.read_csv(url, separator=separator, has_header=has_header)
    except Exception as e:
        raise RuntimeError(
            f"Erreur lors du téléchargement ou de la lecture du CSV depuis {url}: {e}"
        )


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

# Fichiers CSV de référence (data.grandlyon.com)
_BASE_URL = "https://data.grandlyon.com/fr/datapusher/ws/grandlyon/adr_voie_lieu."
_OPTIONS_URL = "/all.csv?maxfeatures=-1&start=1&filename="
_SUFFIX_URL = "-metropole-lyon-point-interet"
_OPTIONS_CSV = "&ds=.&separator=;"

CSV_FILE_REF = {
    "mairies": f"{_BASE_URL}adrmairiepct{_OPTIONS_URL}mairies{_SUFFIX_URL}-v2{_OPTIONS_CSV}",
    "mediatheques": f"{_BASE_URL}adrequiculturepct{_OPTIONS_URL}bibliotheques{_SUFFIX_URL}{_OPTIONS_CSV}",
    "piscines": f"{_BASE_URL}adrequippiscinepct{_OPTIONS_URL}piscines{_SUFFIX_URL}{_OPTIONS_CSV}",
}

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

# Configuration SQLAlchemy
engine = create_engine(f"sqlite:///{DB_FILE}")
Session = sessionmaker(bind=engine)


###############################################################
#                          MAIN                               #
###############################################################
def main():
    """
    Fonction principale du programme de vérification et extraction d'horaires depuis des URLs.
    Cette fonction exécute un pipeline complet en plusieurs étapes :
        1. Chargement des données et initialisation de la base normalisée
        2. Création d'une nouvelle exécution
        3. Extraction concurrente des URLs (si nécessaire)
        4. Extraction des horaires par LLM (reprise possible)
        5. Conversion au format OSM
        6. Génération de rapport HTML
        7. Envoi par email
    """

    # Créer les tables si elles n'existent pas
    Base.metadata.create_all(engine)

    session = Session()

    try:
        #
        # Chargement des données et gestion des lieux
        #
        print("=== CHARGEMENT DES DONNÉES ===")

        # Chargement du CSV
        CSVToDF = CSVToPolars(file_path=CSV_FILE, separator=";", has_header=True)
        df_csv = CSVToDF.load_csv()

        # En cas d'erreur de lecture du fichier, afficher un message et quitter
        if isinstance(df_csv, str):
            print(f"Erreur lors du chargement du fichier CSV '{CSV_FILE}' : '{df_csv}'")
            return

        # Insérer ou mettre à jour les lieux
        for row in df_csv.iter_rows(named=True):
            lieu_existant = (
                session.query(Lieux).filter_by(identifiant=row["identifiant"]).first()
            )

            if not lieu_existant:
                nouveau_lieu = Lieux(
                    identifiant=row["identifiant"],
                    nom=row.get("nom", ""),
                    type_lieu=row.get("type_lieu", ""),
                    url=row.get("url", ""),
                    horaires_data_gl=row.get("horaires_data_gl", ""),
                )
                session.add(nouveau_lieu)
                print(f"Nouveau lieu ajouté: {row['identifiant']}")
            else:
                # Mettre à jour les informations du lieu si nécessaire
                lieu_existant.nom = row.get("nom", lieu_existant.nom)
                lieu_existant.type_lieu = row.get("type_lieu", lieu_existant.type_lieu)
                lieu_existant.url = row.get("url", lieu_existant.url)
                lieu_existant.horaires_data_gl = row.get(
                    "horaires_data_gl", lieu_existant.horaires_data_gl
                )

        # Charger les trois csv de références, et partant de là, remplir le champ horaires_data_gl dans la base
        for nom, url in CSV_FILE_REF.items():
            try:
                df_ref = download_csv(url)
                for row in df_ref.iter_rows(named=True):
                    lieu_existant = (
                        session.query(Lieux)
                        .filter_by(identifiant=row["identifiant"])
                        .first()
                    )
                    if lieu_existant:
                        lieu_existant.horaires_data_gl = row.get(
                            "horaires", lieu_existant.horaires_data_gl
                        )
                        print(
                            f"Horaires GL mis à jour pour: {lieu_existant.identifiant}"
                        )
                    else:
                        print(
                            f"Lieu non trouvé pour mettre à jour les horaires GL: {row['identifiant']}"
                        )
            except Exception as e:
                print(f"Erreur lors du chargement du fichier de référence '{nom}': {e}")

        #
        # Création d'une nouvelle exécution
        #
        nouvelle_execution = Executions(
            date_execution=datetime.now(),
            llm_modele=MODELE,
            llm_fournisseur=fournisseur_LLM,
            llm_url=BASE_URL,
        )
        session.add(nouvelle_execution)
        session.commit()

        execution_id = nouvelle_execution.id_executions
        print(f"Nouvelle exécution créée avec l'ID: {execution_id}")

        #
        # Vérification des exécutions incomplètes à reprendre
        #
        print("=== VÉRIFICATION DES EXÉCUTIONS INCOMPLÈTES ===")

        # Chercher les enregistrements incomplets des exécutions précédentes
        # Séparer par type d'incomplétude pour un traitement plus fin
        enregistrements_incomplets = (
            session.query(ResultatsExtraction, Lieux)
            .join(Lieux, ResultatsExtraction.lieu_id == Lieux.identifiant)
            .filter(
                ResultatsExtraction.id_execution != execution_id,
                # Conditions pour définir un enregistrement comme incomplet
                (
                    (
                        ResultatsExtraction.statut_url != "ok"
                    )  # URL pas encore téléchargée
                    | (
                        (ResultatsExtraction.statut_url == "ok")
                        & (
                            ResultatsExtraction.llm_horaires_json == ""
                        )  # URL OK mais pas de LLM
                    )
                    | (
                        (ResultatsExtraction.statut_url == "ok")
                        & (ResultatsExtraction.llm_horaires_json != "")
                        & (
                            ResultatsExtraction.llm_horaires_osm == ""
                        )  # LLM OK mais pas d'OSM
                    )
                ),
            )
            .all()
        )

        if enregistrements_incomplets:
            print(
                f"{len(enregistrements_incomplets)} enregistrements incomplets détectés - reprise d'exécutions précédentes"
            )

            # Analyser et classer les enregistrements incomplets
            url_manquantes = []
            llm_manquant = []
            osm_manquant = []

            for resultat, lieu in enregistrements_incomplets:
                # Mettre à jour l'ID d'exécution immédiatement pour tous les enregistrements incomplets
                resultat.id_execution = execution_id
                print(
                    f"Enregistrement '{lieu.identifiant}' assigné à l'exécution {execution_id}"
                )

                # Classifier selon ce qui manque
                if resultat.statut_url != "ok":
                    url_manquantes.append((resultat, lieu))
                elif resultat.llm_horaires_json == "":
                    llm_manquant.append((resultat, lieu))
                elif resultat.llm_horaires_osm == "":
                    osm_manquant.append((resultat, lieu))

            session.commit()

            print(f"  - {len(url_manquantes)} URLs à télécharger")
            print(f"  - {len(llm_manquant)} extractions LLM à effectuer")
            print(f"  - {len(osm_manquant)} conversions OSM à effectuer")

            # Ne créer de nouveaux enregistrements que pour les lieux qui n'ont pas encore d'enregistrement
            lieux_existants_ids = set(
                [resultat.lieu_id for resultat, _ in enregistrements_incomplets]
            )
        else:
            print("Aucun enregistrement incomplet détecté")
            lieux_existants_ids = set()

        # Créer les enregistrements de résultats d'extraction pour cette exécution
        # (seulement pour les nouveaux lieux qui ne sont pas dans la base)
        nouveaux_lieux_count = 0
        for row in df_csv.iter_rows(named=True):
            if row["identifiant"] not in lieux_existants_ids:
                # Vérifier qu'il n'existe pas déjà un enregistrement pour ce lieu
                enregistrement_existant = (
                    session.query(ResultatsExtraction)
                    .filter_by(lieu_id=row["identifiant"])
                    .first()
                )

                if not enregistrement_existant:
                    nouveau_resultat = ResultatsExtraction(
                        lieu_id=row["identifiant"],
                        id_execution=execution_id,
                        statut_url="",
                        code_http=0,
                        message_url="",
                        markdown="",
                        prompt_message="",
                        llm_consommation_requete="",
                        llm_horaires_json="",
                        llm_horaires_osm="",
                    )
                    session.add(nouveau_resultat)
                    nouveaux_lieux_count += 1

        if nouveaux_lieux_count > 0:
            print(f"{nouveaux_lieux_count} nouveaux enregistrements créés")

        session.commit()

        #
        # Extraction URL par appels concurrents
        #
        print("=== EXTRACTION DU CONTENU DES URLs ===")

        # Récupérer les résultats à traiter pour cette exécution
        # (seulement ceux sans contenu URL valide)
        resultats_a_traiter = (
            session.query(ResultatsExtraction, Lieux)
            .join(Lieux, ResultatsExtraction.lieu_id == Lieux.identifiant)
            .filter(
                ResultatsExtraction.id_execution == execution_id,
                ResultatsExtraction.statut_url != "ok",
            )
            .all()
        )

        if resultats_a_traiter:
            print(
                f"{len(resultats_a_traiter)} URLs à traiter pour l'extraction de contenu."
            )

            with concurrent.futures.ThreadPoolExecutor(
                max_workers=NB_THREADS_URL
            ) as executor:
                # Préparer les données pour retrieve_url
                future_to_resultat = {}
                for resultat, lieu in resultats_a_traiter:
                    row_data = {
                        "identifiant": lieu.identifiant,
                        "nom": lieu.nom,
                        "url": lieu.url,
                        "type_lieu": lieu.type_lieu,
                    }
                    future = executor.submit(
                        retrieve_url,
                        row_data,
                        sortie="markdown",
                        encoding_errors="ignore",
                        char_replacements=CHAR_REPLACEMENTS,
                    )
                    future_to_resultat[future] = resultat

                # Traitement des résultats
                for future in concurrent.futures.as_completed(future_to_resultat):
                    resultat = future_to_resultat[future]
                    row_dict = future.result()

                    # Mise à jour du résultat
                    resultat.statut_url = row_dict.get("statut", "error")
                    code_http_val = row_dict.get("code_http")
                    resultat.code_http = (
                        int(code_http_val) if code_http_val not in ("", None) else 0
                    )
                    resultat.message_url = row_dict.get(
                        "message", "Erreur inconnue lors de la récupération de l'URL."
                    )
                    resultat.markdown = row_dict.get("markdown", "")

            session.commit()
        else:
            print("Aucune extraction de contenu d'URL nécessaire.")

        #
        # Extraction des horaires par LLM
        #
        print("=== EXTRACTION DES HORAIRES PAR LLM ===")

        # Filtrer les enregistrements à traiter par le LLM
        # (ceux qui ont un contenu URL OK mais pas encore d'extraction LLM)
        resultats_pour_llm = (
            session.query(ResultatsExtraction, Lieux)
            .join(Lieux, ResultatsExtraction.lieu_id == Lieux.identifiant)
            .filter(ResultatsExtraction.id_execution == execution_id)
            .filter(
                ResultatsExtraction.statut_url == "ok",
                ResultatsExtraction.llm_horaires_json == "",
            )
            .all()
        )

        if resultats_pour_llm:
            print(f"{len(resultats_pour_llm)} enregistrements à traiter par le LLM")

            # Chargement du schéma JSON
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

            # Configuration du client LLM
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
                structured_format = get_mistral_tool_format(
                    schema=opening_hours_schema,
                    function_name="opening_hours_extraction",
                )
            else:
                print("Fournisseur LLM non supporté ou non configuré.")
                return

            # Traitement des enregistrements
            total = len(resultats_pour_llm)
            for i, (resultat, lieu) in enumerate(resultats_pour_llm, 1):
                print(f"Appel {i}/{total} au LLM pour '{lieu.nom}'")

                try:
                    # Préparer les données pour get_prompt
                    row_data = {
                        "identifiant": lieu.identifiant,
                        "nom": lieu.nom,
                        "url": lieu.url,
                        "type_lieu": lieu.type_lieu,
                        "markdown": resultat.markdown,
                    }

                    messages = get_prompt(row_data, opening_hours_schema)
                    resultat.prompt_message = json.dumps(messages, ensure_ascii=False)

                    # Appel au LLM
                    if fournisseur_LLM == "OPENAI":
                        result = llm_client.call_llm(
                            messages, response_format=structured_format
                        )
                    elif fournisseur_LLM == "MISTRAL":
                        result = llm_client.call_llm(
                            messages, tool_params=structured_format
                        )
                    else:
                        result = llm_client.call_llm(messages)

                    # Mise à jour avec le résultat LLM
                    resultat.llm_horaires_json = result

                    # Conversion OSM immédiate après extraction LLM réussie
                    try:
                        llm_horaires_json = json.loads(result)
                        conversion_result = converter.convert_to_osm(llm_horaires_json)

                        if conversion_result.osm_periods:
                            result_osm = " / ".join(
                                [
                                    f"{period}: {osm_format}"
                                    for period, osm_format in conversion_result.osm_periods.items()
                                ]
                            )
                        else:
                            result_osm = "No periods found"

                        resultat.llm_horaires_osm = result_osm
                        print(f"Conversion OSM réussie pour '{lieu.identifiant}'")

                    except json.JSONDecodeError as e:
                        print(
                            f"Erreur de parsing JSON pour conversion OSM '{lieu.nom}': {e}"
                        )
                        resultat.llm_horaires_osm = f"Erreur JSON: {e}"
                    except Exception as e:
                        print(
                            f"Erreur lors de la conversion OSM pour '{lieu.nom}': {e}"
                        )
                        resultat.llm_horaires_osm = f"Erreur Conversion OSM: {e}"

                    session.commit()
                    print(
                        f"Enregistrement '{lieu.identifiant}' sauvegardé avec conversion OSM"
                    )

                    # Délai entre les appels
                    if i < total:
                        time.sleep(DELAI_ENTRE_APPELS)

                except Exception as e:
                    print(f"Erreur lors de l'appel au LLM pour '{lieu.nom}': {e}")
                    resultat.llm_horaires_json = f"Erreur LLM: {e}"
                    session.commit()

                    if i < total:
                        time.sleep(DELAI_EN_CAS_ERREUR)

        print("=== EXTRACTION DES HORAIRES TERMINÉE ===")

        #
        # Conversion au format OSM pour les enregistrements restants (si nécessaire)
        #
        print("=== VÉRIFICATION CONVERSION OSM RESTANTE ===")

        # Chercher les enregistrements qui ont une extraction LLM mais pas de conversion OSM
        resultats_pour_osm = (
            session.query(ResultatsExtraction, Lieux)
            .join(Lieux, ResultatsExtraction.lieu_id == Lieux.identifiant)
            .filter(ResultatsExtraction.id_execution == execution_id)
            .filter(
                ResultatsExtraction.statut_url == "ok",
                ResultatsExtraction.llm_horaires_json != "",
                ResultatsExtraction.llm_horaires_json.notlike(
                    "Erreur LLM:%"
                ),  # Exclure les erreurs LLM
                ResultatsExtraction.llm_horaires_osm == "",
            )
            .all()
        )

        if resultats_pour_osm:
            print(
                f"{len(resultats_pour_osm)} enregistrements nécessitent encore une conversion OSM"
            )

            for i, (resultat, lieu) in enumerate(resultats_pour_osm, 1):
                print(f"Conversion OSM {i}/{len(resultats_pour_osm)} pour '{lieu.nom}'")

                try:
                    llm_horaires_json = json.loads(resultat.llm_horaires_json)
                    conversion_result = converter.convert_to_osm(llm_horaires_json)

                    if conversion_result.osm_periods:
                        result_osm = " / ".join(
                            [
                                f"{period}: {osm_format}"
                                for period, osm_format in conversion_result.osm_periods.items()
                            ]
                        )
                    else:
                        result_osm = "No periods found"

                    resultat.llm_horaires_osm = result_osm
                    session.commit()
                    print(f"Conversion OSM pour '{lieu.identifiant}' sauvegardée")

                except json.JSONDecodeError as e:
                    print(f"Erreur de parsing JSON pour '{lieu.nom}': {e}")
                    resultat.llm_horaires_osm = f"Erreur JSON: {e}"
                    session.commit()
                except Exception as e:
                    print(f"Erreur lors de la conversion OSM pour '{lieu.nom}': {e}")
                    resultat.llm_horaires_osm = f"Erreur Conversion OSM: {e}"
                    session.commit()
        else:
            print("Aucune conversion OSM supplémentaire nécessaire")

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
            table_name="resultats_extraction",
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

    finally:
        session.close()


if __name__ == "__main__":
    main()
