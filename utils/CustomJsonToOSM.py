"""
Convertisseur d'horaires d'ouverture au format OpenStreetMap,
en se basant sur le format JSON personnalisé (../assets/opening_hours_schema.json).

Ce module fournit des fonctionnalités complètes pour convertir un format JSON personnalisé
en spécification opening_hours d'OSM.
"""

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

try:
    from dateutil import parser as date_parser
except ImportError:
    date_parser = None
    print(
        "Avertissement : dateutil n'est pas disponible. L'analyse des dates sera limitée."
    )


@dataclass
class ConversionResult:
    """Conteneur pour les résultats de conversion avec métadonnées."""

    osm_periods: Dict[str, str]

    def __post_init__(self):
        pass


@dataclass
class TimeSlot:
    """Représente un créneau horaire avec validation."""

    start: str
    end: str
    occurence: Optional[Union[int, List[int]]] = None  # Ajout du champ occurence

    def __post_init__(self):
        if not self._validate_time_format(self.start):
            raise ValueError(f"Format d'heure de début invalide : {self.start}")
        if not self._validate_time_format(self.end):
            raise ValueError(f"Format d'heure de fin invalide : {self.end}")

    @staticmethod
    def _validate_time_format(time_str: str) -> bool:
        """Valide le format d'heure HH:MM."""
        try:
            parts = time_str.split(":")
            if len(parts) != 2:
                return False
            hour, minute = int(parts[0]), int(parts[1])
            return 0 <= hour <= 23 and 0 <= minute <= 59
        except (ValueError, IndexError):
            return False

    def to_osm_format(self) -> str:
        """Convertit en format de plage horaire OSM (sans jour)."""
        return f"{self.start}-{self.end}"


class OSMDayMapper:
    """Gère le mappage et la validation des noms de jours."""

    DAY_MAPPING = {
        "lundi": "Mo",
        "mardi": "Tu",
        "mercredi": "We",
        "jeudi": "Th",
        "vendredi": "Fr",
        "samedi": "Sa",
        "dimanche": "Su",
    }

    DAY_ORDER = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]

    @classmethod
    def normalize_day(cls, day: str) -> Optional[str]:
        """Convertit un nom de jour en français au format OSM."""
        return cls.DAY_MAPPING.get(day.lower())

    @classmethod
    def compress_day_ranges(cls, days: List[str]) -> str:
        """Compresse les jours consécutifs en plages (Mo-Fr, Sa-Su, etc.)."""
        if not days:
            return ""

        day_indices = {day: i for i, day in enumerate(cls.DAY_ORDER)}
        days = sorted(set(days), key=lambda d: day_indices.get(d, 99))

        ranges = []
        start_idx = 0

        while start_idx < len(days):
            end_idx = start_idx

            # Trouve les jours consécutifs
            while (
                end_idx + 1 < len(days)
                and day_indices.get(days[end_idx + 1], 99)
                == day_indices.get(days[end_idx], 99) + 1
            ):
                end_idx += 1

            # Formate la plage
            if start_idx == end_idx:
                ranges.append(days[start_idx])
            else:
                ranges.append(f"{days[start_idx]}-{days[end_idx]}")

            start_idx = end_idx + 1

        return ",".join(ranges)


