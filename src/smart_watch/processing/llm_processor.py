# Processeur pour les extractions LLM.
# Documentation : https://datagora-erasme.github.io/smart_watch/source/modules/processing/llm_processor.html

import json
from datetime import date, datetime
from typing import Any, Dict, cast

import requests

from ..core.ConfigManager import ConfigManager
from ..core.GetPrompt import get_prompt
from ..core.LLMClient import (
    MistralAPIClient,
    OpenAICompatibleClient,
    get_mistral_tool_format,
    get_structured_response_format,
)
from ..core.Logger import SmartWatchLogger
from ..data_models.schema_bdd import Lieux, ResultatsExtraction
from ..processing.database_processor import DatabaseProcessor
from ..utils.CustomJsonToOSM import JsonToOsmConverter
from ..utils.JoursFeries import get_jours_feries


class LLMProcessor:
    """Processeur pour les extractions LLM."""

    def __init__(self, config: ConfigManager, logger: SmartWatchLogger) -> None:
        """
        Initialise le processeur LLM.

        Args:
            config (ConfigManager): L'objet de gestion de la configuration.
            logger (SmartWatchLogger): L'objet logger pour l'enregistrement des messages.
        """
        self.config = config
        self.logger = logger
        self.json_converter = JsonToOsmConverter()
        self._init_llm_client()
        self._load_schema()
        self.total_co2_emissions = 0.0  # Accumulation des émissions pour l'exécution

    def _init_llm_client(self):
        """Initialise le client LLM selon la configuration."""
        llm_config = self.config.llm

        # Vérifier que base_url et api_key ne sont pas None avant de les utiliser
        base_url = llm_config.base_url
        api_key = llm_config.api_key

        if base_url is None:
            raise ValueError("La configuration LLM doit définir une base_url.")
        if api_key is None:
            raise ValueError("La configuration LLM doit définir une api_key.")

        if llm_config.fournisseur == "OPENAI":
            self.llm_client = OpenAICompatibleClient(
                api_key=api_key,
                model=llm_config.modele,
                base_url=base_url,
                temperature=llm_config.temperature,
                timeout=llm_config.timeout,
                seed=llm_config.seed,
            )
        elif llm_config.fournisseur == "MISTRAL":
            self.llm_client = MistralAPIClient(
                api_key=api_key,
                model=llm_config.modele,
                temperature=llm_config.temperature,
                timeout=llm_config.timeout,
                seed=llm_config.seed,
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

    def _is_future_date(self, date_str: str, today: date) -> bool:
        """Vérifie si une chaîne est une date valide au format YYYY-MM-DD et si elle est dans le futur."""
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date() > today
        except ValueError:
            return False

    def _process_special_days(self, llm_result: str, lieu: Lieux) -> str:
        """
        Nettoie les jours spéciaux passés du JSON LLM et l'enrichit avec les jours fériés
        pour les types de lieux spécifiques. Retourne toujours une chaîne JSON valide.
        """
        if not llm_result:
            return "{}"

        try:
            llm_data = json.loads(llm_result)
        except json.JSONDecodeError:
            # Si le résultat n'est pas un JSON valide, retourner un JSON vide.
            return "{}"

        today = datetime.now().date()

        # Nettoyage des horaires spécifiques passés
        periodes = llm_data.get("horaires_ouverture", {}).get("periodes", {})
        for periode_data in periodes.values():
            if "horaires_specifiques" in periode_data and isinstance(
                periode_data["horaires_specifiques"], dict
            ):
                horaires_originaux = periode_data["horaires_specifiques"]
                horaires_filtres = {
                    date_str: value
                    for date_str, value in horaires_originaux.items()
                    if self._is_future_date(date_str, today)
                }
                periode_data["horaires_specifiques"] = horaires_filtres

        # Enrichissement avec les jours fériés pour certains types de lieux
        types_de_lieux_concernes = ["mairie", "bibliothèque"]
        if lieu.type_lieu.lower() in types_de_lieux_concernes:
            try:
                annee_courante = today.year
                jours_feries_courants = get_jours_feries(annee=annee_courante) or {}
                jours_feries_suivants = get_jours_feries(annee=annee_courante + 1) or {}

                jours_feries_courants = {
                    date_ferie: nom_ferie
                    for date_ferie, nom_ferie in jours_feries_courants.items()
                    if self._is_future_date(date_ferie, today)
                }

                tous_jours_feries = {}
                tous_jours_feries.update(jours_feries_courants)
                tous_jours_feries.update(jours_feries_suivants)

                if tous_jours_feries:
                    if "jours_feries" not in periodes:
                        periodes["jours_feries"] = {
                            "source_found": True,
                            "label": "Jours fériés",
                            "condition": "PH",
                            "mode": "ferme",
                            "horaires_specifiques": {},
                            "description": "Jours fériés français - mairie généralement fermée",
                        }
                    horaires_specifiques = periodes["jours_feries"].get(
                        "horaires_specifiques", {}
                    )
                    for date_ferie in tous_jours_feries:
                        if date_ferie not in horaires_specifiques:
                            horaires_specifiques[date_ferie] = "ferme"
                    periodes["jours_feries"]["horaires_specifiques"] = (
                        horaires_specifiques
                    )

            except requests.exceptions.RequestException as e:
                self.logger.warning(
                    f"*{lieu.identifiant}* Impossible de récupérer les jours fériés pour '{lieu.nom}' (erreur réseau): {e}"
                )
            except Exception as e:
                self.logger.error(
                    f"*{lieu.identifiant}* Erreur lors de l'enrichissement des jours fériés pour '{lieu.nom}': {e}"
                )

        return json.dumps(llm_data, ensure_ascii=False)

    def _process_single_llm(
        self, resultat: ResultatsExtraction, lieu: Lieux, index: int = 0, total: int = 0
    ) -> Dict[str, Any]:
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
                        messages,
                        response_format=self.structured_format,
                        index=index,
                        total=total,
                    )
                else:  # MISTRAL
                    llm_response = self.llm_client.call_llm(
                        messages,
                        tool_params=self.structured_format,
                        index=index,
                        total=total,
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
                        processed_result, cast(str, lieu.identifiant)
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
            # Retourner un dictionnaire d'erreur au lieu de None
            return {
                "prompt_message": "",
                "llm_horaires_json": f"Erreur: Aucun résultat LLM ({str(e)})",
                "llm_horaires_osm": f"Erreur: Aucun résultat LLM ({str(e)})",
                "llm_consommation_requete": 0.0,
            }

    def process_llm_extractions(
        self, db_processor: DatabaseProcessor, execution_id: int
    ) -> None:
        """
        Traite toutes les extractions LLM pour une exécution donnée.

        Args:
            db_processor (DatabaseProcessor): Processeur de base de données
            execution_id (int): ID de l'exécution
        """
        # Récupérer les résultats prêts pour l'extraction LLM
        pending_llm = db_processor.get_pending_llm(execution_id)
        total_llm = len(pending_llm)

        for index, result_row in enumerate(pending_llm, 1):
            resultat, lieu = result_row

            # Extraction via LLM
            llm_result = self._process_single_llm(
                resultat, lieu, index=index, total=total_llm
            )

            # Mettre à jour en base
            db_processor.update_llm_result(resultat.id_resultats_extraction, llm_result)

            # Mettre à jour les émissions totales de l'exécution
            if "llm_consommation_requete" in llm_result:
                db_processor.update_execution_emissions(
                    execution_id, llm_result["llm_consommation_requete"]
                )
