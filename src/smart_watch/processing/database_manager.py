"""
Gestionnaire des opérations de base de données.
"""

import json
from datetime import datetime
from typing import List, Tuple

from sqlalchemy import create_engine
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import sessionmaker

from ..core.ConfigManager import ConfigManager
from ..data_models.schema_bdd import (
    Base,
    Executions,
    Lieux,
    ResultatsExtraction,
)
from ..utils.CSVToPolars import CSVToPolars
from ..utils.OSMToCustomJson import OsmToJsonConverter


class DatabaseManager:
    """Gestionnaire des opérations de base de données."""

    def __init__(self, config: ConfigManager, logger):
        self.config = config
        self.logger = logger
        self.engine = create_engine(f"sqlite:///{config.database.db_file}")
        self.Session = sessionmaker(bind=self.engine)

        # Créer les tables si nécessaire
        Base.metadata.create_all(self.engine)

    def setup_execution(self, df_csv) -> int:
        """Configure une nouvelle exécution et retourne son ID."""
        session = self.Session()
        try:
            # Mise à jour des lieux
            self._update_lieux_batch(session, df_csv)

            # Mise à jour des références GL
            self._update_horaires_lieux_depuis_gl(session)

            # Création de l'exécution
            execution_id = self._create_execution(session)

            # Configuration des résultats d'extraction
            self._setup_resultats_extraction(session, df_csv, execution_id)

            return execution_id
        finally:
            session.close()

    def _update_lieux_batch(self, session, df_csv):
        """Met à jour les lieux par batch pour plus d'efficacité."""
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
        """Met à jour les horaires des lieux depuis data.grandlyon.com."""
        try:
            osm_converter = OsmToJsonConverter()
        except ImportError:
            self.logger.error("Convertisseur OSM non disponible")
            osm_converter = None

        for nom, url in self.config.database.csv_file_ref.items():
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
                                    f"Erreur conversion {row['identifiant']}: {e}"
                                )

                session.commit()
                self.logger.info(f"Références {nom} mises à jour: {count} lieux")

            except Exception as e:
                self.logger.error(f"Erreur chargement {nom}: {e}")

    def _create_execution(self, session) -> int:
        """Crée une nouvelle exécution et retourne son ID."""
        nouvelle_execution = Executions(
            date_execution=datetime.now(),
            llm_modele=self.config.llm.modele,
            llm_fournisseur=self.config.llm.fournisseur,
            llm_url=self.config.llm.base_url,
        )
        session.add(nouvelle_execution)
        session.commit()

        execution_id = nouvelle_execution.id_executions
        self.logger.info(f"Nouvelle exécution créée: {execution_id}")

        return execution_id

    def _setup_resultats_extraction(self, session, df_csv, execution_id):
        """Configure les résultats d'extraction."""
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
                    f"Enregistrement '{lieu.identifiant}' assigné à l'exécution {execution_id} pour reprise"
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

            # La vérification des comparaisons manquantes est gérée globalement par le ComparisonProcessor.
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

    def get_pending_urls(self, execution_id) -> List[Tuple]:
        """Récupère les URLs en attente de traitement."""
        session = self.Session()
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

    def get_pending_llm(self, execution_id) -> List[Tuple]:
        """Récupère les enregistrements en attente d'extraction LLM."""
        session = self.Session()
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

    def update_url_result(self, resultat_id: int, result_data: dict):
        """Met à jour le résultat d'une extraction URL."""
        session = self.Session()
        try:
            resultat = session.get(ResultatsExtraction, resultat_id)
            if resultat:
                resultat.statut_url = result_data.get("statut", "error")
                resultat.code_http = int(result_data.get("code_http", 0))
                resultat.message_url = result_data.get("message", "")
                resultat.markdown_brut = result_data.get(
                    "markdown", ""
                )  # Sauvegarder comme markdown brut

                # Ajouter erreur URL si échec
                if result_data.get("statut") != "ok":
                    error_msg = result_data.get("message", "Erreur inconnue")
                    self._add_error_to_result(resultat, "URL", error_msg)

                session.commit()
        finally:
            session.close()

    def update_cleaned_markdown(self, resultat_id: int, cleaned_markdown: str):
        """Met à jour le markdown nettoyé."""
        session = self.Session()
        try:
            resultat = session.get(ResultatsExtraction, resultat_id)
            if resultat:
                resultat.markdown_nettoye = cleaned_markdown
                session.commit()
        finally:
            session.close()

    def update_filtered_markdown(
        self, resultat_id: int, filtered_markdown: str, co2_emissions: float = 0.0
    ):
        """Met à jour le markdown filtré et ajoute les émissions CO2."""
        session = self.Session()
        try:
            resultat = session.get(ResultatsExtraction, resultat_id)
            if resultat:
                resultat.markdown_filtre = filtered_markdown
                # Ajouter les émissions de l'embedding à la consommation existante
                current_emissions = resultat.llm_consommation_requete or 0.0
                resultat.llm_consommation_requete = current_emissions + co2_emissions
                session.commit()
        finally:
            session.close()

    def update_llm_result(self, resultat_id: int, llm_data: dict):
        """Met à jour le résultat d'une extraction LLM."""
        session = self.Session()
        try:
            resultat = session.get(ResultatsExtraction, resultat_id)
            if resultat:
                # Toujours mettre à jour le prompt s'il est fourni
                if llm_data.get("prompt_message"):
                    resultat.prompt_message = llm_data["prompt_message"]

                # Mettre à jour la consommation CO2 de la requête
                if "llm_consommation_requete" in llm_data:
                    current_emissions = resultat.llm_consommation_requete or 0.0
                    resultat.llm_consommation_requete = (
                        current_emissions + llm_data["llm_consommation_requete"]
                    )

                # Variable pour éviter les erreurs dupliquées
                error_added = False

                # Mettre à jour les résultats LLM (JSON et OSM), y compris les erreurs
                if "llm_horaires_json" in llm_data:
                    resultat.llm_horaires_json = llm_data["llm_horaires_json"]
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
                    resultat.llm_horaires_osm = llm_data["llm_horaires_osm"]
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
        session = self.Session()
        try:
            execution = session.get(Executions, execution_id)
            if execution:
                current_emissions = execution.llm_consommation_execution or 0.0
                execution.llm_consommation_execution = (
                    current_emissions + total_emissions
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
        session = self.Session()
        try:
            execution = session.get(Executions, execution_id)
            if execution:
                # Ajouter aux émissions existantes (LLM + embeddings)
                current_emissions = execution.llm_consommation_execution or 0.0
                execution.llm_consommation_execution = (
                    current_emissions + embeddings_emissions
                )
                session.commit()
                self.logger.debug(
                    f"Émissions embeddings ajoutées à l'exécution {execution_id}: +{embeddings_emissions:.6f} kg CO2"
                )
        finally:
            session.close()

    def add_pipeline_error(self, resultat_id: int, error_type: str, error_message: str):
        """Ajoute une erreur à la chaîne d'erreurs du pipeline."""
        session = self.Session()
        try:
            resultat = session.get(ResultatsExtraction, resultat_id)
            if resultat:
                # Créer l'entrée d'erreur avec timestamp
                from datetime import datetime

                timestamp = datetime.now().strftime("%H:%M:%S")
                error_entry = f"[{timestamp}] {error_type}: {error_message}"

                # Ajouter à la chaîne existante
                if resultat.erreurs_pipeline:
                    resultat.erreurs_pipeline += f" | {error_entry}"
                else:
                    resultat.erreurs_pipeline = error_entry

                session.commit()
        finally:
            session.close()

    def _add_error_to_result(self, resultat, error_type: str, error_message: str):
        """Ajoute une erreur à la chaîne d'erreurs (méthode interne)."""
        from datetime import datetime

        timestamp = datetime.now().strftime("%H:%M:%S")
        error_entry = f"[{timestamp}] {error_type}: {error_message}"

        if resultat.erreurs_pipeline:
            resultat.erreurs_pipeline += f" | {error_entry}"
        else:
            resultat.erreurs_pipeline = error_entry
