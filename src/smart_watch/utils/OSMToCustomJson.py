# Convertisseur de données horaires d'ouverture OSM vers JSON personnalisé
# https://datagora-erasme.github.io/smart_watch/source/modules/utils/OSMToCustomJson.html

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union

from ..core.ErrorHandler import ErrorCategory, ErrorSeverity, handle_errors
from ..core.Logger import create_logger

# Initialize logger for this module
logger = create_logger(
    module_name="OSMToCustomJson",
)


# --- Data Classes (Modèles de données purs) ---
@dataclass
class TimeSlot:
    """Représente un créneau horaire."""

    start: str  # HH:MM
    end: str  # HH:MM
    occurrence: Optional[Union[int, List[int]]] = None


@dataclass
class DaySchedule:
    """Représente les horaires d'une journée."""

    source_found: bool = False
    open: bool = False
    time_slots: List[TimeSlot] = field(default_factory=list)


@dataclass
class SpecialDate:
    """Représente un jour spécial/férié."""

    date: str  # YYYY-MM-DD
    status: str  # "ferme" ou objet horaires
    description: Optional[str] = None


# --- Parser Class (Logique de parsing de la chaîne OSM) ---
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

    @handle_errors(
        category=ErrorCategory.PARSING,
        severity=ErrorSeverity.MEDIUM,
        user_message="Erreur lors du parsing de la chaîne OSM.",
        default_return={},
    )
    def parse_osm_string(self, osm_string: str) -> Dict:
        """Parse une chaîne OSM complète avec une approche robuste."""
        logger.debug(f"Parsing OSM string: {osm_string[:100]}...")

        # Cas spécial : lieu fermé définitivement
        if osm_string.strip().lower() == "closed":
            return self._create_closed_schedule()

        # Sépare les règles par point-virgule
        rules = [rule.strip() for rule in osm_string.split(";") if rule.strip()]

        # Initialise les structures de données
        weekly_schedule = self._create_empty_weekly_schedule()
        special_dates = []
        vacation_periods = []

        # Parse chaque règle
        for rule in rules:
            if self._is_date_rule(rule):
                # Règle avec date spécifique
                if self._is_vacation_period(rule):
                    vacation_periods.append(rule)
                else:
                    special_date = self._parse_special_date(rule)
                    if special_date:
                        special_dates.append(special_date)
            else:
                # Règle d'horaires réguliers
                self._parse_regular_schedule(rule, weekly_schedule)

        return {
            "weekly_schedule": weekly_schedule,
            "special_schedules": {},  # Pour les horaires spéciaux avec occurrences
            "special_dates": special_dates,
            "vacation_periods": vacation_periods,
            "permanently_closed": False,
        }

    def _create_closed_schedule(self) -> Dict:
        """Crée un planning pour un lieu fermé définitivement."""
        weekly_schedule = {}
        for french_day in self.DAY_MAPPING.values():
            weekly_schedule[french_day] = DaySchedule(source_found=True, open=False)

        return {
            "weekly_schedule": weekly_schedule,
            "special_schedules": {},
            "special_dates": [],
            "vacation_periods": [],
            "permanently_closed": True,
        }

    def _create_empty_weekly_schedule(self) -> Dict[str, DaySchedule]:
        """Crée un planning hebdomadaire vide."""
        return {french_day: DaySchedule() for french_day in self.DAY_MAPPING.values()}

    def _is_date_rule(self, rule: str) -> bool:
        """Vérifie si une règle contient une date spécifique."""
        # Patterns pour détecter les dates
        date_patterns = [
            r"\b\d{4}\s+[A-Za-z]{3}\s+\d{1,2}\b",  # YYYY MMM DD
            r"\b\d{4}\s+[A-Za-z]{3}\s+\d{1,2}-\d{4}\s+[A-Za-z]{3}\s+\d{1,2}\b",  # Period
        ]
        return any(re.search(pattern, rule) for pattern in date_patterns)

    def _is_vacation_period(self, rule: str) -> bool:
        """Vérifie si c'est une période de vacances (avec une plage de dates)."""
        # Une période de vacances doit contenir une plage de dates.
        # On cherche un motif comme "YYYY Mon DD-" qui indique un début de plage.
        # Cela évite de classifier à tort un jour férié unique (ex: "Toussaint")
        # comme une période de vacances.
        return bool(re.search(r"\d{4}\s+[A-Za-z]{3}\s+\d{1,2}-", rule))

    def _parse_special_date(self, rule: str) -> Optional[SpecialDate]:
        """Parse une règle de date spéciale."""
        # Pattern amélioré pour capturer date et statut
        # Cherche d'abord le pattern complet avec statut
        date_match = re.search(
            r"(\d{4})\s+([A-Za-z]{3})\s+(\d{1,2})\s+(closed|open)", rule
        )

        if not date_match:
            # Fallback : cherche juste la date si "closed" est présent ailleurs dans la règle
            if "closed" in rule.lower():
                date_match = re.search(r"(\d{4})\s+([A-Za-z]{3})\s+(\d{1,2})", rule)
                if date_match:
                    year, month_str, day = date_match.groups()
                    status = "closed"  # Par défaut fermé si "closed" est dans la règle
                else:
                    return None
            else:
                return None
        else:
            year, month_str, day, status = date_match.groups()

        # Convertit en format ISO
        if month_str not in self.MONTH_MAPPING:
            logger.warning(f"Mois non reconnu: {month_str}")
            return None

        month_num = self.MONTH_MAPPING[month_str]
        # S'assurer que le jour est correctement formaté
        day_formatted = day.zfill(2)
        date_iso = f"{year}-{month_num}-{day_formatted}"

        # Log pour debug
        logger.debug(f"Parsing date: {year} {month_str} {day} -> {date_iso}")

        # Détermine le statut final
        final_status = "ferme" if status.lower() == "closed" else "ouvert"

        # Extrait la description entre guillemets
        description_match = re.search(r'"([^"]*)"', rule)
        description = description_match.group(1) if description_match else None

        return SpecialDate(date=date_iso, status=final_status, description=description)

    def _parse_regular_schedule(
        self, rule: str, weekly_schedule: Dict[str, DaySchedule]
    ):
        """Parse une règle d'horaires réguliers avec approche robuste."""
        logger.debug(f"Parsing regular schedule: {rule}")

        # Divise la règle en segments individuels
        segments = self._tokenize_rule(rule)

        for segment in segments:
            self._parse_segment(segment, weekly_schedule)

    def _tokenize_rule(self, rule: str) -> List[str]:
        """
        Divise une règle en segments individuels.
        Approche robuste qui gère tous les cas de figure.
        """
        # Pattern pour identifier les segments : jours suivis d'horaires
        # Gère les cas comme "Mo-Fr 08:00-12:00", "Mo,We 14:00-18:00", "Th[1] 10:00-12:00"
        pattern = r"([A-Z][a-z](?:\[[^\]]+\])?(?:[-,][A-Z][a-z])*)\s+([0-9:,-]+(?:\s*-\s*[0-9:]+)*)"

        segments = []
        last_end = 0

        for match in re.finditer(pattern, rule):
            # Vérifie s'il y a du texte non traité avant ce match
            if match.start() > last_end:
                potential_segment = rule[last_end : match.start()].strip()
                if potential_segment and not potential_segment.startswith(","):
                    # Essaie de parser ce segment avec l'ancienne méthode
                    old_segments = self._fallback_tokenize(potential_segment)
                    segments.extend(old_segments)

            # Ajoute le segment trouvé
            segment = f"{match.group(1)} {match.group(2)}"
            segments.append(segment)
            last_end = match.end()

        # Traite le reste de la règle s'il y en a
        if last_end < len(rule):
            remaining = rule[last_end:].strip()
            if remaining and not remaining.startswith(","):
                old_segments = self._fallback_tokenize(remaining)
                segments.extend(old_segments)

        # Si aucun segment trouvé, utilise l'ancienne méthode en fallback
        if not segments:
            segments = self._fallback_tokenize(rule)

        return [s.strip() for s in segments if s.strip()]

    def _fallback_tokenize(self, rule: str) -> List[str]:
        """Méthode de fallback pour tokeniser les règles."""
        # Découpe simple par virgule, mais intelligente
        parts = rule.split(",")
        segments = []
        current_segment = ""

        for part in parts:
            part = part.strip()
            if current_segment:
                # Vérifie si cette partie commence par un jour
                if re.match(r"^[A-Z][a-z]", part):
                    # Nouvelle règle, sauvegarde la précédente
                    segments.append(current_segment)
                    current_segment = part
                else:
                    # Continue la règle précédente
                    current_segment += f", {part}"
            else:
                current_segment = part

        if current_segment:
            segments.append(current_segment)

        return segments

    def _parse_segment(self, segment: str, weekly_schedule: Dict[str, DaySchedule]):
        """Parse un segment individuel jour+horaire."""
        logger.debug(f"Parsing segment: {segment}")

        # Sépare jours et horaires
        parts = segment.split(None, 1)  # Split sur le premier espace
        if len(parts) < 2:
            return

        day_part = parts[0]
        time_part = parts[1]

        # Parse les jours avec gestion des occurrences
        days_info = self._parse_days_with_occurrence(day_part)

        # Parse les horaires
        if time_part.lower() in ["off", "closed"]:
            # Jour fermé
            for day_info in days_info:
                day = day_info["day"]
                if day in weekly_schedule:
                    weekly_schedule[day].source_found = True
                    weekly_schedule[day].open = False
                    weekly_schedule[day].time_slots = []  # Assurer la cohérence
        else:
            # Parse les créneaux horaires
            time_slots = self._parse_time_slots(
                time_part, days_info[0].get("occurrence") if days_info else None
            )

            for day_info in days_info:
                day = day_info["day"]
                occurrence = day_info.get("occurrence")

                if day in weekly_schedule:
                    weekly_schedule[day].source_found = True
                    weekly_schedule[day].open = True

                    # Ajoute les créneaux (cumulatif pour gérer les multiples segments)
                    for slot in time_slots:
                        new_slot = TimeSlot(
                            start=slot["start"], end=slot["end"], occurrence=occurrence
                        )
                        weekly_schedule[day].time_slots.append(new_slot)

    def _parse_days_with_occurrence(self, day_part: str) -> List[Dict]:
        """Parse une spécification de jours avec gestion des occurrences."""
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
                    occurrence = int(occ_str)
            except ValueError:
                logger.warning(f"Impossible de parser l'occurrence: {occ_str}")
                pass  # Garde occurrence=None

            # Supprime l'occurrence de la chaîne
            day_part = re.sub(r"\[([^\]]+)\]", "", day_part)

        # Parse les jours
        french_days = self._parse_days(day_part)

        # Ajoute l'information d'occurrence
        for day in french_days:
            day_info = {"day": day}
            if occurrence is not None:
                day_info["occurrence"] = occurrence
            days_info.append(day_info)

        return days_info

    def _parse_days(self, day_part: str) -> List[str]:
        """Parse une spécification de jours."""
        french_days = []

        # Sépare par virgule
        day_groups = [group.strip() for group in day_part.split(",")]

        for group in day_groups:
            if "-" in group:
                # Plage de jours
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
                        # Plage qui traverse la semaine
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

        return list(
            dict.fromkeys(french_days)
        )  # Supprime les doublons en préservant l'ordre

    def _parse_time_slots(
        self, time_part: str, occurrence: Optional[Union[int, List[int]]] = None
    ) -> List[Dict]:
        """Parse les créneaux horaires."""
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
                        slots.append({"start": start_time, "end": end_time})
                except ValueError:
                    logger.warning(f"Could not parse time slot: {slot_part}")

        return slots

    def _is_valid_time(self, time_str: str) -> bool:
        """Vérifie si une chaîne est un horaire valide HH:MM."""
        return bool(re.match(r"^\d{1,2}:\d{2}$", time_str))


