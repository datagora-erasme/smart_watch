"""
Convertisseur d'horaires d'ouverture depuis le format OpenStreetMap
vers le format JSON personnalisé (../assets/opening_hours_schema.json).

Ce module fournit des fonctionnalités complètes pour convertir une spécification
opening_hours d'OSM en format JSON personnalisé.
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Union

from dotenv import load_dotenv

# sys.path.append(str(Path(__file__).parent.parent))
from core.Logger import LogOutput, create_logger

# Charger la variable d'environnement pour le nom du fichier log
load_dotenv()
csv_name = os.getenv("CSV_URL_HORAIRES")

# Initialize logger for this module
logger = create_logger(
    outputs=[LogOutput.CONSOLE, LogOutput.FILE],
    log_file=Path(__file__).parent.parent / "data" / "logs" / f"{csv_name}.log",
    module_name="OSMToCustomJson",
)


class OSMParser:
    """Parser principal pour les horaires OSM."""

    # Mapping des jours OSM vers français
    DAY_MAPPING = {
        "Mo": "lundi",
        "Tu": "mardi",
        "We": "mercredi",
        "Th": "jeudi",
        "Fr": "vendredi",
        "Sa": "samedi",
        "Su": "dimanche",
    }

    # Ordre des jours pour les plages
    DAY_ORDER = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]

    # Mapping des mois OSM vers numéros
    MONTH_MAPPING = {
        "Jan": "01",
        "Feb": "02",
        "Mar": "03",
        "Apr": "04",
        "May": "05",
        "Jun": "06",
        "Jul": "07",
        "Aug": "08",
        "Sep": "09",
        "Oct": "10",
        "Nov": "11",
        "Dec": "12",
    }

    def parse_osm_string(self, osm_string: str) -> Dict:
        """Parse une chaîne OSM complète."""
        logger.debug(f"Parsing OSM string: {osm_string[:100]}...")

        # Sépare les règles par point-virgule
        rules = [rule.strip() for rule in osm_string.split(";") if rule.strip()]

        # Sépare les règles normales des règles de dates spécifiques
        normal_rules = []
        date_rules = []

        for rule in rules:
            if self._is_date_rule(rule):
                date_rules.append(rule)
            else:
                normal_rules.append(rule)

        # Parse les règles normales (horaires réguliers et spéciaux)
        weekly_data = self._parse_weekly_rules(normal_rules)

        # Parse les règles de dates (jours fériés/spéciaux)
        special_dates = self._parse_date_rules(date_rules)

        return {
            "weekly_schedule": weekly_data.get("weekly_schedule", {}),
            "special_schedules": weekly_data.get("special_schedules", {}),
            "special_dates": special_dates,
        }

    def _is_date_rule(self, rule: str) -> bool:
        """Vérifie si une règle contient une date spécifique."""
        # Cherche le pattern YYYY MMM DD
        return bool(re.search(r"\b\d{4}\s+[A-Za-z]{3}\s+\d{1,2}\b", rule))

    def _parse_weekly_rules(self, rules: List[str]) -> Dict:
        """Parse les règles d'horaires hebdomadaires."""
        schedule = self._create_empty_weekly_schedule()
        special_schedules = {}

        for rule in rules:
            logger.debug(f"Parsing weekly rule: {rule}")

            # Sépare les parties jours et horaires
            # Format: "Tu-Fr 16:00-19:00, We,Sa 10:00-13:00,14:00-18:00"
            parts = rule.split(" ", 1)
            if len(parts) < 2:
                continue

            day_part = parts[0]
            time_part = parts[1]

            # Parse les jours et occurrences
            days_info = self._parse_days_with_occurrence(day_part)

            # Parse les horaires
            if time_part.lower() in ["off", "closed"]:
                # Jour fermé
                for day_info in days_info:
                    day = day_info["day"]
                    occurrence = day_info.get("occurrence")

                    if occurrence:
                        # Crée un horaire spécial fermé avec occurrence
                        if day not in special_schedules:
                            special_schedules[day] = {
                                "source_found": True,
                                "ouvert": False,
                                "creneaux": [
                                    {
                                        "debut": "00:00",
                                        "fin": "00:00",
                                        "occurence": occurrence,
                                    }
                                ],
                            }
                    elif day in schedule:
                        # Horaire régulier fermé
                        schedule[day]["source_found"] = True
                        schedule[day]["ouvert"] = False
            else:
                # Parse les créneaux horaires
                time_slots = self._parse_time_slots(time_part)
                for day_info in days_info:
                    day = day_info["day"]
                    occurrence = day_info.get("occurrence")

                    if occurrence:
                        # Horaire spécial avec occurrence
                        if day not in special_schedules:
                            special_schedules[day] = {
                                "source_found": True,
                                "ouvert": True,
                                "creneaux": [],
                            }

                        # Ajoute les créneaux avec occurrence
                        for slot in time_slots:
                            slot_with_occurrence = slot.copy()
                            slot_with_occurrence["occurence"] = occurrence
                            special_schedules[day]["creneaux"].append(
                                slot_with_occurrence
                            )

                        special_schedules[day]["ouvert"] = (
                            len(special_schedules[day]["creneaux"]) > 0
                        )
                    elif day in schedule:
                        # Horaire régulier
                        schedule[day]["source_found"] = True
                        schedule[day]["ouvert"] = True

                        # Ajoute les créneaux
                        for slot in time_slots:
                            schedule[day]["creneaux"].append(slot.copy())

        return {"weekly_schedule": schedule, "special_schedules": special_schedules}

    def _create_special_key(self, day: str, occurrence) -> str:
        """Crée une clé pour les horaires spéciaux avec occurrence."""
        if isinstance(occurrence, list):
            occ_str = ",".join(map(str, occurrence))
            return f"{day}[{occ_str}]"
        else:
            return f"{day}[{occurrence}]"

    def _parse_days_with_occurrence(self, day_part: str) -> List[Dict]:
        """Parse une spécification de jours avec gestion des occurrences (ex: Th[1])."""
        days_info = []

        # Cherche les occurrences [1], [1,3], etc.
        occurrence_match = re.search(r"\[([^\]]+)\]", day_part)
        occurrence = None

        if occurrence_match:
            try:
                occ_str = occurrence_match.group(1)
                if "," in occ_str:
                    occurrence = [int(x.strip()) for x in occ_str.split(",")]
                else:
                    occurrence = [int(occ_str)]
            except ValueError:
                pass

            # Supprime l'occurrence de la chaîne pour parser les jours
            day_part = re.sub(r"\[([^\]]+)\]", "", day_part)

        # Parse les jours normalement
        french_days = self._parse_days(day_part)

        # Ajoute l'information d'occurrence
        for day in french_days:
            day_info = {"day": day}
            if occurrence:
                day_info["occurrence"] = (
                    occurrence if len(occurrence) > 1 else occurrence[0]
                )
            days_info.append(day_info)

        return days_info

    def _parse_days(self, day_part: str) -> List[str]:
        """Parse une spécification de jours (ex: Tu-Fr, We,Sa)."""
        french_days = []

        # Sépare par virgule
        day_groups = [group.strip() for group in day_part.split(",")]

        for group in day_groups:
            if "-" in group:
                # Plage de jours (Tu-Fr)
                start_day, end_day = group.split("-", 1)
                start_day = start_day.strip()
                end_day = end_day.strip()

                if start_day in self.DAY_ORDER and end_day in self.DAY_ORDER:
                    start_idx = self.DAY_ORDER.index(start_day)
                    end_idx = self.DAY_ORDER.index(end_day)

                    if end_idx >= start_idx:
                        # Plage normale
                        for i in range(start_idx, end_idx + 1):
                            day = self.DAY_ORDER[i]
                            if day in self.DAY_MAPPING:
                                french_days.append(self.DAY_MAPPING[day])
                    else:
                        # Plage qui traverse la semaine (Sa-Mo)
                        for i in range(start_idx, len(self.DAY_ORDER)):
                            day = self.DAY_ORDER[i]
                            if day in self.DAY_MAPPING:
                                french_days.append(self.DAY_MAPPING[day])
                        for i in range(0, end_idx + 1):
                            day = self.DAY_ORDER[i]
                            if day in self.DAY_MAPPING:
                                french_days.append(self.DAY_MAPPING[day])
            else:
                # Jour simple
                if group in self.DAY_MAPPING:
                    french_days.append(self.DAY_MAPPING[group])

        return list(set(french_days))  # Supprime les doublons

    def _parse_time_slots(self, time_part: str) -> List[Dict]:
        """Parse les créneaux horaires (ex: 16:00-19:00,10:00-13:00,14:00-18:00)."""
        slots = []

        # Sépare par virgule pour les différents créneaux
        slot_parts = [part.strip() for part in time_part.split(",")]

        for slot_part in slot_parts:
            if "-" in slot_part and ":" in slot_part:
                # Format HH:MM-HH:MM
                try:
                    start_time, end_time = slot_part.split("-", 1)
                    start_time = start_time.strip()
                    end_time = end_time.strip()

                    # Valide le format HH:MM
                    if self._is_valid_time(start_time) and self._is_valid_time(
                        end_time
                    ):
                        slots.append({"debut": start_time, "fin": end_time})
                except ValueError:
                    logger.warning(f"Could not parse time slot: {slot_part}")

        return slots

    def _is_valid_time(self, time_str: str) -> bool:
        """Vérifie si une chaîne est un horaire valide HH:MM."""
        return bool(re.match(r"^\d{1,2}:\d{2}$", time_str))

    def _parse_date_rules(self, rules: List[str]) -> Dict:
        """Parse les règles avec dates spécifiques."""
        special_dates = {}

        for rule in rules:
            logger.debug(f"Parsing date rule: {rule}")

            # Cherche le pattern de date YYYY MMM DD
            date_match = re.search(r"(\d{4})\s+([A-Za-z]{3})\s+(\d{1,2})", rule)
            if not date_match:
                continue

            year, month_name, day = date_match.groups()

            # Convertit en format ISO
            if month_name in self.MONTH_MAPPING:
                month_num = self.MONTH_MAPPING[month_name]
                date_iso = f"{year}-{month_num}-{day.zfill(2)}"

                # Détermine le statut (closed, ouvert, ou horaires spécifiques)
                if "closed" in rule.lower() or "off" in rule.lower():
                    special_dates[date_iso] = "ferme"
                else:
                    # Parse les horaires si présents
                    # Pour l'instant, on assume que c'est fermé si pas d'horaires explicites
                    special_dates[date_iso] = "ferme"

        return special_dates

    def _create_empty_weekly_schedule(self) -> Dict:
        """Crée un planning hebdomadaire vide."""
        schedule = {}
        for french_day in self.DAY_MAPPING.values():
            schedule[french_day] = {
                "source_found": False,
                "ouvert": False,
                "creneaux": [],
            }
        return schedule


