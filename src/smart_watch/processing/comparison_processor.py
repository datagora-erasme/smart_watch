"""
Processeur pour les comparaisons d'horaires.
"""

import json
from typing import Dict, List, Tuple

from ..core.ComparateurHoraires import HorairesComparator
from ..core.ConfigManager import ConfigManager
from ..data_models.schema_bdd import Lieux, ResultatsExtraction
from .database_processor import DatabaseProcessor


class ComparisonProcessor:
    """Processeur pour les comparaisons d'horaires."""

    def __init__(self, config: ConfigManager, logger):
        self.config = config
        self.logger = logger

    def _get_pending_comparisons(self, db_manager: DatabaseProcessor) -> List[Tuple]:
        """Récupère les enregistrements en attente de comparaison."""
        session = db_manager.Session()
        try:
            # Récupérer TOUS les enregistrements qui ont besoin d'une comparaison
            # peu importe leur execution_id
            return (
                session.query(ResultatsExtraction, Lieux)
                .join(Lieux, ResultatsExtraction.lieu_id == Lieux.identifiant)
                .filter(
                    ResultatsExtraction.llm_horaires_json != "",
                    ResultatsExtraction.llm_horaires_json.notlike("Erreur LLM:%"),
                    # Condition principale : comparaison pas encore effectuée (NULL ou vide)
                    (
                        ResultatsExtraction.horaires_identiques.is_(None)
                        | (ResultatsExtraction.horaires_identiques == "")
                    ),
                )
                .all()
            )
        finally:
            session.close()

    def _compare_single(self, comparator, resultat, lieu) -> Dict:
        """Compare un seul enregistrement et retourne les résultats structurés."""
        try:
            # Vérifier si on a des horaires data.grandlyon.com JSON pour ce lieu
            if (
                not lieu.horaires_data_gl_json
                or lieu.horaires_data_gl_json.strip() == ""
            ):
                return {
                    "identique": None,
                    "differences": "Pas d'horaires de référence data.grandlyon.com disponibles",
                }

            # Charger les horaires data.grandlyon.com (déjà en format JSON)
            try:
                if lieu.horaires_data_gl_json.startswith("Erreur conversion:"):
                    return {
                        "identique": None,
                        "differences": f"Erreur dans les données GL: {lieu.horaires_data_gl_json}",
                    }

                horaires_gl_json = json.loads(lieu.horaires_data_gl_json)
            except json.JSONDecodeError as e:
                return {
                    "identique": None,
                    "differences": f"Erreur parsing JSON data.grandlyon.com: {str(e)}",
                }

            # Charger les horaires extraits par LLM
            try:
                horaires_llm_json = json.loads(resultat.llm_horaires_json)
            except json.JSONDecodeError as e:
                return {
                    "identique": None,
                    "differences": f"Erreur parsing JSON LLM: {str(e)}",
                }

            # Effectuer la comparaison directe entre les deux JSON
            try:
                comparison_result = comparator.compare_schedules(
                    horaires_gl_json, horaires_llm_json
                )

                # Préparer les résultats structurés
                if comparison_result.identical:
                    return {
                        "identique": True,  # True = identiques
                        "differences": "",  # Pas de différences
                    }
                else:
                    differences_text = comparison_result.differences

                    return {
                        "identique": False,  # False = différents
                        "differences": differences_text,
                    }

            except Exception as e:
                return {
                    "identique": None,
                    "differences": f"Erreur lors de la comparaison: {str(e)}",
                }

        except Exception as e:
            return {
                "identique": None,
                "differences": f"Erreur générale: {str(e)}",
            }

    def _update_comparison_result(
        self, db_manager: DatabaseProcessor, resultat_id: int, result_data: Dict
    ):
        """Met à jour le résultat d'une comparaison."""
        session = db_manager.Session()
        try:
            resultat = session.get(ResultatsExtraction, resultat_id)
            if resultat:
                resultat.horaires_identiques = result_data.get("identique")
                resultat.differences_horaires = result_data.get("differences", "")

                # Ajouter erreur de comparaison si échec
                if result_data.get("identique") is None:
                    db_manager._add_error_to_result(
                        resultat,
                        "COMPARAISON",
                        result_data.get("differences", "Erreur inconnue"),
                    )

                session.commit()
        finally:
            session.close()

    def process_comparisons(self, db_manager: DatabaseProcessor):
        """Traite les comparaisons avec data.grandlyon.com."""
        self.logger.section("COMPARAISON HORAIRES")

        try:
            comparator = HorairesComparator()

            # Récupérer les enregistrements nécessitant une comparaison
            resultats_pour_comparaison = self._get_pending_comparisons(db_manager)

            if not resultats_pour_comparaison:
                self.logger.info("Aucune comparaison nécessaire")
                return

            self.logger.info(
                f"{len(resultats_pour_comparaison)} comparaisons à effectuer"
            )

            # Afficher la répartition par execution_id pour debug
            executions_stats = {}
            for resultat, lieu in resultats_pour_comparaison:
                exec_id = resultat.id_execution
                executions_stats[exec_id] = executions_stats.get(exec_id, 0) + 1

            for exec_id, count in executions_stats.items():
                self.logger.info(f"  - Exécution {exec_id}: {count} comparaisons")

            successful_count = 0
            for i, (resultat, lieu) in enumerate(resultats_pour_comparaison, 1):
                self.logger.info(
                    f"[{lieu.identifiant}] Comparaison {i}/{len(resultats_pour_comparaison)} pour '{lieu.nom}' (exec: {resultat.id_execution})"
                )

                try:
                    comparison_result = self._compare_single(comparator, resultat, lieu)

                    # Ne mettre à jour que si la comparaison a réussi
                    if comparison_result.get("identique") is not None:
                        self._update_comparison_result(
                            db_manager,
                            resultat.id_resultats_extraction,
                            comparison_result,
                        )
                        successful_count += 1
                    else:
                        self.logger.warning(
                            f"[{lieu.identifiant}] Comparaison échouée pour '{lieu.nom}': {comparison_result.get('differences', 'Erreur inconnue')} - Base non modifiée"
                        )

                except Exception as e:
                    self.logger.error(
                        f"[{lieu.identifiant}] Erreur comparaison pour '{lieu.nom}': {e}"
                    )
                    # Ne pas mettre à jour la base en cas d'erreur

            self.logger.info(
                f"Comparaisons: {successful_count}/{len(resultats_pour_comparaison)} réussies"
            )

        except ImportError as e:
            self.logger.error(f"Comparateur non disponible: {e}")
        except Exception as e:
            self.logger.error(f"Erreur comparaisons: {e}")
