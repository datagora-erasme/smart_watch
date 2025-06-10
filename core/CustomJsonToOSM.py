# Script de conversion du format Json Custom, vers le format OSM standard

import json
import re
import sqlite3
from typing import Any, Dict, List, Optional


class OSMConverter:
    """Converter from custom JSON opening hours format to OSM opening_hours syntax."""

    DAY_MAPPING = {
        "lundi": "Mo",
        "monday": "Mo",
        "mardi": "Tu",
        "tuesday": "Tu",
        "mercredi": "We",
        "wednesday": "We",
        "jeudi": "Th",
        "thursday": "Th",
        "vendredi": "Fr",
        "friday": "Fr",
        "samedi": "Sa",
        "saturday": "Sa",
        "dimanche": "Su",
        "sunday": "Su",
    }

    def __init__(self):
        self.debug = False

    def parse_time_range(self, time_str: str) -> Optional[str]:
        """Parse and normalize time range string."""
        if not time_str or time_str.lower() in ["fermé", "ferme", "closed"]:
            return None

        # Handle multiple ranges separated by comma
        if "," in time_str:
            ranges = [self.parse_time_range(r.strip()) for r in time_str.split(",")]
            ranges = [r for r in ranges if r]  # Filter out None values
            return ",".join(ranges) if ranges else None

        # Clean and normalize format
        time_str = time_str.strip().replace(" ", "").replace("h", ":")

        # Match HH:MM-HH:MM pattern
        match = re.match(r"(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})", time_str)
        if match:
            start_h, start_m, end_h, end_m = match.groups()
            return f"{int(start_h):02d}:{start_m}-{int(end_h):02d}:{end_m}"

        return None

    def normalize_day_name(self, day: str) -> Optional[str]:
        """Convert French day name to OSM format."""
        return self.DAY_MAPPING.get(day.lower())

    def parse_day_schedule(self, day_data: Any) -> Optional[str]:
        """Parse schedule for a single day."""
        if isinstance(day_data, str):
            return self.parse_time_range(day_data)
        elif isinstance(day_data, list):
            ranges = [self.parse_time_range(str(item)) for item in day_data]
            ranges = [r for r in ranges if r]
            return ",".join(ranges) if ranges else None
        elif isinstance(day_data, dict):
            # Handle schema-compliant format
            if "ouvert" in day_data and not day_data["ouvert"]:
                return None
            if "creneaux" in day_data:
                ranges = []
                for creneau in day_data["creneaux"]:
                    if (
                        isinstance(creneau, dict)
                        and "debut" in creneau
                        and "fin" in creneau
                    ):
                        ranges.append(f"{creneau['debut']}-{creneau['fin']}")
                return ",".join(ranges) if ranges else None

        return None

    def group_consecutive_days(self, schedule: Dict[str, str]) -> List[str]:
        """Group consecutive days with same schedule."""
        if not schedule:
            return []

        # Day order for grouping
        day_order = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]

        # Group days by schedule
        schedule_groups = {}
        for day in day_order:
            if day in schedule:
                sched = schedule[day]
                if sched not in schedule_groups:
                    schedule_groups[sched] = []
                schedule_groups[sched].append(day)

        # Convert to OSM format
        osm_parts = []
        for sched, days in schedule_groups.items():
            if not sched:  # Skip closed days
                osm_parts.append(f"{','.join(days)} off")
                continue

            # Group consecutive days
            day_ranges = self.compress_day_ranges(days)
            osm_parts.append(f"{day_ranges} {sched}")

        return osm_parts

    def compress_day_ranges(self, days: List[str]) -> str:
        """Compress consecutive days into ranges (Mo-Fr, Sa-Su, etc.)."""
        day_order = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        day_indices = {day: i for i, day in enumerate(day_order)}

        # Sort days by order
        days = sorted(days, key=lambda d: day_indices[d])

        if not days:
            return ""

        ranges = []
        start = days[0]
        prev_idx = day_indices[start]

        for i in range(1, len(days)):
            curr_idx = day_indices[days[i]]
            if curr_idx != prev_idx + 1:
                # Break in sequence
                if start == days[i - 1]:
                    ranges.append(start)
                else:
                    ranges.append(f"{start}-{days[i - 1]}")
                start = days[i]
            prev_idx = curr_idx

        # Handle last range
        if start == days[-1]:
            ranges.append(start)
        else:
            ranges.append(f"{start}-{days[-1]}")

        return ",".join(ranges)

    def convert_weekly_schedule(self, schedule_data: Dict) -> str:
        """Convert weekly schedule to OSM format."""
        normalized_schedule = {}

        for day_key, day_data in schedule_data.items():
            osm_day = self.normalize_day_name(day_key)
            if osm_day:
                parsed_schedule = self.parse_day_schedule(day_data)
                if parsed_schedule is not None:
                    normalized_schedule[osm_day] = parsed_schedule
                else:
                    normalized_schedule[osm_day] = None  # Closed

        osm_parts = self.group_consecutive_days(normalized_schedule)
        return "; ".join(osm_parts)

    def convert_special_days(self, special_data: Dict) -> List[str]:
        """Convert special days/holidays to OSM format."""
        osm_parts = []

        for date_desc, schedule in special_data.items():
            # Simple handling - more sophisticated date parsing could be added
            if isinstance(schedule, str):
                if schedule.lower() in ["fermé", "ferme", "closed"]:
                    # Try to extract date pattern for OSM
                    if any(
                        word in date_desc.lower()
                        for word in ["mai", "juin", "juillet", "août"]
                    ):
                        osm_parts.append("PH off")  # Generic public holidays off
                else:
                    parsed = self.parse_time_range(schedule)
                    if parsed:
                        osm_parts.append(f"PH {parsed}")

        return osm_parts

    def convert_to_osm(self, data: Dict) -> str:
        """Convert complete schedule data to OSM opening_hours format."""
        osm_parts = []

        # Handle main schedule periods
        periods_to_check = [
            ("hors_vacances_scolaires", None),
            ("horaires.hors_vacances_scolaires", None),
            ("vacances_scolaires", "SH"),
            ("horaires.vacances_scolaires", "SH"),
            ("petites_vacances", "SH"),
            ("grandes_vacances", "SH off"),
            ("vacances_ete", "SH"),
        ]

        for period_path, condition in periods_to_check:
            schedule_data = self.get_nested_value(data, period_path)
            if schedule_data and isinstance(schedule_data, dict):
                # Handle multi-zone schedules (e.g., different pools)
                if any(
                    isinstance(v, dict) and "Lundi" in str(v)
                    for v in schedule_data.values()
                ):
                    # This is a multi-zone schedule
                    for zone, zone_schedule in schedule_data.items():
                        if isinstance(zone_schedule, dict):
                            osm_schedule = self.convert_weekly_schedule(zone_schedule)
                            if osm_schedule:
                                if condition:
                                    osm_parts.append(f'{osm_schedule} "{condition}"')
                                else:
                                    osm_parts.append(osm_schedule)
                else:
                    # Regular weekly schedule
                    osm_schedule = self.convert_weekly_schedule(schedule_data)
                    if osm_schedule:
                        if condition:
                            osm_parts.append(f'{osm_schedule} "{condition}"')
                        else:
                            osm_parts.append(osm_schedule)
                break  # Use first found schedule

        # Handle special days and holidays
        for special_key in ["jours_feries", "jours_speciaux", "horaires_speciaux"]:
            special_data = self.get_nested_value(data, special_key)
            if special_data:
                special_osm = self.convert_special_days(special_data)
                osm_parts.extend(special_osm)

        # Clean up and join
        result = "; ".join(filter(None, osm_parts))
        return result if result else "closed"

    def get_nested_value(self, data: Dict, path: str) -> Any:
        """Get value from nested dictionary using dot notation."""
        keys = path.split(".")
        current = data

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None

        return current

    def convert_file(self, input_file: str, output_file: str = None) -> Dict:
        """Convert entire JSON file to OSM format."""
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        results = {}

        if isinstance(data, list):
            for i, item in enumerate(data):
                identifier = item.get("identifiant", item.get("nom", f"item_{i}"))
                osm_hours = self.convert_to_osm(item)
                results[identifier] = {
                    "original_data": item,
                    "osm_opening_hours": osm_hours,
                }
        else:
            osm_hours = self.convert_to_osm(data)
            results["single_item"] = {
                "original_data": data,
                "osm_opening_hours": osm_hours,
            }

        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

        return results