class OSMToCustomConverter:
    """Convertisseur principal d'OSM vers JSON personnalisé."""

    def __init__(self):
        self.parser = OSMParser()

    def convert_osm_string(
        self, osm_string: str, metadata: Optional[Dict] = None
    ) -> Dict:
        """Convertit une chaîne OSM en JSON personnalisé."""
        logger.info(
            f"Converting OSM string for: {metadata.get('identifiant', 'unknown') if metadata else 'unknown'}"
        )

        # Parse la chaîne OSM
        parsed_data = self.parser.parse_osm_string(osm_string)

        # Crée la structure JSON selon le schéma
        result = {
            "horaires_ouverture": {
                "metadata": metadata
                or {
                    "identifiant": "converted_from_osm",
                    "nom": "Lieu converti depuis OSM",
                    "type_lieu": "Indéterminé",
                    "url": "",
                },
                "periodes": {
                    "hors_vacances_scolaires": {
                        "source_found": True,
                        "label": "Période hors vacances scolaires",
                        "condition": "default",
                        "horaires": parsed_data.get("weekly_schedule", {}),
                    },
                    "vacances_scolaires_ete": {
                        "source_found": False,
                        "label": "Grandes vacances scolaires",
                        "condition": "SH",
                        "horaires": self._create_empty_weekly_schedule(),
                    },
                    "petites_vacances_scolaires": {
                        "source_found": False,
                        "label": "Petites vacances scolaires",
                        "condition": "SH",
                        "horaires": self._create_empty_weekly_schedule(),
                    },
                    "jours_feries": {
                        "source_found": len(parsed_data.get("special_dates", {})) > 0,
                        "label": "Jours fériés",
                        "condition": "PH",
                        "mode": "ferme",
                        "horaires_specifiques": parsed_data.get("special_dates", {}),
                    },
                    "jours_speciaux": {
                        "source_found": len(parsed_data.get("special_schedules", {}))
                        > 0,
                        "label": "Jours spéciaux",
                        "mode": "ouvert",
                        "horaires_specifiques": parsed_data.get(
                            "special_schedules", {}
                        ),
                    },
                },
                "extraction_info": {
                    "source_found": True,
                    "notes": "Converti depuis format OSM",
                },
            }
        }

        logger.info("OSM conversion completed successfully")
        return result

    def _create_empty_weekly_schedule(self) -> Dict:
        """Crée un planning hebdomadaire vide."""
        schedule = {}
        day_names = [
            "lundi",
            "mardi",
            "mercredi",
            "jeudi",
            "vendredi",
            "samedi",
            "dimanche",
        ]
        for day in day_names:
            schedule[day] = {"source_found": False, "ouvert": False, "creneaux": []}
        return schedule

    def convert_file(
        self,
        input_file: Union[str, Path],
        output_file: Optional[Union[str, Path]] = None,
    ) -> Dict:
        """Convertit un fichier contenant des chaînes OSM."""
        input_path = Path(input_file)
        if not input_path.exists():
            logger.error(f"Input file not found: {input_path}")
            raise FileNotFoundError(f"Input file not found: {input_path}")

        logger.info(f"Converting OSM file: {input_path.name}")

        with open(input_path, "r", encoding="utf-8") as f:
            if input_path.suffix.lower() == ".json":
                data = json.load(f)
            else:
                data = f.read().strip()

        if isinstance(data, str):
            result = self.convert_osm_string(data)
        elif isinstance(data, dict):
            result = {}
            for key, osm_string in data.items():
                if isinstance(osm_string, str):
                    result[key] = self.convert_osm_string(osm_string)
        else:
            raise ValueError("Unsupported input file format")

        if output_file:
            output_path = Path(output_file)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            logger.info(f"Output saved to: {output_path}")

        return result