class DateParser:
    """Gère l'analyse des dates avec prise en charge de plusieurs formats."""

    MONTH_MAPPING = {
        "janvier": "January",
        "jan": "Jan",
        "février": "February",
        "fév": "Feb",
        "fevrier": "February",
        "fev": "Feb",
        "mars": "March",
        "mar": "Mar",
        "avril": "April",
        "avr": "Apr",
        "mai": "May",
        "juin": "June",
        "juillet": "July",
        "juil": "Jul",
        "août": "August",
        "aout": "August",
        "septembre": "September",
        "sep": "Sep",
        "sept": "Sep",
        "octobre": "October",
        "oct": "Oct",
        "novembre": "November",
        "nov": "Nov",
        "décembre": "December",
        "déc": "Dec",
        "decembre": "December",
        "dec": "Dec",
    }

    @classmethod
    def parse_date_to_osm(cls, date_desc: str) -> Optional[str]:
        """Analyse une description de date au format OSM (YYYY MMM DD)."""
        if not date_desc or not isinstance(date_desc, str):
            return None

        try:
            # Normalise les noms de mois en français
            normalized = date_desc.lower()
            for fr, en in cls.MONTH_MAPPING.items():
                normalized = normalized.replace(fr, en)

            if date_parser:
                parsed_date = date_parser.parse(normalized, fuzzy=True)
                return parsed_date.strftime("%Y %b %d")
            else:
                # Analyse de base en cas de fallback
                return cls._basic_date_parse(normalized)

        except Exception:
            return None

    @classmethod
    def _basic_date_parse(cls, date_str: str) -> Optional[str]:
        """Analyse de base des dates sans dateutil."""
        # Modèle simple YYYY-MM-DD
        import re

        pattern = r"(\d{4})-(\d{1,2})-(\d{1,2})"
        match = re.search(pattern, date_str)
        if match:
            year, month, day = match.groups()
            try:
                dt = datetime(int(year), int(month), int(day))
                return dt.strftime("%Y %b %d")
            except ValueError:
                pass
        return None


