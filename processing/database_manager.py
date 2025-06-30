"""
Gestionnaire des opérations de base de données.
"""

import json
from datetime import datetime
from typing import List, Tuple

import requests
from sqlalchemy import create_engine
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import sessionmaker

from assets.schema_bdd import Base, Executions, Lieux, ResultatsExtraction
from core.ConfigManager import ConfigManager


def download_csv(url_or_path, separator=";", has_header=True):
    """Fonction utilitaire pour télécharger un CSV depuis une URL ou charger un fichier local."""
    import polars as pl

    try:
        # Vérifier si c'est une URL
        if url_or_path.startswith(("http://", "https://")):
            # Télécharger depuis l'URL
            response = requests.get(url_or_path, timeout=30)
            response.raise_for_status()

            # Lire directement depuis le contenu téléchargé
            from io import StringIO

            csv_content = StringIO(response.text)
            return pl.read_csv(csv_content, separator=separator, has_header=has_header)
        else:
            # Lire depuis un fichier local
            return pl.read_csv(url_or_path, separator=separator, has_header=has_header)

    except Exception as e:
        raise RuntimeError(f"Erreur chargement CSV {url_or_path}: {e}")


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
            from utils.OSMToCustomJson import OSMToCustomConverter

            osm_converter = OSMToCustomConverter()
        except ImportError:
            self.logger.warning("Convertisseur OSM non disponible")
            osm_converter = None

        for nom, url in self.config.database.csv_file_ref.items():
            try:
                df_ref = download_csv(url)
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
                        markdown="",
                        prompt_message="",
                        llm_consommation_requete="",
                        llm_horaires_json="",
                        llm_horaires_osm="",
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
                    ResultatsExtraction.markdown_horaires
                    != "",  # Changé: utiliser le markdown filtré
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
                resultat.markdown = result_data.get("markdown", "")
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

                # Ne mettre à jour les résultats LLM que s'ils sont fournis et valides
                if llm_data.get("llm_horaires_json") and not llm_data[
                    "llm_horaires_json"
                ].startswith("Erreur"):
                    resultat.llm_horaires_json = llm_data["llm_horaires_json"]

                if llm_data.get("llm_horaires_osm") and not llm_data[
                    "llm_horaires_osm"
                ].startswith("Erreur"):
                    resultat.llm_horaires_osm = llm_data["llm_horaires_osm"]

                session.commit()
        finally:
            session.close()
