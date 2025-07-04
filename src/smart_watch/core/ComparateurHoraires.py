"""
Comparateur d'horaires d'ouverture au format JSON personnalisé.

Ce module compare deux structures d'horaires et identifie les différences
avec un rapport détaillé des changements.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Union

from .Logger import create_logger

# Initialize logger for this module
logger = create_logger(
    module_name="ComparateurHoraires",
)


@dataclass
class ComparisonResult:
    """Résultat de la comparaison d'horaires."""

    identical: bool
    differences: str
    details: Dict[str, any]

    def __str__(self) -> str:
        status = "IDENTIQUE" if self.identical else "DIFFÉRENT"
        return f"Statut: {status}\n{self.differences}"


class ScheduleNormalizer:
    """Normalise les structures d'horaires pour faciliter la comparaison."""

    @staticmethod
    def normalize_time_slot(slot: Dict) -> Dict:
        """Normalise un créneau horaire."""
        normalized = {"debut": slot.get("debut", ""), "fin": slot.get("fin", "")}

        # Gère l'occurrence (1er et 3eme mardis du mois, etc.)
        occurrence = slot.get("occurence")
        if occurrence is not None:
            if isinstance(occurrence, list):
                normalized["occurence"] = sorted(occurrence)
            else:
                normalized["occurence"] = occurrence

        return normalized

    @staticmethod
    def normalize_day_schedule(day_data: Dict) -> Dict:
        """Normalise les horaires d'un jour."""
        if not isinstance(day_data, dict):
            return {"ouvert": False, "creneaux": []}

        normalized = {
            "ouvert": day_data.get("ouvert", False),
            "creneaux": [],
        }

        # Normalise et trie les créneaux
        creneaux = day_data.get("creneaux", [])
        if isinstance(creneaux, list):
            normalized_slots = [
                ScheduleNormalizer.normalize_time_slot(slot)
                for slot in creneaux
                if isinstance(slot, dict)
            ]
            # Trie par heure de début puis occurrence
            normalized["creneaux"] = sorted(
                normalized_slots, key=lambda x: (x["debut"], x.get("occurence", 0))
            )

        return normalized

    @staticmethod
    def normalize_special_schedules(schedules: Dict) -> Dict:
        """Normalise les horaires spéciaux."""
        if not isinstance(schedules, dict):
            return {}

        normalized = {}
        for date, schedule in schedules.items():
            if isinstance(schedule, str):
                normalized[date] = schedule
            elif isinstance(schedule, dict):
                normalized[date] = ScheduleNormalizer.normalize_day_schedule(schedule)

        return normalized