def main():
    """Example usage of the OSM converter."""
    converter = OSMConverter()

    # Connect to SQLite database
    db_path = r"c:\Users\beranger\Documents\GitHub\smart_watch\data\alerte_modif_horaire_lieu_short.db"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Read all records with horaires_llm column
        cursor.execute(
            "SELECT identifiant, nom, url, horaires_llm FROM alerte_modif_horaire_lieu_short WHERE horaires_llm IS NOT NULL"
        )
        records = cursor.fetchall()

        print("=== OSM CONVERSION RESULTS ===")

        for record in records:
            item_id, nom, url, horaires_llm = record

            try:
                # Parse the JSON string from horaires_llm column
                horaires_data = json.loads(horaires_llm)

                # Convert to OSM format
                osm_hours = converter.convert_to_osm(horaires_data)

                print(f"\nID: {item_id}")
                print(f"Nom: {nom}")
                print(f"URL: {url}")
                print(f"OSM: {osm_hours}")
                print("-" * 50)

            except json.JSONDecodeError as e:
                print(f"\nID: {item_id} - Error parsing JSON: {e}")
            except Exception as e:
                print(f"\nID: {item_id} - Error converting: {e}")

        conn.close()

    except sqlite3.Error as e:
        print(f"Database error: {e}")


if __name__ == "__main__":
    main()
