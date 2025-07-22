"""
Processeur pour les extractions LLM.
"""

import json
import time
from datetime import datetime
from typing import Dict

import requests

from ..core.ConfigManager import ConfigManager
from ..core.GetPrompt import get_prompt
from ..core.LLMClient import (
    MistralAPIClient,
    OpenAICompatibleClient,
    get_mistral_tool_format,
    get_structured_response_format,
)
from ..utils.CustomJsonToOSM import JsonToOsmConverter
from ..utils.JoursFeries import get_jours_feries
from .database_processor import DatabaseProcessor


class LLMProcessor:
    """Processeur pour les extractions LLM."""

    def __init__(self, config: ConfigManager, logger):
        self.config = config
        self.logger = logger
        self.json_converter = JsonToOsmConverter()
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
        if not llm_result or llm_result.startswith("Erreur"):
            return ""

        try:
            llm_data = json.loads(llm_result)
        except json.JSONDecodeError as e:
            self.logger.warning(
                f"*{identifiant}* Le résultat LLM pour n'est pas un JSON valide: {e}"
            )
            return "Erreur Conversion OSM: JSON invalide"

        # L'appel à convert_to_osm est maintenant sécurisé par le @handle_errors
        # Il ne lèvera plus d'exception mais retournera un résultat vide en cas d'erreur.
        conversion_result = self.json_converter.convert_to_osm(llm_data)

        # Joindre les différentes périodes OSM en une seule chaîne
        osm_horaires = "; ".join(
            f"{period_name}: {osm_string}"
            for period_name, osm_string in conversion_result.osm_periods.items()
            if osm_string and period_name != "general"
        )

        # Ajouter la période générale si elle existe
        general_schedule = conversion_result.osm_periods.get("general")
        if general_schedule:
            if osm_horaires:
                osm_horaires = f"{general_schedule}; {osm_horaires}"
            else:
                osm_horaires = general_schedule

        if not osm_horaires:
            self.logger.debug(
                f"*{identifiant}* La conversion OSM n'a produit aucun résultat."
            )

        return osm_horaires

    def _process_special_days(self, llm_result: str, lieu) -> str:
        """
        Nettoie les jours spéciaux passés du JSON LLM et l'enrichit avec les jours fériés
        pour les types de lieux spécifiques.
        """
        try:
            llm_data = json.loads(llm_result)
            today = datetime.now().date()

            # Étape 1: Nettoyer systématiquement les horaires spécifiques passés pour tous les lieux.
            self.logger.debug(
                f"*{lieu.identifiant}* Nettoyage des jours passés pour '{lieu.nom}'"
            )
            periodes = llm_data.get("horaires_ouverture", {}).get("periodes", {})
            for periode_key, periode_data in periodes.items():
                if "horaires_specifiques" in periode_data and isinstance(
                    periode_data["horaires_specifiques"], dict
                ):
                    horaires_originaux = periode_data["horaires_specifiques"]
                    horaires_filtres = {}
                    for date_str, value in horaires_originaux.items():
                        try:
                            # Conserver uniquement les dates strictement futures
                            if datetime.strptime(date_str, "%Y-%m-%d").date() > today:
                                horaires_filtres[date_str] = value
                        except ValueError:
                            self.logger.warning(
                                f"*{lieu.identifiant}* Format de date invalide '{date_str}' dans les horaires spécifiques pour '{lieu.nom}', ignoré."
                            )

                    if len(horaires_filtres) < len(horaires_originaux):
                        self.logger.debug(
                            f"*{lieu.identifiant}* Nettoyage de {len(horaires_originaux) - len(horaires_filtres)} jour(s) spécial(aux) passé(s) pour la période '{periode_key}' de '{lieu.nom}'"
                        )
                    periode_data["horaires_specifiques"] = horaires_filtres

            # Étape 2: Enrichir avec les jours fériés uniquement pour certains types de lieux.
            types_de_lieux_concernes = ["mairie", "bibliothèque"]
            if lieu.type_lieu.lower() not in types_de_lieux_concernes:
                # Retourner le JSON nettoyé si le lieu n'est pas concerné par l'enrichissement.
                return json.dumps(llm_data, ensure_ascii=False)

            self.logger.debug(
                f"*{lieu.identifiant}* Enrichissement en jours fériés pour '{lieu.nom}'"
            )

            # Récupérer et ajouter les jours fériés futurs
            annee_courante = today.year
            jours_feries_courants = get_jours_feries(annee=annee_courante) or {}
            jours_feries_suivants = get_jours_feries(annee=annee_courante + 1) or {}

            # Filtrer pour ne garder que les jours fériés strictement futurs
            jours_feries_courants = {
                date_ferie: nom_ferie
                for date_ferie, nom_ferie in jours_feries_courants.items()
                if datetime.strptime(date_ferie, "%Y-%m-%d").date() > today
            }

            tous_jours_feries = {}
            tous_jours_feries.update(jours_feries_courants)
            tous_jours_feries.update(jours_feries_suivants)

            if not tous_jours_feries:
                self.logger.debug(
                    f"*{lieu.identifiant}* Aucun jour férié futur à ajouter pour '{lieu.nom}'. Le nettoyage a peut-être eu lieu."
                )
                return json.dumps(llm_data, ensure_ascii=False)

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

            horaires_specifiques = periodes["jours_feries"].get(
                "horaires_specifiques", {}
            )
            nouveaux_jours_feries = 0
            for date_ferie, nom_ferie in tous_jours_feries.items():
                if date_ferie not in horaires_specifiques:
                    horaires_specifiques[date_ferie] = "ferme"
                    nouveaux_jours_feries += 1
                    self.logger.debug(
                        f"*{lieu.identifiant}* Ajout jour férié pour '{lieu.nom}': {date_ferie} - {nom_ferie}"
                    )

            if nouveaux_jours_feries > 0:
                periodes["jours_feries"]["horaires_specifiques"] = horaires_specifiques
                periodes["jours_feries"]["source_found"] = True
                self.logger.info(
                    f"*{lieu.identifiant}* Enrichissement pour '{lieu.nom}': {nouveaux_jours_feries} nouveaux jours fériés ajoutés."
                )

            return json.dumps(llm_data, ensure_ascii=False)

        except requests.exceptions.RequestException as e:
            self.logger.warning(
                f"*{lieu.identifiant}* Impossible de récupérer les jours fériés pour '{lieu.nom}' (erreur réseau): {e}"
            )
            return llm_result
        except Exception as e:
            self.logger.error(
                f"*{lieu.identifiant}* Erreur lors du traitement des jours spéciaux pour '{lieu.nom}': {e}"
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
                # Appel LLM
                if self.config.llm.fournisseur == "OPENAI":
                    llm_response = self.llm_client.call_llm(
                        messages, response_format=self.structured_format
                    )
                else:  # MISTRAL
                    llm_response = self.llm_client.call_llm(
                        messages, tool_params=self.structured_format
                    )

                # Vérifier si la réponse est un objet LLMResponse ou une chaîne d'erreur
                if isinstance(llm_response, str):
                    # La réponse est une chaîne d'erreur
                    self.logger.error(
                        f"*{lieu.identifiant}* Appel LLM échoué pour '{lieu.nom}': {llm_response}"
                    )
                    result_data["llm_horaires_json"] = f"Erreur LLM: {llm_response}"
                    result_data["llm_horaires_osm"] = f"Erreur LLM: {llm_response}"
                    result_data["llm_consommation_requete"] = 0.0
                    return result_data

                # Vérifier si c'est bien un objet LLMResponse
                if not hasattr(llm_response, "co2_emissions"):
                    self.logger.error(
                        f"*{lieu.identifiant}* Réponse LLM inattendue pour '{lieu.nom}': {type(llm_response)}"
                    )
                    result_data["llm_horaires_json"] = "Erreur LLM: réponse inattendue"
                    result_data["llm_horaires_osm"] = "Erreur LLM: réponse inattendue"
                    result_data["llm_consommation_requete"] = 0.0
                    return result_data

                # Enregistrer les émissions individuelles AVANT accumulation
                individual_emissions = llm_response.co2_emissions
                result_data["llm_consommation_requete"] = individual_emissions

                # Logger les émissions individuelles
                self.logger.debug(
                    f"*{lieu.identifiant}* Émissions CO2 pour cette requête pour '{lieu.nom}': {individual_emissions:.6f} kg"
                )

                # Puis accumuler pour le total
                self.total_co2_emissions += individual_emissions

                # Vérifier si l'appel LLM a réussi
                if llm_response.content and not str(llm_response.content).startswith(
                    "Erreur"
                ):
                    # Traitement des jours spéciaux (nettoyage et enrichissement)
                    processed_result = self._process_special_days(
                        llm_response.content, lieu
                    )

                    # Conversion OSM (le try/except n'est plus nécessaire ici)
                    osm_result = self._convert_to_osm(
                        processed_result, lieu.identifiant
                    )
                    result_data["llm_horaires_json"] = processed_result
                    result_data["llm_horaires_osm"] = osm_result
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
                        f"*{lieu.identifiant}* Appel LLM échoué pour '{lieu.nom}': {error_msg}"
                    )
                    result_data["llm_horaires_json"] = error_msg
                    result_data["llm_horaires_osm"] = error_msg

            except Exception as e:
                self.logger.error(
                    f"*{lieu.identifiant}* Erreur lors de l'appel LLM pour '{lieu.nom}': {e}"
                )
                error_msg = f"Erreur LLM: {e}"
                result_data["llm_horaires_json"] = error_msg
                result_data["llm_horaires_osm"] = error_msg

            return result_data

        except Exception as e:
            self.logger.error(
                f"*{lieu.identifiant}* Erreur critique traitement LLM pour '{lieu.nom}': {e}"
            )
            return None

    def process_llm_extractions(self, db_manager: DatabaseProcessor, execution_id: int):
        """Traite les extractions LLM."""
        self.logger.section("EXTRACTION HORAIRES LLM")

        # Reset des émissions pour cette exécution
        self.total_co2_emissions = 0.0

        resultats_pour_llm = db_manager.get_pending_llm(execution_id)

        if not resultats_pour_llm:
            self.logger.info("Aucune extraction LLM nécessaire")
            return

        self.logger.info(f"{len(resultats_pour_llm)} extractions LLM à effectuer")

        # Traitement séquentiel
        successful_count = 0
        for i, (resultat, lieu) in enumerate(resultats_pour_llm, 1):
            self.logger.info(
                f"*{lieu.identifiant}* LLM {i}/{len(resultats_pour_llm)} pour '{lieu.nom}'"
            )

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
                        successful_count += 1
                else:
                    # Erreur critique (pas de prompt généré)
                    self.logger.warning(
                        f"*{lieu.identifiant}* Échec critique LLM pour '{lieu.nom}' - aucune donnée générée"
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
                self.logger.error(
                    f"*{lieu.identifiant}* Erreur LLM pour '{lieu.nom}': {e}"
                )
                # Ne pas mettre à jour la base de données en cas d'exception

        # Mettre à jour les émissions totales dans la table executions
        db_manager.update_execution_emissions(execution_id, self.total_co2_emissions)

        self.logger.info(
            f"LLM traité: {successful_count}/{len(resultats_pour_llm)} réussies"
        )
        self.logger.info(
            f"Émissions CO2 (appels LLM): {self.total_co2_emissions:.6f} kg"
        )
