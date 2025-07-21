# Comparateur d'horaires d'ouverture au format JSON personnalisé
# https://datagora-erasme.github.io/smart_watch/source/modules/core/comparateur_horaires.html

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Union

from .Logger import create_logger

# Instancier un logger pour ce module
logger = create_logger(
    module_name="ComparateurHoraires",
)


@dataclass
class ComparisonResult:
    """
    Classe représentant le résultat d'une comparaison d'horaires.

    Attributes:
        identical (bool): Indique si les horaires comparés sont identiques.
        differences (str): Description textuelle des différences trouvées lors de la comparaison.
        details (Dict[str, any]): Détails supplémentaires sur les différences, organisés par clé.

    Methods:
        __str__(): Retourne une représentation textuelle du résultat de la comparaison, incluant le statut et les différences.
    """

    identical: bool
    differences: str
    details: Dict[str, any]

    def __str__(self) -> str:
        status = "IDENTIQUE" if self.identical else "DIFFÉRENT"
        return f"Statut: {status}\n{self.differences}"


class ScheduleNormalizer:
    """
    Classe utilitaire pour la normalisation des horaires et des créneaux horaires.

    Cette classe propose des méthodes statiques permettant de :
        - Normaliser un créneau horaire (début, fin, occurrence).
        - Normaliser les horaires d'un jour (ouverture, liste des créneaux).
        - Normaliser les horaires spéciaux (jours fériés, exceptions).

    Méthodes:
        normalize_time_slot(slot: Dict) -> Dict:
            Normalise un créneau horaire en structurant les champs 'debut', 'fin' et 'occurence'.
        normalize_day_schedule(day_data: Dict) -> Dict:
            Normalise les horaires d'un jour, en structurant l'ouverture et en triant les créneaux.
        normalize_special_schedules(schedules: Dict) -> Dict:
            Normalise les horaires spéciaux, en gérant les exceptions et les jours particuliers.

    Exemple d'utilisation:
        >>> slot = {"debut": "08:00", "fin": "12:00", "occurence": [1, 3]}
        >>> ScheduleNormalizer.normalize_time_slot(slot)
        {'debut': '08:00', 'fin': '12:00', 'occurence': [1, 3]}
    """

    @staticmethod
    def normalize_time_slot(slot: Dict) -> Dict:
        """
        Normalise un créneau horaire en assurant la présence des clés 'debut', 'fin' et 'occurence'.

        Cette fonction prend un dictionnaire représentant un créneau horaire et retourne un nouveau dictionnaire
        contenant les clés normalisées. Les valeurs par défaut pour 'debut' et 'fin' sont des chaînes vides si elles
        ne sont pas présentes. La clé 'occurence' est triée si elle est une liste.

        Args:
            slot (Dict): Dictionnaire représentant un créneau horaire, pouvant contenir les clés 'debut', 'fin' et 'occurence'.

        Returns:
            Dict: Dictionnaire normalisé avec les clés 'debut', 'fin' et éventuellement 'occurence'.
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
    def normalize_day_schedule(day_data: Dict) -> Dict:
        """
        Normalise les données d'un jour d'ouverture et trie les créneaux horaires.

        Cette fonction prend un dictionnaire représentant les horaires d'un jour,
        vérifie sa validité, normalise les créneaux horaires à l'aide de
        ScheduleNormalizer.normalize_time_slot, puis les trie par heure de début
        et par occurrence.

        Args:
            day_data (Dict): Dictionnaire contenant les informations du jour,
                avec les clés "ouvert" (bool) et "creneaux" (list de dict).

        Returns:
            Dict: Dictionnaire normalisé avec les clés "ouvert" (bool) et
                "creneaux" (list de dict triés et normalisés).
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
    def normalize_special_schedules(schedules: Dict) -> Dict:
        """
        Normalise les horaires spéciaux fournis sous forme de dictionnaire.

        Cette fonction prend un dictionnaire représentant des horaires spéciaux, où chaque clé est une date
        et chaque valeur peut être une chaîne de caractères ou un dictionnaire décrivant l'horaire du jour.
        Les horaires sous forme de dictionnaire sont normalisés via la méthode `ScheduleNormalizer.normalize_day_schedule`.
        Les horaires sous forme de chaîne sont conservés tels quels.

        Args:
            schedules (Dict): Dictionnaire des horaires spéciaux à normaliser. Les clés sont des dates (str),
                les valeurs sont soit des chaînes de caractères, soit des dictionnaires représentant un horaire.

        Returns:
            Dict: Dictionnaire des horaires normalisés, avec les mêmes clés (dates) et des valeurs normalisées.
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

    def __init__(self):
        self.normalizer = ScheduleNormalizer()
        logger.debug("Comparateur d'horaires initialisé")

    def compare_schedules(self, schedule1: Dict, schedule2: Dict) -> ComparisonResult:
        """
        Compare deux horaires d'ouverture et retourne le résultat de la comparaison.

        Cette méthode analyse les horaires d'ouverture de deux établissements, en tenant compte des fermetures définitives et des différences pour chaque période d'ouverture. Elle retourne un objet `ComparisonResult` contenant le statut d'identité, les différences détectées et des détails sur la comparaison.

        Args:
            schedule1 (Dict): Dictionnaire représentant les horaires d'ouverture du premier établissement.
            schedule2 (Dict): Dictionnaire représentant les horaires d'ouverture du second établissement.

        Returns:
            ComparisonResult: Objet contenant le résultat de la comparaison, incluant si les horaires sont identiques, la liste des différences, et des détails sur la comparaison.

        Raises:
            Exception: En cas d'erreur lors de la comparaison des horaires.

        Exemple:
            >>> result = compare_schedules(schedule1, schedule2)
            >>> print(result.identical)
            >>> print(result.differences)
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

    def _is_permanently_closed(self, horaires: Dict) -> bool:
        """
        Détermine si un ensemble d'horaires indique une fermeture permanente.

        Cette méthode analyse les différentes périodes d'ouverture (hors vacances scolaires, vacances scolaires d'été, petites vacances scolaires, jours fériés, jours spéciaux)
        pour vérifier si toutes les sources d'horaires disponibles indiquent une fermeture. Elle considère qu'une période est fermée si aucun jour n'est marqué comme ouvert
        et qu'aucun créneau n'est disponible. Pour les jours fériés et spéciaux, la présence d'horaires spécifiques indique une ouverture.

        Args:
            horaires (Dict): Dictionnaire contenant les périodes et horaires à analyser.

        Returns:
            bool: True si toutes les périodes avec une source indiquent une fermeture permanente, False sinon.
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

    def _compare_period(self, period1: Dict, period2: Dict, period_name: str) -> str:
        """
        Compare deux périodes horaires et retourne une chaîne décrivant les différences.

        Selon le type de période (jours fériés, jours spéciaux ou période hebdomadaire),
        la comparaison est effectuée par des méthodes spécifiques.

        Args:
            period1 (Dict): Première période à comparer.
            period2 (Dict): Deuxième période à comparer.
            period_name (str): Nom du type de période ('jours_feries', 'jours_speciaux', etc.).

        Returns:
            str: Description des différences entre les deux périodes. Chaîne vide si aucune période n'est définie.
        """
        if not period1 and not period2:
            return ""

        # Compare selon le type de période
        if period_name in ["jours_feries", "jours_speciaux"]:
            return self._compare_special_period(period1, period2)
        else:
            return self._compare_weekly_period(period1, period2)

    def _compare_weekly_period(self, period1: Dict, period2: Dict) -> str:
        """
        Compare deux périodes hebdomadaires et retourne les différences entre les horaires de chaque jour.

        Args:
            period1 (Dict): Première période contenant les horaires par jour.
            period2 (Dict): Deuxième période contenant les horaires par jour.

        Returns:
            str: Chaîne de caractères listant les différences pour chaque jour, séparées par " | ".
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

    def _compare_day_schedule(self, day1: Dict, day2: Dict, day_name: str) -> str:
        """
        Compare les horaires d'ouverture d'un jour donné entre deux ensembles d'horaires.

        Cette méthode normalise les horaires des deux jours, puis compare leur statut d'ouverture
        (ouvert/fermé) ainsi que les créneaux horaires. Les différences sont formatées sous forme
        de chaîne de caractères lisible.

        Args:
            day1 (Dict): Horaires du premier jour à comparer.
            day2 (Dict): Horaires du second jour à comparer.
            day_name (str): Nom du jour (ex: "lundi").

        Returns:
            str: Description des différences entre les deux horaires pour le jour donné,
                séparées par " | ". Si aucune différence, retourne une chaîne vide.
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

    def _compare_time_slots(self, slots1: List[Dict], slots2: List[Dict]) -> str:
        """
        Compare deux listes de créneaux horaires et retourne les différences sous forme de chaîne.

        Cette méthode convertit chaque créneau horaire en chaîne de caractères, puis en set, pour faciliter la comparaison.
        Elle identifie les créneaux ajoutés et supprimés entre les deux listes en exploitant les caractéristiques des set;
        puis retourne une description textuelle des différences.

        Args:
            slots1 (List[Dict]): Liste de créneaux horaires initiale.
            slots2 (List[Dict]): Nouvelle liste de créneaux horaires à comparer.

        Returns:
            str: Description des créneaux ajoutés et supprimés, séparés par " | ".
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

    def _slot_to_string(self, slot: Dict) -> str:
        """
        Convertit un créneau horaire sous forme de dictionnaire en une chaîne de caractères lisible.

        Cette méthode prend un dictionnaire représentant un créneau horaire, contenant au minimum les clés 'debut' et 'fin'.
        Si la clé 'occurence' est présente, elle est ajoutée à la chaîne entre crochets.
        La valeur de 'occurence' peut être une liste ou un entier.

        Args:
            slot (Dict): Dictionnaire contenant les informations du créneau horaire.
                Doit inclure les clés 'debut' et 'fin', et optionnellement 'occurence'.

        Returns:
            str: Représentation textuelle du créneau horaire, incluant éventuellement l'occurrence.
        """
        base = f"{slot['debut']}-{slot['fin']}"
        if "occurence" in slot:
            occur = slot["occurence"]
            if isinstance(occur, list):
                base += f"[{','.join(map(str, occur))}]"
            else:
                base += f"[{occur}]"
        return base

    def _compare_special_schedules(self, schedules1: Dict, schedules2: Dict) -> str:
        """
        Compare deux dictionnaires d'horaires spécifiques et retourne une description des différences.

        Args:
            schedules1 (Dict): Premier dictionnaire d'horaires spécifiques (normalisé).
            schedules2 (Dict): Second dictionnaire d'horaires spécifiques (normalisé).

        Returns:
            str: Description textuelle des différences, séparées par " | ".
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

    def _compare_special_period(self, period1: Dict, period2: Dict) -> str:
        """
        Compare les horaires spécifiques entre deux périodes et retourne une description des différences.

        Cette méthode normalise les horaires spécifiques des deux périodes, puis compare chaque date
        présente dans l'une ou l'autre des périodes. Elle identifie les ajouts, suppressions ou modifications
        d'horaires pour chaque date et retourne une chaîne résumant ces différences.

        Args:
            period1 (Dict): Dictionnaire représentant la première période, contenant éventuellement la clé "horaires_specifiques".
            period2 (Dict): Dictionnaire représentant la seconde période, contenant éventuellement la clé "horaires_specifiques".

        Returns:
            str: Description textuelle des différences entre les horaires spécifiques des deux périodes, séparées par " | ".
        """
        schedules1 = self.normalizer.normalize_special_schedules(
            period1.get("horaires_specifiques", {})
        )
        schedules2 = self.normalizer.normalize_special_schedules(
            period2.get("horaires_specifiques", {})
        )

        return self._compare_special_schedules(schedules1, schedules2)

    def compare_files(
        self, file1: Union[str, Path], file2: Union[str, Path]
    ) -> ComparisonResult:
        """
        Compare deux fichiers JSON contenant des horaires et retourne le résultat de la comparaison.

        Cette méthode lit les deux fichiers spécifiés, analyse leur contenu JSON, puis compare les horaires
        à l'aide de la méthode `compare_schedules`. Elle gère les erreurs courantes telles que l'absence de fichier
        ou un format JSON invalide, et retourne un objet `ComparisonResult` détaillant le résultat.

        Args:
            file1 (Union[str, Path]): Chemin vers le premier fichier JSON à comparer.
            file2 (Union[str, Path]): Chemin vers le second fichier JSON à comparer.

        Returns:
            ComparisonResult: Résultat de la comparaison, incluant si les fichiers sont identiques,
            les différences détectées et des détails sur d'éventuelles erreurs.

        Raises:
            Aucun. Les exceptions sont capturées et traitées dans le résultat retourné.
        """
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