class OSMConverter:
    """
    Convertisseur d'horaires d'ouverture OpenStreetMap.

    Convertit un format JSON personnalisé en spécification opening_hours d'OSM.
    """

    def __init__(self):
        """Initialise le convertisseur OSM."""
        self.day_mapper = OSMDayMapper()
        self.date_parser = DateParser()

    def _process_time_slots(self, slots: List[Dict]) -> List[TimeSlot]:
        """Traite et valide les créneaux horaires."""
        processed_slots = []

        for slot in slots:
            try:
                if isinstance(slot, dict) and "debut" in slot and "fin" in slot:
                    occurence = slot.get("occurence")
                    # Si occurence est une liste, la garder, sinon None ou int
                    if isinstance(occurence, list):
                        occur = occurence
                    elif occurence is not None:
                        occur = [occurence]
                    else:
                        occur = None
                    time_slot = TimeSlot(slot["debut"], slot["fin"], occurence=occur)
                    processed_slots.append(time_slot)
            except ValueError:
                continue

        return processed_slots

    def _process_daily_hours(self, day_data: Dict) -> Optional[List[Dict]]:
        """Traite les horaires pour un jour donné. Retourne une liste de dicts {occurence, slot_str}."""
        if not isinstance(day_data, dict):
            return None

        if not day_data.get("source_found", True):
            return None

        time_slots = day_data.get("creneaux", [])

        results = []
        if time_slots:
            processed_slots = self._process_time_slots(time_slots)
            for slot in processed_slots:
                # slot.occurence est soit None, soit une liste d'entiers
                results.append(
                    {"occurence": slot.occurence, "slot_str": slot.to_osm_format()}
                )
            return results if results else None

        is_open = day_data.get("ouvert", False)
        if not is_open:
            return None

        return None

    def _process_weekly_schedule(self, schedule: Dict) -> str:
        """Traite les données d'horaires hebdomadaires avec gestion des occurences."""
        if not isinstance(schedule, dict):
            return ""

        # Pour chaque jour, on collecte une liste de tuples (occurence, slot_str)
        day_slots = {}

        for day_name, day_data in schedule.items():
            osm_day = self.day_mapper.normalize_day(day_name)
            if not osm_day:
                continue

            if not day_data.get("source_found", True):
                continue

            slot_infos = self._process_daily_hours(day_data)
            if slot_infos:
                day_slots[osm_day] = slot_infos

        # On va regrouper par (occurence, slot_str) pour tous les jours
        # Structure : {(tuple_occurence, slot_str): [osm_day, ...]}
        slot_groups = {}
        for osm_day, slot_infos in day_slots.items():
            for slot_info in slot_infos:
                occur = slot_info["occurence"]
                slot_str = slot_info["slot_str"]
                # Pour la clé, tuple(occur) ou None
                occur_key = (
                    tuple(occur)
                    if isinstance(occur, list)
                    else (occur,)
                    if occur is not None
                    else None
                )
                group_key = (occur_key, slot_str)
                if group_key not in slot_groups:
                    slot_groups[group_key] = []
                slot_groups[group_key].append(osm_day)

        # Génération du format OSM
        osm_parts = []
        for (occur_key, slot_str), days in slot_groups.items():
            day_ranges = self.day_mapper.compress_day_ranges(days)
            # Ajout du [n] ou [n,m] si occurence
            if occur_key and any(x is not None for x in occur_key):
                occur_list = [str(x) for x in occur_key if x is not None]
                occur_part = f"[{','.join(occur_list)}]"
            else:
                occur_part = ""
            osm_parts.append(f"{day_ranges}{occur_part} {slot_str}")

        # Gestion des jours fermés (off)
        closed_days = []
        for day in self.day_mapper.DAY_ORDER:
            if day not in day_slots:
                closed_days.append(day)
        if closed_days:
            day_ranges = self.day_mapper.compress_day_ranges(closed_days)
            osm_parts.append(f"{day_ranges} off")

        return "; ".join(osm_parts)

    def _process_special_days(self, special_data: Dict) -> str:
        """Traite les jours spéciaux (jours fériés, exceptions)."""
        if not special_data.get("source_found", False):
            return ""

        specific_schedules = special_data.get("horaires_specifiques", {})

        if not specific_schedules:
            # Utilise le mode par défaut
            mode = special_data.get("mode", "ferme")
            condition = special_data.get("condition", "PH")

            if mode == "ferme":
                return f"{condition} off"
            elif mode == "ouvert":
                return f"{condition} open"
            else:
                return ""

        # Traite les dates spécifiques
        osm_parts = []

        for date_desc, schedule_data in specific_schedules.items():
            try:
                # Analyse la date
                osm_date = self.date_parser.parse_date_to_osm(date_desc)

                # Traite l'horaire
                if isinstance(schedule_data, dict):
                    if not schedule_data.get("source_found", True):
                        continue

                    if schedule_data.get("ouvert", False):
                        slots = schedule_data.get("creneaux", [])
                        if slots:
                            processed_slots = self._process_time_slots(slots)

                            if processed_slots:
                                schedule_str = ",".join(
                                    slot.to_osm_format() for slot in processed_slots
                                )
                                date_part = osm_date or "PH"
                                osm_parts.append(f"{date_part} {schedule_str}")
                        else:
                            date_part = osm_date or "PH"
                            osm_parts.append(f"{date_part} open")
                    else:
                        date_part = osm_date or "PH"
                        osm_parts.append(f"{date_part} off")

                elif isinstance(schedule_data, str):
                    if schedule_data.lower() in ["fermé", "ferme", "closed"]:
                        date_part = osm_date or "PH"
                        osm_parts.append(f"{date_part} off")
                    else:
                        date_part = osm_date or "PH"
                        osm_parts.append(f"{date_part} {schedule_data}")

            except Exception:
                continue

        return "; ".join(osm_parts)

    def _has_valid_source_in_period(self, period_data: Dict) -> bool:
        """Vérifie si une période contient des données source valides."""
        if not isinstance(period_data, dict) or not period_data.get(
            "source_found", False
        ):
            return False

        # Vérifie les horaires hebdomadaires
        if "horaires" in period_data:
            horaires = period_data["horaires"]
            if isinstance(horaires, dict):
                return any(
                    day_data.get("source_found", True)
                    for day_data in horaires.values()
                    if isinstance(day_data, dict)
                )

        # Vérifie les horaires spécifiques
        if "horaires_specifiques" in period_data:
            schedules = period_data["horaires_specifiques"]
            if isinstance(schedules, dict):
                return any(
                    schedule.get("source_found", True)
                    if isinstance(schedule, dict)
                    else True
                    for schedule in schedules.values()
                )

        return True

    def convert_to_osm(self, data: Dict) -> ConversionResult:
        """
        Méthode principale de conversion.

        Args:
            data: Données JSON en entrée

        Returns:
            ConversionResult avec les périodes OSM
        """
        try:
            # Convertit par périodes
            periods_result = self._convert_by_periods(data)
            return ConversionResult(osm_periods=periods_result)

        except Exception:
            return ConversionResult(osm_periods={})

    def _convert_by_periods(self, data: Dict) -> Dict[str, str]:
        """Convertit les données par périodes individuelles."""
        periods_result = {}

        horaires_data = data.get("horaires_ouverture", {})
        periods = horaires_data.get("periodes", {})

        # Traite chaque période
        for period_key, period_data in periods.items():
            if not isinstance(period_data, dict):
                continue

            if not self._has_valid_source_in_period(period_data):
                continue

            try:
                if period_key in [
                    "hors_vacances_scolaires",
                    "vacances_scolaires_ete",
                    "petites_vacances_scolaires",
                ]:
                    # Horaires hebdomadaires
                    schedule = period_data.get("horaires", {})
                    if schedule:
                        osm_str = self._process_weekly_schedule(schedule)
                        if osm_str:
                            periods_result[period_key] = osm_str

                elif period_key in ["jours_feries", "jours_speciaux"]:
                    # Jours spéciaux
                    osm_str = self._process_special_days(period_data)
                    if osm_str:
                        periods_result[period_key] = osm_str

            except Exception:
                continue

        return periods_result

    def convert_file(
        self,
        input_file: Union[str, Path],
        output_file: Optional[Union[str, Path]] = None,
    ) -> Dict[str, ConversionResult]:
        """
        Convertit un fichier JSON entier.

        Args:
            input_file: Chemin du fichier JSON en entrée
            output_file: Chemin optionnel du fichier de sortie

        Returns:
            Dictionnaire des résultats de conversion par identifiant
        """
        input_path = Path(input_file)
        if not input_path.exists():
            raise FileNotFoundError(f"Fichier d'entrée introuvable : {input_path}")

        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        results = {}

        if isinstance(data, list):
            for i, item in enumerate(data):
                metadata = item.get("horaires_ouverture", {}).get("metadata", {})
                identifier = metadata.get("identifiant", f"item_{i}")
                results[identifier] = self.convert_to_osm(item)
        else:
            metadata = data.get("horaires_ouverture", {}).get("metadata", {})
            identifier = metadata.get("identifiant", "single_item")
            results[identifier] = self.convert_to_osm(data)

        if output_file:
            output_path = Path(output_file)
            output_data = {
                identifier: {
                    "osm_periods": result.osm_periods,
                }
                for identifier, result in results.items()
            }

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

        return results