class HorairesComparator:
    """Comparateur principal d'horaires d'ouverture."""

    def __init__(self):
        self.normalizer = ScheduleNormalizer()
        logger.debug("Comparateur d'horaires initialisé")

    def compare_schedules(self, schedule1: Dict, schedule2: Dict) -> ComparisonResult:
        """Compare deux structures d'horaires complètes."""
        try:
            logger.debug("Début comparaison horaires")

            differences = []
            details = {
                "periods_compared": [],
                "schedule_differences": {},
            }

            # Extrait les données d'horaires
            horaires1 = schedule1.get("horaires_ouverture", {})
            horaires2 = schedule2.get("horaires_ouverture", {})

            # Vérifie les fermetures définitives
            closed1 = self._is_permanently_closed(horaires1)
            closed2 = self._is_permanently_closed(horaires2)

            if closed1 and closed2:
                return ComparisonResult(
                    identical=True,
                    differences="Aucune différence détectée.",
                    details={"both_permanently_closed": True},
                )
            elif closed1 and not closed2:
                return ComparisonResult(
                    identical=False,
                    differences="Établissement 1 définitivement fermé, établissement 2 ouvert",
                    details={"schedule1_permanently_closed": True},
                )
            elif not closed1 and closed2:
                return ComparisonResult(
                    identical=False,
                    differences="Établissement 1 ouvert, établissement 2 définitivement fermé",
                    details={"schedule2_permanently_closed": True},
                )

            # Compare les périodes normalement
            periods1 = horaires1.get("periodes", {})
            periods2 = horaires2.get("periodes", {})

            all_periods = set(periods1.keys()) | set(periods2.keys())
            details["periods_compared"] = list(all_periods)

            for period in sorted(all_periods):
                period_diff = self._compare_period(
                    periods1.get(period, {}), periods2.get(period, {}), period
                )
                if period_diff:
                    differences.append(f"{period.upper()}: {period_diff}")
                    details["schedule_differences"][period] = period_diff

            # Détermine si identique
            identical = len(differences) == 0

            if identical:
                logger.debug("Horaires identiques")
                diff_text = "Aucune différence détectée."
            else:
                logger.debug(f"Différences trouvées: {len(differences)}")
                diff_text = "\n".join(differences)

            return ComparisonResult(
                identical=identical, differences=diff_text, details=details
            )

        except Exception as e:
            logger.error(f"Erreur comparaison: {e}")
            return ComparisonResult(
                identical=False,
                differences=f"Erreur lors de la comparaison: {str(e)}",
                details={"error": str(e)},
            )

    def _is_permanently_closed(self, horaires: Dict) -> bool:
        """Vérifie si un établissement est définitivement fermé."""
        periods = horaires.get("periodes", {})

        # Vérifie si toutes les périodes avec source indiquent une fermeture
        has_source = False
        all_closed = True

        for period_key, period_data in periods.items():
            if not isinstance(period_data, dict) or not period_data.get(
                "source_found", False
            ):
                continue

            has_source = True

            if period_key in [
                "hors_vacances_scolaires",
                "vacances_scolaires_ete",
                "petites_vacances_scolaires",
            ]:
                schedule = period_data.get("horaires", {})
                for day_data in schedule.values():
                    if isinstance(day_data, dict) and (
                        day_data.get("ouvert", False) or day_data.get("creneaux", [])
                    ):
                        all_closed = False
                        break
            elif period_key in ["jours_feries", "jours_speciaux"]:
                specific_schedules = period_data.get("horaires_specifiques", {})
                if specific_schedules:
                    all_closed = False

            if not all_closed:
                break

        return has_source and all_closed

    def _compare_period(self, period1: Dict, period2: Dict, period_name: str) -> str:
        """Compare une période spécifique."""
        if not period1 and not period2:
            return ""

        # Compare selon le type de période
        if period_name in ["jours_feries", "jours_speciaux"]:
            return self._compare_special_period(period1, period2)
        else:
            return self._compare_weekly_period(period1, period2)

    def _compare_weekly_period(self, period1: Dict, period2: Dict) -> str:
        """Compare une période d'horaires hebdomadaires."""
        horaires1 = period1.get("horaires", {})
        horaires2 = period2.get("horaires", {})

        differences = []
        all_days = set(horaires1.keys()) | set(horaires2.keys())

        for day in [
            "lundi",
            "mardi",
            "mercredi",
            "jeudi",
            "vendredi",
            "samedi",
            "dimanche",
        ]:
            if day in all_days:
                day_diff = self._compare_day_schedule(
                    horaires1.get(day, {}), horaires2.get(day, {}), day
                )
                if day_diff:
                    differences.append(f"{day}: {day_diff}")

        return " | ".join(differences)

    def _compare_day_schedule(self, day1: Dict, day2: Dict, day_name: str) -> str:
        """Compare les horaires d'un jour."""
        norm1 = self.normalizer.normalize_day_schedule(day1)
        norm2 = self.normalizer.normalize_day_schedule(day2)

        differences = []

        # Compare ouvert/fermé
        if norm1["ouvert"] != norm2["ouvert"]:
            status1 = "ouvert" if norm1["ouvert"] else "fermé"
            status2 = "ouvert" if norm2["ouvert"] else "fermé"
            differences.append(f"{status1} → {status2}")

        # Compare les créneaux
        slots_diff = self._compare_time_slots(norm1["creneaux"], norm2["creneaux"])
        if slots_diff:
            differences.append(f"créneaux: {slots_diff}")

        return " | ".join(differences)

    def _compare_time_slots(self, slots1: List[Dict], slots2: List[Dict]) -> str:
        """Compare les créneaux horaires."""
        # Convertit en ensembles pour comparaison
        set1 = {self._slot_to_string(slot) for slot in slots1}
        set2 = {self._slot_to_string(slot) for slot in slots2}

        added = set2 - set1
        removed = set1 - set2

        differences = []
        if added:
            differences.append(f"ajoutés: {', '.join(sorted(added))}")
        if removed:
            differences.append(f"supprimés: {', '.join(sorted(removed))}")

        return " | ".join(differences)

    def _slot_to_string(self, slot: Dict) -> str:
        """Convertit un créneau en chaîne pour comparaison."""
        base = f"{slot['debut']}-{slot['fin']}"
        if "occurence" in slot:
            occur = slot["occurence"]
            if isinstance(occur, list):
                base += f"[{','.join(map(str, occur))}]"
            else:
                base += f"[{occur}]"
        return base

    def _compare_special_period(self, period1: Dict, period2: Dict) -> str:
        """Compare une période de jours spéciaux."""
        schedules1 = self.normalizer.normalize_special_schedules(
            period1.get("horaires_specifiques", {})
        )
        schedules2 = self.normalizer.normalize_special_schedules(
            period2.get("horaires_specifiques", {})
        )

        differences = []
        all_dates = set(schedules1.keys()) | set(schedules2.keys())

        for date in sorted(all_dates):
            sched1 = schedules1.get(date)
            sched2 = schedules2.get(date)

            if sched1 != sched2:
                if sched1 is None:
                    differences.append(f"{date}: ajouté")
                elif sched2 is None:
                    differences.append(f"{date}: supprimé")
                else:
                    # Compare les détails
                    if isinstance(sched1, str) and isinstance(sched2, str):
                        differences.append(f"{date}: {sched1} → {sched2}")
                    else:
                        day_diff = self._compare_day_schedule(sched1, sched2, date)
                        if day_diff:
                            differences.append(f"{date}: {day_diff}")

        return " | ".join(differences)

    def compare_files(
        self, file1: Union[str, Path], file2: Union[str, Path]
    ) -> ComparisonResult:
        """Compare deux fichiers JSON d'horaires."""
        try:
            logger.info(
                f"Comparaison fichiers: {Path(file1).name} vs {Path(file2).name}"
            )

            # Lit les fichiers
            with open(file1, "r", encoding="utf-8") as f:
                data1 = json.load(f)
            with open(file2, "r", encoding="utf-8") as f:
                data2 = json.load(f)

            return self.compare_schedules(data1, data2)

        except FileNotFoundError as e:
            logger.error(f"Fichier non trouvé: {e}")
            return ComparisonResult(
                identical=False,
                differences=f"Fichier non trouvé: {str(e)}",
                details={"error": str(e)},
            )
        except json.JSONDecodeError as e:
            logger.error(f"Erreur JSON: {e}")
            return ComparisonResult(
                identical=False,
                differences=f"Erreur de format JSON: {str(e)}",
                details={"error": str(e)},
            )
        except Exception as e:
            logger.error(f"Erreur comparaison fichiers: {e}")
            return ComparisonResult(
                identical=False,
                differences=f"Erreur: {str(e)}",
                details={"error": str(e)},
            )


