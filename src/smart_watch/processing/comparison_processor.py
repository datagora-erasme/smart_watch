# Processeur pour les comparaisons d'horaires.
# https://datagora-erasme.github.io/smart_watch/source/modules/processing/comparison_processor.html

import json
from typing import Dict, Optional, Union, cast

from ..core.ComparateurHoraires import HorairesComparator
from ..core.ConfigManager import ConfigManager
from ..core.Logger import SmartWatchLogger
from ..data_models.schema_bdd import Lieux, ResultatsExtraction
from .database_processor import DatabaseProcessor


class ComparisonProcessor:
    """Processeur pour les comparaisons d'horaires."""

    def __init__(self, config: ConfigManager, logger: SmartWatchLogger) -> None:
        """Initialise le processeur de comparaisons.

        Args:
            config (ConfigManager): Le gestionnaire de configuration.
            logger (SmartWatchLogger): L'instance du logger pour la journalisation.
        """
        self.config = config
        self.logger = logger

    def _compare_single(
        self,
        comparator: HorairesComparator,
        resultat: ResultatsExtraction,
        lieu: Lieux,
    ) -> Dict[str, Union[Optional[bool], str]]:
        """Compare les horaires d'un lieu à partir de différentes sources.

        Cette méthode prend un résultat d'extraction et un lieu, puis compare les
        horaires obtenus par le LLM avec les horaires de référence (data.grandlyon.com).
        Elle gère les erreurs de parsing JSON et les cas où les données sont absentes.

        Args:
            comparator (HorairesComparator): L'instance du comparateur d'horaires.
            resultat (ResultatsExtraction): L'objet contenant les horaires extraits par le LLM.
            lieu (Lieux): L'objet représentant le lieu, contenant les horaires de référence.

        Returns:
            dict: Un dictionnaire contenant le résultat de la comparaison, avec les clés
                  "identique" (booléen ou None) et "differences" (chaîne de caractères).
        """
        try:
            horaires_gl = cast(Optional[str], lieu.horaires_data_gl_json)
            # Vérifier si on a des horaires data.grandlyon.com JSON pour ce lieu
            if horaires_gl is None or horaires_gl.strip() == "":
                return {
                    "identique": None,
                    "differences": "Pas d'horaires de référence data.grandlyon.com disponibles",
                }

            # Charger les horaires data.grandlyon.com (déjà en format JSON)
            try:
                if horaires_gl.startswith("Erreur conversion:"):
                    return {
                        "identique": None,
                        "differences": f"Erreur dans les données GL: {horaires_gl}",
                    }
                horaires_gl_json = json.loads(horaires_gl)
            except json.JSONDecodeError as e:
                return {
                    "identique": None,
                    "differences": f"Erreur parsing JSON data.grandlyon.com: {str(e)}",
                }

            # Charger les horaires extraits par LLM
            horaires_llm = cast(Optional[str], resultat.llm_horaires_json)
            if horaires_llm is None or horaires_llm.strip() == "":
                return {
                    "identique": None,
                    "differences": "Horaires LLM non disponibles (None ou vide).",
                }
            try:
                horaires_llm_json = json.loads(horaires_llm)
            except json.JSONDecodeError as e:
                return {
                    "identique": None,
                    "differences": f"Erreur parsing JSON LLM: {str(e)}",
                }

            # Gérer le cas où le LLM n'a pas trouvé de source d'information.
            # C'est la vérification prioritaire.
            extraction_info = horaires_llm_json.get("extraction_info", {})
            if not extraction_info.get("source_found", True):
                comment = extraction_info.get(
                    "notes", "Aucune source d'horaires trouvée par le LLM."
                )
                return {
                    "identique": None,  # Sera classé comme "Comparaison impossible/Erreur"
                    "differences": f"Comparaison impossible: {comment}",  # C'est l'info qui sera affichée
                }

            # Effectuer la comparaison détaillée
            try:
                comparison_result = comparator.compare_schedules(
                    horaires_gl_json, horaires_llm_json
                )

                # Préparer les résultats structurés
                return {
                    "identique": comparison_result.identical,
                    "differences": comparison_result.differences,
                }

            except Exception as e:
                return {
                    "identique": None,
                    "differences": f"Erreur lors de la comparaison: {str(e)}",
                }

        except Exception as e:
            # Erreur générale non prévue
            return {
                "identique": None,
                "differences": f"Erreur générale: {str(e)}",
            }

    def process_comparisons(self, db_processor: DatabaseProcessor) -> None:
        """
        Compare les horaires extraits avec les références.

        Args:
            db_processor (DatabaseProcessor): Processeur de base de données
        """
        self.logger.section("COMPARAISON HORAIRES")

        try:
            comparator = HorairesComparator()

            # Utiliser la méthode du DatabaseProcessor
            resultats_pour_comparaison = db_processor.get_pending_comparisons()

            if not resultats_pour_comparaison:
                self.logger.info("Aucune comparaison nécessaire")
                return

            self.logger.info(
                f"{len(resultats_pour_comparaison)} comparaisons à effectuer"
            )

            # Afficher la répartition par execution_id pour debug
            executions_stats: Dict[Union[int, str], int] = {}
            for resultat, lieu in resultats_pour_comparaison:
                exec_id = (
                    resultat.id_execution
                    if hasattr(resultat, "id_execution")
                    else "unknown"
                )
                executions_stats[exec_id] = executions_stats.get(exec_id, 0) + 1

            for exec_id, count in executions_stats.items():
                self.logger.info(f"  - Exécution {exec_id}: {count} comparaisons")

            successful_count = 0
            for i, (resultat, lieu) in enumerate(resultats_pour_comparaison, 1):
                lieu_id = (
                    lieu.identifiant if hasattr(lieu, "identifiant") else "unknown"
                )
                lieu_nom = lieu.nom if hasattr(lieu, "nom") else "unknown"
                exec_id = (
                    resultat.id_execution
                    if hasattr(resultat, "id_execution")
                    else "unknown"
                )

                self.logger.info(
                    f"*{lieu_id}* Comparaison {i}/{len(resultats_pour_comparaison)} pour '{lieu_nom}' (exec: {exec_id})"
                )

                try:
                    comparison_result = self._compare_single(comparator, resultat, lieu)

                    # On vérifie simplement que le résultat est un dictionnaire valide
                    if isinstance(comparison_result, dict):
                        # Essayer différents noms d'attributs pour l'ID
                        resultat_id = resultat.id_resultats_extraction

                        if resultat_id is not None:
                            try:
                                db_processor.update_comparison_result(
                                    int(resultat_id),  # Conversion explicite en int
                                    comparison_result,
                                )
                                successful_count += 1
                            except (ValueError, TypeError) as e:
                                self.logger.error(
                                    f"*{lieu_id}* ID invalide ({resultat_id}) pour '{lieu_nom}': {e}"
                                )
                        else:
                            self.logger.error(
                                f"*{lieu_id}* Impossible de trouver l'ID du résultat pour '{lieu_nom}'"
                            )
                    else:
                        self.logger.warning(
                            f"*{lieu_id}* Comparaison a retourné un résultat invalide pour '{lieu_nom}' - Base non modifiée"
                        )

                except Exception as e:
                    self.logger.error(
                        f"*{lieu_id}* Erreur comparaison pour '{lieu_nom}': {e}"
                    )
                    # Ne pas mettre à jour la base en cas d'erreur

            self.logger.info(
                f"Comparaisons: {successful_count}/{len(resultats_pour_comparaison)} réussies"
            )

        except ImportError as e:
            self.logger.error(f"Comparateur non disponible: {e}")
        except Exception as e:
            self.logger.error(f"Erreur comparaisons: {e}")