def main():
    """Exemple d'utilisation et tests."""

    print("=== CONVERTISSEUR OSM ===")

    # Initialise le convertisseur
    converter = OSMConverter()

    # Test avec une base de données
    db_path = Path(
        r"C:\Users\beranger\Documents\GitHub\smart_watch\data\alerte_modif_horaire_lieu_unique_devstral.db"
    )

    if not db_path.exists():
        print(f"Base de données introuvable : {db_path}")
        return

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT identifiant, nom, url, llm_horaires_json 
                FROM alerte_modif_horaire_lieu_unique 
                WHERE llm_horaires_json IS NOT NULL 
                LIMIT 5
            """)

            for record in cursor.fetchall():
                item_id, nom, url, llm_horaires_json = record

                try:
                    horaires_data = json.loads(llm_horaires_json)
                    result = converter.convert_to_osm(horaires_data)

                    print(f"\nID : {item_id}")
                    print(f"Nom : {nom}")

                    if result.osm_periods:
                        print("Périodes :")
                        for period, osm_format in result.osm_periods.items():
                            print(f"  {period} : {osm_format}")
                    else:
                        print("Aucune période trouvée")

                    print("-" * 50)

                except json.JSONDecodeError:
                    print(f"Erreur de décodage JSON pour {item_id}")
                except Exception:
                    print(f"Erreur de conversion pour {item_id}")

    except sqlite3.Error as e:
        print(f"Erreur de base de données : {e}")


if __name__ == "__main__":
    main()