def main():
    """Exemple d'utilisation et tests."""
    json1 = '{"horaires_ouverture": {"metadata": {"identifiant": "S1433", "nom": "Mairie de Lyon 1", "type_lieu": "mairie", "url": "https://mairie1.lyon.fr/lieu/mairies/mairie-du-1er-arrondissement"}, "periodes": {"hors_vacances_scolaires": {"source_found": true, "label": "Période hors vacances scolaires", "condition": "default", "horaires": {"lundi": {"source_found": true, "ouvert": true, "creneaux": [{"debut": "08:45", "fin": "16:45"}]}, "mardi": {"source_found": true, "ouvert": true, "creneaux": [{"debut": "08:45", "fin": "16:45"}]}, "mercredi": {"source_found": true, "ouvert": true, "creneaux": [{"debut": "08:45", "fin": "16:45"}]}, "jeudi": {"source_found": false, "ouvert": false, "creneaux": []}, "vendredi": {"source_found": true, "ouvert": true, "creneaux": [{"debut": "08:45", "fin": "16:45"}]}, "samedi": {"source_found": false, "ouvert": false, "creneaux": []}, "dimanche": {"source_found": false, "ouvert": false, "creneaux": []}}}, "vacances_scolaires_ete": {"source_found": false, "label": "Grandes vacances scolaires", "condition": "SH", "horaires": {"lundi": {"source_found": false, "ouvert": false, "creneaux": []}, "mardi": {"source_found": false, "ouvert": false, "creneaux": []}, "mercredi": {"source_found": false, "ouvert": false, "creneaux": []}, "jeudi": {"source_found": false, "ouvert": false, "creneaux": []}, "vendredi": {"source_found": false, "ouvert": false, "creneaux": []}, "samedi": {"source_found": false, "ouvert": false, "creneaux": []}, "dimanche": {"source_found": false, "ouvert": false, "creneaux": []}}}, "petites_vacances_scolaires": {"source_found": false, "label": "Petites vacances scolaires", "condition": "SH", "horaires": {"lundi": {"source_found": false, "ouvert": false, "creneaux": []}, "mardi": {"source_found": false, "ouvert": false, "creneaux": []}, "mercredi": {"source_found": false, "ouvert": false, "creneaux": []}, "jeudi": {"source_found": false, "ouvert": false, "creneaux": []}, "vendredi": {"source_found": false, "ouvert": false, "creneaux": []}, "samedi": {"source_found": false, "ouvert": false, "creneaux": []}, "dimanche": {"source_found": false, "ouvert": false, "creneaux": []}}}, "jours_feries": {"source_found": true, "label": "Jours fériés", "condition": "PH", "mode": "ferme", "horaires_specifiques": {"2025-07-05": "ferme", "2025-10-18": "ferme", "2025-12-20": "ferme", "2025-12-26": "ferme", "2026-02-07": "ferme", "2026-04-04": "ferme", "2026-05-14": "ferme", "2025-07-12": "ferme", "2025-07-14": "ferme", "2025-08-02": "ferme", "2025-08-09": "ferme", "2025-08-15": "ferme", "2025-08-16": "ferme", "2025-08-23": "ferme", "2025-11-01": "ferme", "2025-11-11": "ferme", "2025-12-25": "ferme", "2026-01-01": "ferme", "2026-04-06": "ferme", "2026-05-01": "ferme", "2026-05-08": "ferme", "2026-05-25": "ferme", "2026-07-14": "ferme", "2026-08-15": "ferme", "2026-11-01": "ferme", "2026-11-11": "ferme", "2026-12-25": "ferme"}}, "jours_speciaux": {"source_found": false, "label": "Jours spéciaux", "mode": "ferme", "horaires_specifiques": {}}}, "extraction_info": {"source_found": true, "notes": "Converti depuis format OSM"}}}'
    json2 = '{"horaires_ouverture":{"metadata":{"identifiant":"mairie1","nom":"MairiedeLyon1","type_lieu":"Mairie","timezone":"Europe/Paris"},"periodes":{"hors_vacances_scolaires":{"source_found":true,"horaires":{"lundi":{"source_found":true,"ouvert":true,"creneaux":[{"debut":"08:45","fin":"16:45"}]},"mardi":{"source_found":true,"ouvert":true,"creneaux":[{"debut":"08:45","fin":"16:45"}]},"mercredi":{"source_found":true,"ouvert":true,"creneaux":[{"debut":"08:45","fin":"16:45"}]},"jeudi":{"source_found":true,"ouvert":true,"creneaux":[{"debut":"10:00","fin":"16:45"}]},"vendredi":{"source_found":true,"ouvert":true,"creneaux":[{"debut":"08:45","fin":"16:45"}]},"samedi":{"source_found":true,"ouvert":true,"creneaux":[{"debut":"09:30","fin":"12:00"}]},"dimanche":{"source_found":false,"ouvert":false,"creneaux":[]}}},"vacances_scolaires_ete":{"source_found":true,"horaires":{"lundi":{"source_found":true,"ouvert":true,"creneaux":[{"debut":"08:45","fin":"12:30"},{"debut":"13:30","fin":"16:45"}]},"mardi":{"source_found":true,"ouvert":true,"creneaux":[{"debut":"08:45","fin":"12:30"},{"debut":"13:30","fin":"16:45"}]},"mercredi":{"source_found":true,"ouvert":true,"creneaux":[{"debut":"08:45","fin":"12:30"},{"debut":"13:30","fin":"16:45"}]},"jeudi":{"source_found":true,"ouvert":true,"creneaux":[{"debut":"10:00","fin":"12:30"},{"debut":"13:30","fin":"16:45"}]},"vendredi":{"source_found":true,"ouvert":true,"creneaux":[{"debut":"08:45","fin":"12:30"},{"debut":"13:30","fin":"16:45"}]},"samedi":{"source_found":true,"ouvert":true,"creneaux":[{"debut":"09:30","fin":"12:00"}]},"dimanche":{"source_found":false,"ouvert":false,"creneaux":[]}}},"jours_speciaux":{"source_found":true,"horaires_specifiques":{"2025-01-01":{"source_found":true,"ouvert":false,"creneaux":[]},"2025-04-01":{"source_found":true,"ouvert":true,"creneaux":[{"debut":"13:30","fin":"16:45"}]}}}},"extraction_info":{"source_found":true,"permanently_closed":false}}}'
    comparator = HorairesComparator()

    print(comparator.compare_schedules(json.loads(json1), json.loads(json2)))

    # Test avec des fichiers JSON d'exemple
    print("Comparateur d'horaires initialisé")
    print("Utilisation: comparator.compare_schedules(json1, json2)")
    print("ou comparator.compare_files(file1, file2)")


if __name__ == "__main__":
    main()