# --- Converter Class (Mise en forme du résultat du parsing en JSON final) ---
class OsmToJsonConverter:
    """Convertisseur principal d'OSM vers JSON personnalisé."""

    def __init__(self):
        self.parser = OSMParser()

    @handle_errors(
        category=ErrorCategory.CONVERSION,
        severity=ErrorSeverity.HIGH,
        user_message="Erreur lors de la conversion de la chaîne OSM en JSON.",
        default_return={},
    )
    def convert_osm_string(
        self, osm_string: str, metadata: Optional[Dict] = None
    ) -> Dict:
        """Convertit une chaîne OSM en JSON personnalisé."""
        logger.info(
            f"Converting OSM string for: {metadata.get('identifiant', 'unknown') if metadata else 'unknown'}"
        )

        # Parse la chaîne OSM
        parsed_data = self.parser.parse_osm_string(osm_string)
        if not parsed_data:
            return {}  # Erreur de parsing gérée par le décorateur de `parse_osm_string`

        special_dates_list = parsed_data.get("special_dates", [])
        special_dates_dict = {sd.date: sd.status for sd in special_dates_list}

        # Crée la structure JSON selon le schéma
        result = {
            "horaires_ouverture": {
                "metadata": metadata
                or {
                    "identifiant": "converted_from_osm",
                    "nom": "Lieu converti depuis OSM",
                    "type_lieu": "Indéterminé",
                    "url": "",
                    "timezone": "Europe/Paris",
                },
                "periodes": {
                    "hors_vacances_scolaires": {
                        "source_found": True,
                        "label": "Période hors vacances scolaires",
                        "condition": "default",
                        "horaires": self._format_weekly_schedule(
                            parsed_data.get("weekly_schedule", {})
                        ),
                    },
                    "vacances_scolaires_ete": {
                        "source_found": False,
                        "label": "Grandes vacances scolaires",
                        "condition": "SH",
                        "horaires": self._create_empty_formatted_schedule(),
                    },
                    "petites_vacances_scolaires": {
                        "source_found": False,
                        "label": "Petites vacances scolaires",
                        "condition": "SH",
                        "horaires": self._create_empty_formatted_schedule(),
                    },
                    "jours_feries": {
                        "source_found": len(special_dates_dict) > 0,
                        "label": "Jours fériés",
                        "condition": "PH",
                        "mode": "ferme",
                        "horaires_specifiques": special_dates_dict,
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
                    "permanently_closed": parsed_data.get("permanently_closed", False),
                    "notes": "Converti depuis format OSM",
                },
            }
        }

        logger.info("OSM conversion completed successfully")
        return result

    def _format_weekly_schedule(self, weekly_schedule: Dict[str, DaySchedule]) -> Dict:
        """Convertit le planning de DaySchedule en dictionnaire JSON."""
        formatted = {}
        for day, schedule in weekly_schedule.items():
            formatted[day] = {
                "source_found": schedule.source_found,
                "ouvert": schedule.open,
                "creneaux": [self._format_time_slot(ts) for ts in schedule.time_slots],
            }
        return formatted

    def _format_time_slot(self, time_slot: TimeSlot) -> Dict:
        """Convertit un TimeSlot en dictionnaire JSON."""
        result = {"debut": time_slot.start, "fin": time_slot.end}
        if time_slot.occurrence is not None:
            result["occurence"] = time_slot.occurrence
        return result

    def _create_empty_formatted_schedule(self) -> Dict:
        """Crée un planning hebdomadaire formaté et vide."""
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
