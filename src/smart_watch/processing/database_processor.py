# Gestionnaire des opérations de base de données spécifiques à SmartWatch.
# https://datagora-erasme.github.io/smart_watch/source/modules/processing/database_processor.html

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional, Sequence, Tuple

from sqlalchemy import text
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.engine import Row

from src.smart_watch.core.DatabaseManager import DatabaseManager
from src.smart_watch.core.Logger import SmartWatchLogger

from ..core.ConfigManager import ConfigManager
from ..data_models.schema_bdd import (
    Base,
    Executions,
    Lieux,
    ResultatsExtraction,
)
from ..utils.CSVToPolars import CSVToPolars
from ..utils.OSMToCustomJson import OsmToJsonConverter

if TYPE_CHECKING:
    # Type hints pour éviter les erreurs Pylance avec SQLAlchemy
    pass


class DatabaseProcessor:
    """Crée la base de données et les tables nécessaires."""

    def __init__(self, config: ConfigManager, logger: SmartWatchLogger):
        """Initialise le processeur de base de données."""
        self.config = config
        self.logger = logger
        # Le DatabaseManager est initialisé avec le chemin du fichier de la base de données.
        self.db_manager = DatabaseManager(self.config.database.db_file)

    def create_database(self) -> DatabaseManager:
        """
        Crée les tables de la base de données si elles n'existent pas et retourne le manager.
        """
        self.logger.info(
            f"Initialisation de la base de données {self.config.database.db_file}..."
        )
        # Utiliser l'engine du db_manager pour créer les tables
        Base.metadata.create_all(self.db_manager.engine)
        self.logger.info("Base de données et tables créées avec succès.")
        return self.db_manager

    def execute_query(
        self, query: str, params: Optional[dict] = None
    ) -> Sequence[Row[Any]]:
        """
        Exécute une requête SQL sur la base de données et retourne les résultats.

        Args:
            query (str): La requête SQL à exécuter.
            params (Optional[dict], optionnel): Les paramètres à utiliser dans la requête SQL. Par défaut à None.

        Returns:
            Sequence[Row[Any]]: Une séquence de lignes retournées par la requête.
        """
        with self.db_manager.engine.connect() as connection:
            try:
                result = connection.execute(text(query), params or {})
                return result.fetchall()
            except Exception as e:
                self.logger.error(f"Erreur exécution requête: {e}")
                raise

    def setup_execution(self, df_csv) -> int:
        """
        Configure et initialise une nouvelle exécution à partir d'un DataFrame issu
        du fichier CSV pris sur l'URL indiqué dans CSV_URL_HORAIRES du fichier .env.

        Etapes :
        1. Met à jour les lieux dans la base de données à partir des données du DataFrame CSV.
        2. Met à jour les horaires des lieux en se basant sur les références GL.
        3. Crée une nouvelle entrée d'exécution dans la base de données.
        4. Configure les résultats d'extraction associés à cette exécution en utilisant les données du DataFrame CSV.

        Args:
            df_csv (pd.DataFrame): DataFrame contenant les données extraites du CSV.

        Returns:
            int: Identifiant unique de l'exécution créée.
        """
        session = self.db_manager.Session()
        try:
            # 1. Mise à jour des lieux
            self._update_lieux_batch(session, df_csv)

            # 2. Mise à jour des références GL
            self._update_horaires_lieux_depuis_gl(session)

            # 3. Création de l'exécution
            execution_id = self._create_execution(session)

            # 4. Configuration des résultats d'extraction
            self._setup_resultats_extraction(session, df_csv, execution_id)

            return execution_id
        finally:
            session.close()

    def _update_lieux_batch(self, session, df_csv):
        """
        Met à jour en batch les enregistrements de lieux dans la base de données à partir du df issu de CSV_URL_HORAIRES.

        Pour chaque ligne du DataFrame, extrait les informations du lieu (identifiant, nom, type_lieu, url, horaires_data_gl)
        et prépare les données pour une insertion ou mise à jour efficace dans la table 'Lieux'.

        Utilise une opération 'merge' (insert avec gestion des conflits) pour insérer les nouveaux lieux ou mettre à jour
        ceux existants selon l'identifiant.

        Log le nombre d'enregistrements mis à jour.

        Args:
            session (Session): Session SQLAlchemy active pour effectuer les opérations sur la base de données.
            df_csv (DataFrame): DataFrame contenant les données des lieux à insérer ou mettre à jour.
        """
        lieux_data = []
        for row in df_csv.iter_rows(named=True):
            lieux_data.append(
                {
                    "identifiant": row["identifiant"],
                    "nom": row.get("nom", ""),
                    "type_lieu": row.get("type_lieu", ""),
                    "url": row.get("url", ""),
                    "horaires_data_gl": row.get("horaires_data_gl", ""),
                }
            )

        # Utiliser merge pour insert efficace
        stmt = insert(Lieux).values(lieux_data)
        stmt = stmt.on_conflict_do_update(
            index_elements=["identifiant"],
            set_={
                "nom": stmt.excluded.nom,
                "type_lieu": stmt.excluded.type_lieu,
                "url": stmt.excluded.url,
                "horaires_data_gl": stmt.excluded.horaires_data_gl,
            },
        )
        session.execute(stmt)
        session.commit()
        self.logger.info(f"Lieux mis à jour: {len(lieux_data)} enregistrements")

    def _update_horaires_lieux_depuis_gl(self, session):
        """
        Met à jour les horaires des lieux à partir des fichiers de référence CSV issus de data.grandlyon.com :
        CSV_URL_PISCINES, CSV_URL_MAIRIES, CSV_URL_MEDIATHEQUES.

        Pour chaque fichier de référence :
            - Charge les données CSV en utilisant CSVToPolars.
            - Parcourt chaque ligne pour trouver le lieu correspondant dans la base de données via son identifiant.
            - Si le lieu existe et que des horaires sont présents :
                - Met à jour le champ 'horaires_data_gl' du lieu.
                - Si le convertisseur OSM est disponible, tente de convertir les horaires au format JSON enrichi et met à jour le champ 'horaires_data_gl_json'.
            - Enregistre les modifications dans la base de données.
            - Journalise le nombre de lieux mis à jour ou les erreurs rencontrées.

        Args:
            session (Session): Session SQLAlchemy utilisée pour accéder et modifier les objets de la base de données.

        Exceptions:
            - Journalise les erreurs lors du chargement des fichiers CSV ou de la conversion des horaires.
            - Si le convertisseur OSM n'est pas disponible, journalise une erreur et ignore la conversion JSON.
        """
        try:
            osm_converter = OsmToJsonConverter()
        except ImportError:
            self.logger.error("Convertisseur OSM non disponible")
            osm_converter = None

        for nom, url in self.config.database.csv_file_ref.items():
            row = None  # Initialiser row à None avant la boucle
            try:
                csv_loader = CSVToPolars(
                    source=url,
                    separator="auto",
                    has_header=True,
                )
                df_ref = csv_loader.load_csv()
                count = 0

                for row in df_ref.iter_rows(named=True):
                    lieu_existant = (
                        session.query(Lieux)
                        .filter_by(identifiant=row["identifiant"])
                        .first()
                    )

                    if lieu_existant and row.get("horaires"):
                        lieu_existant.horaires_data_gl = row.get("horaires")

                        # Conversion JSON si possible
                        if osm_converter:
                            try:
                                horaires_gl_json = osm_converter.convert_osm_string(
                                    row.get("horaires"),
                                    metadata={
                                        "identifiant": lieu_existant.identifiant,
                                        "nom": lieu_existant.nom,
                                        "type_lieu": lieu_existant.type_lieu,
                                        "url": lieu_existant.url,
                                    },
                                )
                                lieu_existant.horaires_data_gl_json = json.dumps(
                                    horaires_gl_json, ensure_ascii=False
                                )
                                count += 1
                            except Exception as e:
                                self.logger.error(
                                    f"*{row['identifiant']}* Erreur conversion pour '{row.get('nom', 'Nom Inconnu')}': {e}"
                                )

                session.commit()
                if row:  # S'assurer que la boucle a été exécutée au moins une fois
                    self.logger.info(
                        f"*{row['identifiant']}* Références pour '{nom}' mises à jour: {count} lieux"
                    )

            except Exception as e:
                log_message = f"Erreur chargement '{nom}'"
                if row and "identifiant" in row:
                    log_message = f"*{row['identifiant']}* {log_message}: {e}"
                else:
                    log_message += f": {e}"
                self.logger.error(log_message)

    def _create_execution(self, session) -> int:
        """
        Crée une nouvelle exécution et retourne son ID.

        Args:
            session (Session): Session SQLAlchemy active.

        Returns:
            int: Identifiant unique de l'exécution créée.
        """
        try:
            nouvelle_execution = Executions(date_execution=datetime.now())
            session.add(nouvelle_execution)

            # Essayer flush + refresh d'abord
            try:
                session.flush()
                session.refresh(nouvelle_execution)
                execution_id = nouvelle_execution.id_execution

                # Vérifier que c'est bien un int
                if isinstance(execution_id, int):
                    session.commit()
                    self.logger.info(
                        f"Nouvelle exécution créée avec ID: {execution_id}"
                    )
                    return execution_id
            except Exception:
                # Si flush/refresh échoue, utiliser commit + requête
                pass

            # Fallback : commit puis requête
            session.commit()

            # Récupérer le dernier enregistrement inséré
            last_execution = (
                session.query(Executions)
                .order_by(Executions.id_execution.desc())
                .first()
            )

            execution_id = int(last_execution.id_execution)

            self.logger.info(f"Nouvelle exécution créée avec ID: {execution_id}")
            return execution_id

        except Exception as e:
            self.logger.error(f"Erreur lors de la création de l'exécution: {e}")
            session.rollback()
            raise

    def _setup_resultats_extraction(self, session, df_csv, execution_id):
        """
        Prépare et gère les enregistrements de résultats d'extraction pour une nouvelle exécution.

        Cette méthode effectue les opérations suivantes :
        - Vérifie la présence d'enregistrements incomplets (statut URL, extraction LLM, conversion OSM) issus d'exécutions précédentes,
          et les assigne à l'exécution courante pour reprise.
        - Classe les enregistrements incomplets selon le type de données manquantes (URL, LLM, OSM)
          et journalise le nombre d'actions à effectuer pour chaque catégorie.
        - Crée de nouveaux enregistrements de résultats d'extraction pour les lieux présents dans le fichier CSV_URL_HORAIRES,
          mais absents de la base de données, en initialisant les champs nécessaires.

        Args:
            session (Session): Session SQLAlchemy active pour les opérations sur la base de données.
            df_csv (DataFrame): Fichier CSV des lieux à traiter.
            execution_id (int): Identifiant unique de l'exécution en cours.
        """
        # Vérification des exécutions incomplètes à reprendre
        self.logger.section("VÉRIFICATION DES EXÉCUTIONS INCOMPLÈTES")

        # Chercher les enregistrements incomplets (URL, LLM, OSM) des exécutions précédentes
        enregistrements_incomplets = (
            session.query(ResultatsExtraction, Lieux)
            .join(Lieux, ResultatsExtraction.lieu_id == Lieux.identifiant)
            .filter(
                ResultatsExtraction.id_execution != execution_id,
                # Conditions pour définir un enregistrement comme incomplet (hors comparaison)
                (
                    (ResultatsExtraction.statut_url != "ok")
                    | (
                        (ResultatsExtraction.statut_url == "ok")
                        & (ResultatsExtraction.llm_horaires_json == "")
                    )
                    | (
                        (ResultatsExtraction.statut_url == "ok")
                        & (ResultatsExtraction.llm_horaires_json != "")
                        & (ResultatsExtraction.llm_horaires_osm == "")
                    )
                ),
            )
            .all()
        )

        if enregistrements_incomplets:
            self.logger.info(
                f"{len(enregistrements_incomplets)} enregistrements incomplets (URL/LLM/OSM) détectés - reprise"
            )

            # Analyser et classer les enregistrements incomplets
            url_manquantes = []
            llm_manquant = []
            osm_manquant = []

            for resultat, lieu in enregistrements_incomplets:
                # Mettre à jour l'ID d'exécution immédiatement
                resultat.id_execution = execution_id
                self.logger.info(
                    f"*{lieu.identifiant}* Enregistrement pour '{lieu.nom}' assigné à l'exécution {execution_id} pour reprise"
                )

                # Classifier selon ce qui manque
                if resultat.statut_url != "ok":
                    url_manquantes.append((resultat, lieu))
                elif resultat.llm_horaires_json == "":
                    llm_manquant.append((resultat, lieu))
                elif resultat.llm_horaires_osm == "":
                    osm_manquant.append((resultat, lieu))

            session.commit()

            self.logger.info(f"  - {len(url_manquantes)} URLs à télécharger")
            self.logger.info(f"  - {len(llm_manquant)} extractions LLM à effectuer")
            self.logger.info(f"  - {len(osm_manquant)} conversions OSM à effectuer")

            # Les comparaisons manquantes seront traitées par le ComparisonProcessor
            self.logger.info(
                "  - Les comparaisons manquantes seront traitées globalement."
            )

            lieux_existants_ids = set(
                [resultat.lieu_id for resultat, _ in enregistrements_incomplets]
            )
        else:
            self.logger.info("Aucun enregistrement incomplet (URL/LLM/OSM) détecté")
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
                        markdown_brut="",
                        markdown_nettoye="",
                        markdown_filtre="",
                        prompt_message="",
                        llm_consommation_requete=0.0,
                        llm_horaires_json="",
                        llm_horaires_osm="",
                        erreurs_pipeline="",
                    )
                    session.add(nouveau_resultat)
                    nouveaux_lieux_count += 1

        if nouveaux_lieux_count > 0:
            self.logger.info(f"{nouveaux_lieux_count} nouveaux enregistrements créés")

        session.commit()

    def get_pending_urls(
        self, execution_id
    ) -> Sequence[Row[Tuple[ResultatsExtraction, Lieux]]]:
        """Récupère les URLs en attente de traitement."""
        session = self.db_manager.Session()
        try:
            return (
                session.query(ResultatsExtraction, Lieux)
                .join(Lieux, ResultatsExtraction.lieu_id == Lieux.identifiant)
                .filter(
                    ResultatsExtraction.id_execution == execution_id,
                    ResultatsExtraction.statut_url != "ok",
                )
                .all()
            )
        finally:
            session.close()

    def get_pending_llm(
        self, execution_id
    ) -> Sequence[Row[Tuple[ResultatsExtraction, Lieux]]]:
        """Récupère les enregistrements en attente d'extraction LLM."""
        session = self.db_manager.Session()
        try:
            return (
                session.query(ResultatsExtraction, Lieux)
                .join(Lieux, ResultatsExtraction.lieu_id == Lieux.identifiant)
                .filter(
                    ResultatsExtraction.id_execution == execution_id,
                    ResultatsExtraction.statut_url == "ok",
                    ResultatsExtraction.markdown_filtre
                    != "",  # Utiliser le markdown filtré
                    ResultatsExtraction.llm_horaires_json == "",
                )
                .all()
            )
        finally:
            session.close()

    def get_results_with_raw_markdown(
        self, execution_id: int
    ) -> Sequence[ResultatsExtraction]:
        """Récupère les résultats avec markdown brut à nettoyer."""
        session = self.db_manager.Session()
        try:
            return (
                session.query(ResultatsExtraction)
                .filter(
                    ResultatsExtraction.id_execution == execution_id,
                    ResultatsExtraction.statut_url == "ok",
                    ResultatsExtraction.markdown_brut != "",
                    ResultatsExtraction.markdown_nettoye == "",
                )
                .all()
            )
        finally:
            session.close()

    def get_results_with_cleaned_markdown(
        self, execution_id: int
    ) -> Sequence[ResultatsExtraction]:
        """Récupère les résultats avec markdown nettoyé à filtrer."""
        session = self.db_manager.Session()
        try:
            return (
                session.query(ResultatsExtraction)
                .filter(
                    ResultatsExtraction.id_execution == execution_id,
                    ResultatsExtraction.markdown_nettoye != "",
                    ResultatsExtraction.markdown_filtre == "",
                )
                .all()
            )
        finally:
            session.close()

    def get_results_with_schedules(self) -> Sequence[ResultatsExtraction]:
        """Récupère les résultats avec horaires extraits pour comparaison."""
        session = self.db_manager.Session()
        try:
            return (
                session.query(ResultatsExtraction)
                .filter(ResultatsExtraction.llm_horaires_json != "")
                .all()
            )
        finally:
            session.close()

    def get_pending_comparisons(
        self,
    ) -> Sequence[Row[Tuple[ResultatsExtraction, Lieux]]]:
        """Récupère les enregistrements en attente de comparaison."""
        session = self.db_manager.Session()
        try:
            return (
                session.query(ResultatsExtraction, Lieux)
                .join(Lieux, ResultatsExtraction.lieu_id == Lieux.identifiant)
                .filter(
                    ResultatsExtraction.llm_horaires_json != "",
                    ResultatsExtraction.llm_horaires_json.notlike("Erreur LLM:%"),
                    (
                        ResultatsExtraction.horaires_identiques.is_(None)
                        | (ResultatsExtraction.horaires_identiques == "")
                    ),
                )
                .all()
            )
        finally:
            session.close()

    def update_comparison_result(self, resultat_id: int, comparison_data: dict):
        """Met à jour le résultat d'une comparaison."""
        session = self.db_manager.Session()
        try:
            resultat = session.get(ResultatsExtraction, resultat_id)
            if resultat:
                setattr(
                    resultat, "horaires_identiques", comparison_data.get("identique")
                )
                setattr(
                    resultat,
                    "differences_horaires",
                    comparison_data.get("differences", ""),
                )

                # Ajouter erreur de comparaison si échec
                if comparison_data.get("identique") is None:
                    self._add_error_to_result(
                        resultat,
                        "COMPARAISON",
                        comparison_data.get("differences", "Erreur inconnue"),
                    )

                session.commit()
        finally:
            session.close()

    def update_url_result(self, resultat_id: int, result_data: dict):
        """Met à jour le résultat d'une extraction URL."""
        session = self.db_manager.Session()
        try:
            resultat = session.get(ResultatsExtraction, resultat_id)
            if resultat:
                # Utiliser setattr pour éviter les erreurs de typage Pylance
                setattr(resultat, "statut_url", result_data.get("statut", "error"))
                setattr(resultat, "code_http", int(result_data.get("code_http", 0)))
                setattr(resultat, "message_url", result_data.get("message", ""))
                setattr(resultat, "markdown_brut", result_data.get("markdown", ""))

                # Ajouter erreur URL si échec
                if result_data.get("statut") != "ok":
                    error_msg = result_data.get("message", "Erreur inconnue")
                    self._add_error_to_result(resultat, "URL", error_msg)

                session.commit()
        finally:
            session.close()

    def update_cleaned_markdown(self, resultat_id: int, cleaned_markdown: str):
        """Met à jour le markdown nettoyé."""
        session = self.db_manager.Session()
        try:
            resultat = session.get(ResultatsExtraction, resultat_id)
            if resultat:
                setattr(resultat, "markdown_nettoye", cleaned_markdown)
                session.commit()
        finally:
            session.close()

    def update_filtered_markdown(
        self, resultat_id: int, filtered_markdown: str, co2_emissions: float = 0.0
    ):
        """Met à jour le markdown filtré et ajoute les émissions CO2."""
        session = self.db_manager.Session()
        try:
            resultat = session.get(ResultatsExtraction, resultat_id)
            if resultat:
                setattr(resultat, "markdown_filtre", filtered_markdown)
                # Ajouter les émissions de l'embedding à la consommation existante
                current_emissions = (
                    getattr(resultat, "llm_consommation_requete", None) or 0.0
                )
                setattr(
                    resultat,
                    "llm_consommation_requete",
                    current_emissions + co2_emissions,
                )
                session.commit()
        finally:
            session.close()

    def update_llm_result(self, resultat_id: int, llm_data: dict):
        """Met à jour le résultat d'une extraction LLM."""
        session = self.db_manager.Session()
        try:
            resultat = session.get(ResultatsExtraction, resultat_id)
            if resultat:
                # Toujours mettre à jour le prompt s'il est fourni
                if llm_data.get("prompt_message"):
                    setattr(resultat, "prompt_message", llm_data["prompt_message"])

                # Mettre à jour la consommation CO2 de la requête
                if "llm_consommation_requete" in llm_data:
                    current_emissions = (
                        getattr(resultat, "llm_consommation_requete", None) or 0.0
                    )
                    setattr(
                        resultat,
                        "llm_consommation_requete",
                        current_emissions + llm_data["llm_consommation_requete"],
                    )

                # Variable pour éviter les erreurs dupliquées
                error_added = False

                # Mettre à jour les résultats LLM (JSON et OSM), y compris les erreurs
                if "llm_horaires_json" in llm_data:
                    setattr(
                        resultat, "llm_horaires_json", llm_data["llm_horaires_json"]
                    )
                    # Ajouter erreur LLM si échec (une seule fois)
                    if (
                        llm_data["llm_horaires_json"].startswith("Erreur")
                        and not error_added
                    ):
                        self._add_error_to_result(
                            resultat, "LLM", llm_data["llm_horaires_json"]
                        )
                        error_added = True

                if "llm_horaires_osm" in llm_data:
                    setattr(resultat, "llm_horaires_osm", llm_data["llm_horaires_osm"])
                    # Ajouter erreur OSM seulement si c'est différent de l'erreur LLM
                    if llm_data["llm_horaires_osm"].startswith("Erreur") and llm_data[
                        "llm_horaires_osm"
                    ] != llm_data.get("llm_horaires_json", ""):
                        self._add_error_to_result(
                            resultat, "OSM", llm_data["llm_horaires_osm"]
                        )

                session.commit()
        finally:
            session.close()

    def update_execution_emissions(self, execution_id: int, total_emissions: float):
        """Met à jour les émissions CO2 totales d'une exécution en les ajoutant au total existant."""
        session = self.db_manager.Session()
        try:
            execution = session.get(Executions, execution_id)
            if execution:
                current_emissions = (
                    getattr(execution, "llm_consommation_execution", None) or 0.0
                )
                setattr(
                    execution,
                    "llm_consommation_execution",
                    current_emissions + total_emissions,
                )
                session.commit()
                self.logger.debug(
                    f"Émissions ajoutées à l'exécution {execution_id}: +{total_emissions:.6f} kg CO2"
                )
        finally:
            session.close()

    def update_execution_embeddings(
        self, execution_id: int, embeddings_emissions: float
    ):
        """Met à jour les émissions CO2 des embeddings d'une exécution."""
        session = self.db_manager.Session()
        try:
            execution = session.get(Executions, execution_id)
            if execution:
                # Ajouter aux émissions existantes (LLM + embeddings)
                current_emissions = (
                    getattr(execution, "llm_consommation_execution", None) or 0.0
                )
                setattr(
                    execution,
                    "llm_consommation_execution",
                    current_emissions + embeddings_emissions,
                )
                session.commit()
                self.logger.debug(
                    f"Émissions embeddings ajoutées à l'exécution {execution_id}: +{embeddings_emissions:.6f} kg CO2"
                )
        finally:
            session.close()

    def add_pipeline_error(self, resultat_id: int, error_type: str, error_message: str):
        """Ajoute une erreur à la chaîne d'erreurs du pipeline."""
        session = self.db_manager.Session()
        try:
            resultat = session.get(ResultatsExtraction, resultat_id)
            if resultat:
                # Créer l'entrée d'erreur avec timestamp
                from datetime import datetime

                timestamp = datetime.now().strftime("%H:%M:%S")
                error_entry = f"[{timestamp}] {error_type}: {error_message}"

                # Ajouter à la chaîne existante en utilisant getattr/setattr
                current_errors = getattr(resultat, "erreurs_pipeline", None) or ""
                if current_errors:
                    new_errors = f"{current_errors} | {error_entry}"
                else:
                    new_errors = error_entry

                setattr(resultat, "erreurs_pipeline", new_errors)
                session.commit()
        finally:
            session.close()

    def _add_error_to_result(self, resultat, error_type: str, error_message: str):
        """Ajoute une erreur à la chaîne d'erreurs (méthode interne)."""
        from datetime import datetime

        timestamp = datetime.now().strftime("%H:%M:%S")
        error_entry = f"[{timestamp}] {error_type}: {error_message}"

        # Utiliser getattr/setattr pour éviter les erreurs de typage
        current_errors = getattr(resultat, "erreurs_pipeline", None) or ""
        if current_errors:
            new_errors = f"{current_errors} | {error_entry}"
        else:
            new_errors = error_entry

        setattr(resultat, "erreurs_pipeline", new_errors)
