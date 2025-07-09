"""
Processeur pour les extractions LLM.
"""

import json
import time
from datetime import datetime
from typing import Dict

from ..core.ConfigManager import ConfigManager
from ..core.GetPrompt import get_prompt
from ..core.LLMClient import (
    LLMResponse,
    MistralAPIClient,
    OpenAICompatibleClient,
    get_mistral_tool_format,
    get_structured_response_format,
)
from ..utils.CustomJsonToOSM import OSMConverter
from ..utils.JoursFeries import get_jours_feries
from .database_manager import DatabaseManager
from .url_processor import ProcessingStats


class LLMProcessor:
    """Processeur pour les extractions LLM."""

    def __init__(self, config: ConfigManager, logger):
        self.config = config
        self.logger = logger
        self.converter = OSMConverter()
        self._init_llm_client()
        self._load_schema()
        self.total_co2_emissions = 0.0  # Accumulation des émissions pour l'exécution

    def _init_llm_client(self):
        """Initialise le client LLM selon la configuration."""
        llm_config = self.config.llm

        if llm_config.fournisseur == "OPENAI":
            self.llm_client = OpenAICompatibleClient(
                api_key=llm_config.api_key,
                model=llm_config.modele,
                base_url=llm_config.base_url,
                temperature=llm_config.temperature,
                timeout=llm_config.timeout,
            )
        elif llm_config.fournisseur == "MISTRAL":
            self.llm_client = MistralAPIClient(
                api_key=llm_config.api_key,
                model=llm_config.modele,
                temperature=llm_config.temperature,
                timeout=llm_config.timeout,
            )
        else:
            raise ValueError(f"Fournisseur LLM non supporté: {llm_config.fournisseur}")

    def _load_schema(self):
        """Charge le schéma JSON pour les structured outputs."""
        with open(self.config.database.schema_file, "r", encoding="utf-8") as f:
            schema = json.load(f)

        if self.config.llm.fournisseur == "OPENAI":
            self.structured_format = get_structured_response_format(
                schema=schema, name="opening_hours_extraction"
            )
        else:  # MISTRAL
            self.structured_format = get_mistral_tool_format(
                schema=schema, function_name="opening_hours_extraction"
            )

        self.opening_hours_schema = schema

    def _convert_to_osm(self, llm_result: str, identifiant: str) -> str:
        """Convertit le résultat LLM au format OSM."""
        try:
            if llm_result is None or llm_result.startswith("Erreur"):
                return ""

            llm_horaires_json = json.loads(llm_result)
            conversion_result = self.converter.convert_to_osm(llm_horaires_json)

            if conversion_result.osm_periods:
                return " / ".join(
                    [
                        f"{period}: {osm_format}"
                        for period, osm_format in conversion_result.osm_periods.items()
                    ]
                )
            return "No periods found"

        except Exception as e:
            self.logger.error(f"Erreur conversion OSM {identifiant}: {e}")
            return f"Erreur Conversion OSM: {e}"

    def _enrich_with_jours_feries(self, llm_result: str, lieu) -> str:
        """Enrichit le JSON LLM avec les jours fériés pour les mairies."""
        try:
            # Définir les types de lieux pour l'enrichissement des jours fériés
            types_de_lieux_concernes = ["mairie", "bibliothèque"]

            # Vérifier si le type de lieu est concerné
            if lieu.type_lieu.lower() not in types_de_lieux_concernes:
                return llm_result

            self.logger.debug(f"Enrichissement jours fériés pour mairie: {lieu.nom}")

            # Parser le JSON LLM
            llm_data = json.loads(llm_result)

            # Récupérer les jours fériés pour année courante et suivante
            annee_courante = datetime.now().year
            jours_feries_courants = get_jours_feries(annee=annee_courante)
            jours_feries_suivants = get_jours_feries(annee=annee_courante + 1)

            if not jours_feries_courants and not jours_feries_suivants:
                self.logger.warning(
                    f"Impossible de récupérer les jours fériés pour {lieu.nom}"
                )
                return llm_result

            # Filtrer les jours fériés pour ne garder que ceux qui dépassent
            # la date actuelle (pour éviter les jours fériés passés)
            jours_feries_courants = {
                date_ferie: nom_ferie
                for date_ferie, nom_ferie in jours_feries_courants.items()
                if datetime.strptime(date_ferie, "%Y-%m-%d") >= datetime.now()
            }

            # Combiner les jours fériés des deux années
            tous_jours_feries = {}
            if jours_feries_courants:
                tous_jours_feries.update(jours_feries_courants)
            if jours_feries_suivants:
                tous_jours_feries.update(jours_feries_suivants)

            # Accéder à la structure des périodes
            periodes = llm_data.get("horaires_ouverture", {}).get("periodes", {})

            # Ajouter ou mettre à jour la section jours_feries
            if "jours_feries" not in periodes:
                periodes["jours_feries"] = {
                    "source_found": False,
                    "label": "Jours fériés",
                    "condition": "PH",
                    "mode": "ferme",
                    "horaires_specifiques": {},
                    "description": "Jours fériés français - mairie généralement fermée",
                }

            # Récupérer les horaires spécifiques existants
            horaires_specifiques = periodes["jours_feries"].get(
                "horaires_specifiques", {}
            )

            # IMPORTANT: Ne pas écraser les jours fériés déjà présents
            # Compter seulement les nouveaux jours fériés ajoutés
            nouveaux_jours_feries = 0

            for date_ferie, nom_ferie in tous_jours_feries.items():
                # N'ajouter que si la date n'existe pas déjà
                if date_ferie not in horaires_specifiques:
                    horaires_specifiques[date_ferie] = "ferme"
                    nouveaux_jours_feries += 1
                    self.logger.debug(f"Ajout jour férié: {date_ferie} - {nom_ferie}")
                else:
                    self.logger.debug(f"Jour férié déjà présent: {date_ferie}")

            # Mettre à jour la structure seulement si on a ajouté des jours fériés
            if nouveaux_jours_feries > 0 or len(horaires_specifiques) > 0:
                periodes["jours_feries"]["horaires_specifiques"] = horaires_specifiques
                periodes["jours_feries"]["source_found"] = True

                self.logger.info(
                    f"Enrichissement jours fériés pour {lieu.nom}: {nouveaux_jours_feries} nouveaux, {len(horaires_specifiques)} total"
                )
            else:
                self.logger.debug(f"Aucun nouveau jour férié ajouté pour {lieu.nom}")

            return json.dumps(llm_data, ensure_ascii=False)

        except Exception as e:
            self.logger.error(
                f"Erreur enrichissement jours fériés pour {lieu.identifiant}: {e}"
            )
            return llm_result

    def _process_single_llm(self, resultat, lieu) -> Dict:
        """Traite une extraction LLM individuelle."""
        try:
            # Préparation des données - utiliser le markdown filtré
            row_data = {
                "identifiant": lieu.identifiant,
                "nom": lieu.nom,
                "url": lieu.url,
                "type_lieu": lieu.type_lieu,
                "markdown": resultat.markdown_filtre
                or resultat.markdown_nettoye
                or resultat.markdown_brut,
            }

            messages = get_prompt(row_data, self.opening_hours_schema)
            prompt_message = json.dumps(messages, ensure_ascii=False)

            # Préparer le résultat avec au minimum le prompt
            result_data = {
                "prompt_message": prompt_message,
                "llm_horaires_json": "",
                "llm_horaires_osm": "",
                "llm_consommation_requete": 0.0,
            }

            try:
                # Appel LLM avec mesure d'émissions selon le fournisseur
                if self.config.llm.fournisseur == "OPENAI":
                    llm_response: LLMResponse = self.llm_client.call_llm(
                        messages, response_format=self.structured_format
                    )
                else:  # MISTRAL
                    llm_response: LLMResponse = self.llm_client.call_llm(
                        messages, tool_params=self.structured_format
                    )

                # Enregistrer les émissions individuelles AVANT accumulation
                individual_emissions = llm_response.co2_emissions
                result_data["llm_consommation_requete"] = individual_emissions

                # Logger les émissions individuelles
                self.logger.debug(
                    f"[{lieu.identifiant}] Émissions CO2 cette requête: {individual_emissions:.6f} kg"
                )

                # Puis accumuler pour le total
                self.total_co2_emissions += individual_emissions

                # Vérifier si l'appel LLM a réussi
                if llm_response.content is not None and not str(
                    llm_response.content
                ).startswith("Erreur"):
                    # Enrichissement avec les jours fériés pour les mairies
                    enriched_result = self._enrich_with_jours_feries(
                        llm_response.content, lieu
                    )

                    # Conversion OSM seulement si LLM a réussi
                    try:
                        osm_result = self._convert_to_osm(
                            enriched_result, lieu.identifiant
                        )
                        result_data["llm_horaires_json"] = enriched_result
                        result_data["llm_horaires_osm"] = osm_result
                    except Exception as e:
                        self.logger.error(
                            f"Erreur conversion OSM pour {lieu.identifiant}: {e}"
                        )
                        result_data["llm_horaires_json"] = enriched_result
                        result_data["llm_horaires_osm"] = f"Erreur Conversion OSM: {e}"
                else:
                    # Gestion des erreurs LLM avec messages plus explicites
                    if llm_response.content is None:
                        error_msg = (
                            f"Erreur LLM: reçu '{llm_response.content}' - réponse vide"
                        )
                    elif str(llm_response.content).startswith("Erreur"):
                        error_msg = str(llm_response.content)
                    else:
                        error_msg = f"Erreur LLM: reçu '{llm_response.content}' - réponse inattendue"

                    self.logger.error(
                        f"Appel LLM échoué pour {lieu.identifiant}: {error_msg}"
                    )
                    result_data["llm_horaires_json"] = error_msg
                    result_data["llm_horaires_osm"] = error_msg

            except Exception as e:
                self.logger.error(
                    f"Erreur lors de l'appel LLM pour {lieu.identifiant}: {e}"
                )
                error_msg = f"Erreur LLM: {e}"
                result_data["llm_horaires_json"] = error_msg
                result_data["llm_horaires_osm"] = error_msg

            return result_data

        except Exception as e:
            self.logger.error(f"Erreur critique traitement LLM {lieu.identifiant}: {e}")
            return None

    def process_llm_extractions(
        self, db_manager: DatabaseManager, execution_id: int
    ) -> ProcessingStats:
        """Traite les extractions LLM."""
        self.logger.section("EXTRACTION HORAIRES LLM")

        # Reset des émissions pour cette exécution
        self.total_co2_emissions = 0.0

        resultats_pour_llm = db_manager.get_pending_llm(execution_id)
        stats = ProcessingStats()

        if not resultats_pour_llm:
            self.logger.info("Aucune extraction LLM nécessaire")
            return stats

        self.logger.info(f"{len(resultats_pour_llm)} extractions LLM à effectuer")
        stats.llm_processed = len(resultats_pour_llm)

        # Traitement séquentiel
        for i, (resultat, lieu) in enumerate(resultats_pour_llm, 1):
            self.logger.info(f"LLM {i}/{len(resultats_pour_llm)}: {lieu.nom}")

            try:
                llm_result = self._process_single_llm(resultat, lieu)

                # Toujours mettre à jour la base, même en cas d'erreur LLM
                if llm_result is not None:
                    db_manager.update_llm_result(
                        resultat.id_resultats_extraction, llm_result
                    )

                    # Compter comme succès seulement si on a un résultat JSON valide
                    if llm_result.get("llm_horaires_json") and not llm_result[
                        "llm_horaires_json"
                    ].startswith("Erreur"):
                        stats.llm_successful += 1
                else:
                    # Erreur critique (pas de prompt généré)
                    self.logger.warning(
                        f"Échec critique LLM pour {lieu.nom} - aucune donnée générée"
                    )

                # Délai adaptatif
                if i < len(resultats_pour_llm):
                    delay = self.config.processing.delai_entre_appels
                    if llm_result is None or (
                        llm_result.get("llm_horaires_json", "").startswith("Erreur")
                    ):
                        delay = self.config.processing.delai_en_cas_erreur
                    time.sleep(delay)

            except Exception as e:
                self.logger.error(f"Erreur LLM pour {lieu.nom}: {e}")
                # Ne pas mettre à jour la base de données en cas d'exception

        # Mettre à jour les émissions totales dans la table executions
        db_manager.update_execution_emissions(execution_id, self.total_co2_emissions)

        self.logger.info(
            f"LLM traité: {stats.llm_successful}/{stats.llm_processed} réussies"
        )
        self.logger.info(
            f"Émissions CO2 (appels LLM): {self.total_co2_emissions:.6f} kg"
        )

        return stats
