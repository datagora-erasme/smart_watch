"""
Processeur pour les comparaisons d'horaires.
"""

import json
from typing import Dict

from ..core.ComparateurHoraires import HorairesComparator
from ..core.ConfigManager import ConfigManager
from .database_processor import DatabaseProcessor


class ComparisonProcessor:
    """Processeur pour les comparaisons d'horaires."""

    def __init__(self, config: ConfigManager, logger):
        self.config = config
        self.logger = logger

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

            # Vérifier l'état global de fermeture selon les deux sources
            try:
                is_gl_closed = comparator._is_permanently_closed(horaires_gl_json)
                is_llm_closed = comparator._is_permanently_closed(horaires_llm_json)
            except Exception as e:
                return {
                    "identique": None,
                    "differences": f"Erreur vérification fermeture: {str(e)}",
                }

            # Cas où les deux sources indiquent une fermeture
            if is_gl_closed and is_llm_closed:
                return {
                    "identique": True,
                    "differences": "Fermeture confirmée par les deux sources",
                }

            # Cas où un seul indique une fermeture
            if is_gl_closed != is_llm_closed:
                return {
                    "identique": False,
                    "differences": f"Écart fermeture: {'data.grandlyon.com' if is_gl_closed else 'LLM'} indique fermé",
                }

            # Effectuer la comparaison détaillée si nécessaire
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

    def process_comparisons(self, db_processor: DatabaseProcessor):
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
            executions_stats = {}
            for resultat, lieu in resultats_pour_comparaison:
                exec_id = getattr(resultat, "id_execution", "unknown")
                executions_stats[exec_id] = executions_stats.get(exec_id, 0) + 1

            for exec_id, count in executions_stats.items():
                self.logger.info(f"  - Exécution {exec_id}: {count} comparaisons")

            successful_count = 0
            for i, (resultat, lieu) in enumerate(resultats_pour_comparaison, 1):
                lieu_id = getattr(lieu, "identifiant", "unknown")
                lieu_nom = getattr(lieu, "nom", "unknown")
                exec_id = getattr(resultat, "id_execution", "unknown")

                self.logger.info(
                    f"*{lieu_id}* Comparaison {i}/{len(resultats_pour_comparaison)} pour '{lieu_nom}' (exec: {exec_id})"
                )

                try:
                    comparison_result = self._compare_single(comparator, resultat, lieu)

                    # On vérifie simplement que le résultat est un dictionnaire valide
                    if isinstance(comparison_result, dict):
                        # Essayer différents noms d'attributs pour l'ID
                        resultat_id = (
                            getattr(resultat, "id_resultats_extraction", None)
                            or getattr(resultat, "id", None)
                            or getattr(resultat, "resultat_id", None)
                        )

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