def main():
    """Test et exemple d'utilisation."""
    logger.section("OSM TO CUSTOM JSON CONVERTER")

    converter = OSMToCustomConverter()

    # Test avec l'exemple problématique
    test_osm = """Mo,Tu,We,Fr 08:45-16:45, Th 10:00-16:45, Sa 09:30-12:00; Th[1] 13:30-16:45; 2025 Jul 05-2025 Aug 31 Mo,Tu,We,Fr 08:45-12:30,13:30-16:45, Th 10:00-12:30,13:30-16:45, Sa 09:30-12:00 "Vacances d'Été"; 2025 Oct 18-2025 Nov 02 Mo,Tu,We,Fr 08:45-12:30,13:30-16:45, Th 10:00-12:30,13:30-16:45, Sa 09:30-12:00 "Vacances de la Toussaint"; 2025 Dec 20-2026 Jan 04 Mo,Tu,We,Fr 08:45-12:30,13:30-16:45, Th 10:00-12:30,13:30-16:45, Sa 09:30-12:00 "Vacances de Noël"; 2025 Dec 26-2025 Dec 27 closed; 2026 Feb 07-2026 Feb 22 Mo,Tu,We,Fr 08:45-12:30,13:30-16:45, Th 10:00-12:30,13:30-16:45, Sa 09:30-12:00 "Vacances d'Hiver"; 2026 Apr 04-2026 Apr 19 Mo,Tu,We,Fr 08:45-12:30,13:30-16:45, Th 10:00-12:30,13:30-16:45, Sa 09:30-12:00 "Vacances de Printemps"; 2026 May 14-2026 May 17 Mo,Tu,We,Fr 08:45-12:30,13:30-16:45, Th 10:00-12:30,13:30-16:45, Sa 09:30-12:00 "Pont de l'Ascension"; 2025 Jul 12 closed; 2025 Jul 14 closed "14 juillet"; 2025 Aug 02 closed; 2025 Aug 09 closed; 2025 Aug 15 closed "Assomption"; 2025 Aug 16 closed; 2025 Aug 23 closed; 2025 Nov 01 closed "Toussaint"; 2025 Nov 11 closed "11 novembre"; 2025 Dec 25 closed "Jour de Noël"; 2026 Jan 01 closed "1er janvier"; 2026 Apr 06 closed "Lundi de Pâques"; 2026 May 01 closed "1er mai"; 2026 May 08 closed "8 mai"; 2026 May 14 closed "Ascension"; 2026 May 25 closed "Lundi de Pentecôte"; 2026 Jul 14 closed "14 juillet"; 2026 Aug 15 closed "Assomption"; 2026 Nov 01 closed "Toussaint"; 2026 Nov 11 closed "11 novembre"; 2026 Dec 25 closed "Jour de Noël"""

    metadata = {
        "identifiant": "S7806",
        "nom": "Médiathèque du Tonkin",
        "type_lieu": "bibliothèque",
        "url": "https://mediatheques.villeurbanne.fr/2024/06/horaires-hors-vacances-dete/",
    }

    logger.info("Testing OSM conversion")
    result = converter.convert_osm_string(test_osm, metadata)

    print("Résultat de la conversion:")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
