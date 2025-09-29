# Comparateur d'horaires d'ouverture au format JSON personnalisé
# Documentation : https://datagora-erasme.github.io/smart_watch/source/modules/core/ComparateurHoraires.html

from dataclasses import dataclass
from typing import Any, Dict, List

from .Logger import create_logger

# Instancier un logger pour ce module
logger = create_logger(
    module_name="ComparateurHoraires",
)


@dataclass
class ComparisonResult:
    """
    Représente le résultat d'une comparaison d'horaires.

    Attributes:
        identical (bool): indique si les horaires comparés sont identiques.
        differences (str): description textuelle des différences trouvées.
        details (Dict[str, Any]): détails supplémentaires sur les différences.
    """

    identical: bool
    differences: str
    details: Dict[str, Any]

    def __str__(self) -> str:
        """
        Retourne une représentation sous forme de chaîne de caractères du résultat de la comparaison.

        Returns:
            str: Une chaîne indiquant le statut de la comparaison ("IDENTIQUE" ou "DIFFÉRENT")
                 suivi des différences.
        """
        status = "IDENTIQUE" if self.identical else "DIFFÉRENT"
        return f"Statut: {status}\n{self.differences}"


class ScheduleNormalizer:
    """
    Classe utilitaire pour la normalisation des horaires et des créneaux horaires.

    Cette classe propose des méthodes statiques permettant de :
        - normaliser un créneau horaire (début, fin, occurrence).
        - normaliser les horaires d'un jour (ouverture, liste des créneaux).
        - normaliser les horaires spéciaux (jours fériés, exceptions).

    Méthodes:
        normalize_time_slot(slot: Dict) -> Dict:
            normalise un créneau horaire en structurant les champs 'debut', 'fin' et 'occurence'.
        normalize_day_schedule(day_data: Dict) -> Dict:
            normalise les horaires d'un jour, en structurant l'ouverture et en triant les créneaux.
        normalize_special_schedules(schedules: Dict) -> Dict:
            normalise les horaires spéciaux, en gérant les exceptions et les jours particuliers.
    """

    @staticmethod
    def normalize_time_slot(slot: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalise un créneau horaire.

        Assure la présence des clés 'debut', 'fin' et 'occurence'.
        Les valeurs par défaut pour 'debut' et 'fin' sont des chaînes vides.
        La clé 'occurence' est triée si elle est une liste.

        Args:
            slot (Dict[str, Any]): dictionnaire du créneau horaire.

        Returns:
            Dict[str, Any] : dictionnaire du créneau horaire normalisé.
        """
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
    def normalize_day_schedule(day_data: Any) -> Dict[str, Any]:
        """
        Normalise les données d'un jour d'ouverture et trie les créneaux.

        Args:
            day_data (Dict[str, Any]): dictionnaire des informations du jour.

        Returns:
            Dict[str, Any] : dictionnaire normalisé avec les clés "ouvert" et "creneaux".
        """
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
    def normalize_special_schedules(schedules: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalise un dictionnaire d'horaires spéciaux.

        Args:
            schedules (Dict[str, Any]): dictionnaire des horaires spéciaux.

        Returns:
            Dict[str, Any]: dictionnaire des horaires spéciaux normalisés.
        """
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

    def __init__(self) -> None:
        """Initialise le comparateur d'horaires."""
        self.normalizer = ScheduleNormalizer()
        logger.debug("Comparateur d'horaires initialisé")

    def compare_schedules(
        self, schedule1: Dict[str, Any], schedule2: Dict[str, Any]
    ) -> ComparisonResult:
        """
        Compare deux horaires d'ouverture et retourne le résultat de la comparaison.

        Cette méthode analyse les horaires d'ouverture de deux établissements, en tenant compte des fermetures définitives et des différences pour chaque période d'ouverture. Elle retourne un objet `ComparisonResult` contenant le statut d'identité, les différences détectées et des détails sur la comparaison.

        Args:
            schedule1 (Dict[str, Any]): horaires d'ouverture du premier établissement.
            schedule2 (Dict[str, Any]): horaires d'ouverture du second établissement.

        Returns:
            ComparisonResult: résultat de la comparaison.

        Raises:
            Exception: En cas d'erreur lors de la comparaison.
        """
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

            # Gère les cas de fermeture sans interrompre la comparaison détaillée
            if closed1 and not closed2:
                differences.append(
                    "ATTENTION: L'établissement 1 (attendu) semble définitivement fermé, alors que l'établissement 2 (prédit) est ouvert."
                )
                details["schedule1_permanently_closed"] = True
            elif not closed1 and closed2:
                differences.append(
                    "ATTENTION: L'établissement 1 (attendu) est ouvert, alors que l'établissement 2 (prédit) semble définitivement fermé."
                )
                details["schedule2_permanently_closed"] = True

            # Compare les périodes
            periods1 = horaires1.get("periodes", {})
            periods2 = horaires2.get("periodes", {})

            # Fusionne et compare les jours spéciaux et fériés
            special_schedules1 = {}
            special_schedules1.update(
                periods1.get("jours_feries", {}).get("horaires_specifiques", {})
            )
            special_schedules1.update(
                periods1.get("jours_speciaux", {}).get("horaires_specifiques", {})
            )

            special_schedules2 = {}
            special_schedules2.update(
                periods2.get("jours_feries", {}).get("horaires_specifiques", {})
            )
            special_schedules2.update(
                periods2.get("jours_speciaux", {}).get("horaires_specifiques", {})
            )

            if special_schedules1 or special_schedules2:
                norm_spec1 = self.normalizer.normalize_special_schedules(
                    special_schedules1
                )
                norm_spec2 = self.normalizer.normalize_special_schedules(
                    special_schedules2
                )
                special_diff = self._compare_special_schedules(norm_spec1, norm_spec2)
                if special_diff:
                    diff_key = "JOURS SPÉCIAUX ET FÉRIÉS"
                    differences.append(f"{diff_key}: {special_diff}")
                    details["schedule_differences"][diff_key] = special_diff

            # Compare les autres périodes (hebdomadaires)
            all_periods = set(periods1.keys()) | set(periods2.keys())
            weekly_periods = all_periods - {"jours_feries", "jours_speciaux"}
            details["periods_compared"] = sorted(list(weekly_periods))
            if special_schedules1 or special_schedules2:
                details["periods_compared"].append("jours_speciaux_et_feries")

            for period in sorted(weekly_periods):
                period_diff = self._compare_weekly_period(
                    periods1.get(period, {}), periods2.get(period, {})
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

    def _is_permanently_closed(self, horaires: Dict[str, Any]) -> bool:
        """
        Détermine si un ensemble d'horaires indique une fermeture permanente.

        Args:
            horaires (Dict[str, Any]): dictionnaire contenant les périodes et horaires.

        Returns:
            bool: True si l'établissement est considéré comme fermé, False sinon.
        """
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

    def _compare_period(
        self, period1: Dict[str, Any], period2: Dict[str, Any], period_name: str
    ) -> str:
        """
        Compare deux périodes horaires.

        Args:
            period1 (Dict[str, Any]): première période à comparer.
            period2 (Dict[str, Any]): deuxième période à comparer.
            period_name (str): nom de la période ('jours_feries', etc.).

        Returns:
            str: description textuelle des différences.
        """
        if not period1 and not period2:
            return ""

        # Compare selon le type de période
        if period_name in ["jours_feries", "jours_speciaux"]:
            return self._compare_special_period(period1, period2)
        else:
            return self._compare_weekly_period(period1, period2)

    def _compare_weekly_period(
        self, period1: Dict[str, Any], period2: Dict[str, Any]
    ) -> str:
        """
        Compare deux périodes hebdomadaires.

        Args:
            period1 (Dict[str, Any]): première période hebdomadaire.
            period2 (Dict[str, Any]): deuxième période hebdomadaire.

        Returns:
            str: description textuelle des différences.
        """
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

    def _compare_day_schedule(self, day1: Any, day2: Any, day_name: str) -> str:
        """
        Compare les horaires d'un jour donné.

        Args:
            day1 (Dict[str, Any]): horaires du premier jour.
            day2 (Dict[str, Any]): horaires du second jour.
            day_name (str): nom du jour.

        Returns:
            str: description textuelle des différences.
        """
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

    def _compare_time_slots(
        self, slots1: List[Dict[str, Any]], slots2: List[Dict[str, Any]]
    ) -> str:
        """
        Compare deux listes de créneaux horaires.

        Args:
            slots1 (List[Dict[str, Any]]): première liste de créneaux.
            slots2 (List[Dict[str, Any]]): seconde liste de créneaux.

        Returns:
            str: description textuelle des créneaux ajoutés et supprimés.
        """
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

    def _slot_to_string(self, slot: Dict[str, Any]) -> str:
        """
        Convertit un créneau horaire en chaîne de caractères.

        Args:
            slot (Dict[str, Any]): dictionnaire du créneau horaire.

        Returns:
            str: Représentation textuelle du créneau.
        """
        base = f"{slot['debut']}-{slot['fin']}"
        if "occurence" in slot:
            occur = slot["occurence"]
            if isinstance(occur, list):
                base += f"[{','.join(map(str, occur))}]"
            else:
                base += f"[{occur}]"
        return base

    def _compare_special_schedules(
        self, schedules1: Dict[str, Any], schedules2: Dict[str, Any]
    ) -> str:
        """
        Compare deux dictionnaires d'horaires spécifiques.

        Args:
            schedules1 (Dict[str, Any]): premier dictionnaire d'horaires.
            schedules2 (Dict[str, Any]): second dictionnaire d'horaires.

        Returns:
            str: description textuelle des différences.
        """
        differences = []
        all_dates = set(schedules1.keys()) | set(schedules2.keys())

        for date in sorted(all_dates):
            sched1 = schedules1.get(date)
            sched2 = schedules2.get(date)

            if sched1 != sched2:
                if sched1 is None:
                    day_diff = self._compare_day_schedule({}, sched2, date)
                    differences.append(f"{date}: ajouté ({day_diff})")
                elif sched2 is None:
                    day_diff = self._compare_day_schedule(sched1, {}, date)
                    differences.append(f"{date}: supprimé ({day_diff})")
                else:
                    # Compare les détails
                    if isinstance(sched1, str) and isinstance(sched2, str):
                        differences.append(f"{date}: {sched1} → {sched2}")
                    else:
                        day_diff = self._compare_day_schedule(sched1, sched2, date)
                        if day_diff:
                            differences.append(f"{date}: {day_diff}")

        return " | ".join(differences)

    def _compare_special_period(
        self, period1: Dict[str, Any], period2: Dict[str, Any]
    ) -> str:
        """
        Compare les horaires spécifiques de deux périodes.

        Args:
            period1 (Dict[str, Any]): première période.
            period2 (Dict[str, Any]): seconde période.

        Returns:
            str: description textuelle des différences.
        """
        schedules1 = self.normalizer.normalize_special_schedules(
            period1.get("horaires_specifiques", {})
        )
        schedules2 = self.normalizer.normalize_special_schedules(
            period2.get("horaires_specifiques", {})
        )

        return self._compare_special_schedules(schedules1, schedules2)
