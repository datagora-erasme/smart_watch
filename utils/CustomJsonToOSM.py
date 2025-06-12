# Script de conversion du format Json Custom, vers le format OSM standard

import json
import sqlite3
from typing import Dict, List, Optional


class OSMConverter:
    """Convertisseur du format JSON personnalisé des horaires vers la syntaxe OSM opening_hours."""

    DAY_MAPPING = {
        "lundi": "Mo",
        "mardi": "Tu",
        "mercredi": "We",
        "jeudi": "Th",
        "vendredi": "Fr",
        "samedi": "Sa",
        "dimanche": "Su",
    }

    def __init__(self):
        self.debug = False

    def normalize_day_name(self, day: str) -> Optional[str]:
        """Convertit un nom de jour en français vers le format OSM."""
        return self.DAY_MAPPING.get(day.lower())

    def format_time_range(self, debut: str, fin: str) -> str:
        """Formate un créneau horaire au format OSM."""
        return f"{debut}-{fin}"

    def parse_creneaux(self, creneaux: List[Dict]) -> str:
        """Parse une liste de créneaux horaires."""
        if not creneaux:
            return ""

        formatted_creneaux = []
        for creneau in creneaux:
            if isinstance(creneau, dict) and "debut" in creneau and "fin" in creneau:
                formatted_creneaux.append(
                    self.format_time_range(creneau["debut"], creneau["fin"])
                )

        return ",".join(formatted_creneaux)

    def process_horaires_jour(self, jour_data: Dict) -> Optional[str]:
        """Traite les horaires d'un jour selon le nouveau format."""
        if not isinstance(jour_data, dict):
            return None

        # Vérifier si le jour est actif
        if not jour_data.get("source_found", True):
            return None

        # Vérifier si le lieu est ouvert
        if not jour_data.get("ouvert", False):
            return None

        # Traiter les créneaux
        creneaux = jour_data.get("creneaux", [])
        if not creneaux:
            return None

        return self.parse_creneaux(creneaux)

    def group_consecutive_days(self, schedule: Dict[str, Optional[str]]) -> List[str]:
        """Regroupe les jours consécutifs ayant le même horaire."""
        if not schedule:
            return []

        # Ordre des jours pour le regroupement
        day_order = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]

        # Regrouper les jours par horaire
        schedule_groups = {}
        closed_days = []

        for day in day_order:
            if day in schedule:
                sched = schedule[day]
                if sched is None:
                    closed_days.append(day)
                else:
                    if sched not in schedule_groups:
                        schedule_groups[sched] = []
                    schedule_groups[sched].append(day)

        # Conversion au format OSM
        osm_parts = []

        # Traiter les jours fermés
        if closed_days:
            day_ranges = self.compress_day_ranges(closed_days)
            osm_parts.append(f"{day_ranges} off")

        # Traiter les jours ouverts
        for sched, days in schedule_groups.items():
            if sched:  # Ignorer les chaînes vides
                day_ranges = self.compress_day_ranges(days)
                osm_parts.append(f"{day_ranges} {sched}")

        return osm_parts

    def compress_day_ranges(self, days: List[str]) -> str:
        """Compresse les jours consécutifs en plages (Mo-Fr, Sa-Di, etc.)."""
        if not days:
            return ""

        day_order = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        day_indices = {day: i for i, day in enumerate(day_order)}

        # Trier les jours selon l'ordre
        days = sorted(days, key=lambda d: day_indices[d])

        ranges = []
        start = days[0]
        prev_idx = day_indices[start]

        for i in range(1, len(days)):
            curr_idx = day_indices[days[i]]
            if curr_idx != prev_idx + 1:
                # Rupture dans la séquence
                if start == days[i - 1]:
                    ranges.append(start)
                else:
                    ranges.append(f"{start}-{days[i - 1]}")
                start = days[i]
            prev_idx = curr_idx

        # Gérer la dernière plage
        if start == days[-1]:
            ranges.append(start)
        else:
            ranges.append(f"{start}-{days[-1]}")

        return ",".join(ranges)

    def convert_horaires_hebdomadaires(self, horaires: Dict) -> str:
        """Convertit un planning hebdomadaire au format OSM."""
        if not horaires:
            return ""

        normalized_schedule = {}
        jours_avec_source = 0

        for day_key, day_data in horaires.items():
            osm_day = self.normalize_day_name(day_key)
            if osm_day:
                # Vérifier d'abord si le jour a source_found = True
                if not day_data.get("source_found", True):
                    continue  # Ignorer ce jour complètement

                jours_avec_source += 1
                horaires_jour = self.process_horaires_jour(day_data)
                normalized_schedule[osm_day] = horaires_jour

        # Si aucun jour n'a de source trouvée, retourner vide
        if jours_avec_source == 0:
            return ""

        osm_parts = self.group_consecutive_days(normalized_schedule)
        return "; ".join(osm_parts)

    def process_jours_speciaux(self, jours_data: Dict) -> str:
        """Traite les jours spéciaux/fériés selon le nouveau format."""
        if not jours_data.get("source_found", False):
            return ""

        # Vérifier s'il y a des horaires spécifiques
        horaires_specifiques = jours_data.get("horaires_specifiques", {})
        if not horaires_specifiques:
            # Pas d'horaires spécifiques, utiliser le mode par défaut
            mode = jours_data.get("mode", "ferme")
            condition = jours_data.get("condition", "PH")

            if mode == "ferme":
                return f"{condition} off"
            elif mode == "ouvert":
                return f"{condition} open"
            else:
                return ""

        # Traiter chaque date spécifique
        osm_parts = []
        dates_avec_source = 0

        for date_desc, schedule in horaires_specifiques.items():
            # Vérifier source_found pour chaque date spécifique
            if isinstance(schedule, dict):
                if not schedule.get("source_found", True):
                    continue  # Ignorer cette date
                dates_avec_source += 1
            else:
                dates_avec_source += (
                    1  # Pour les chaînes, on considère qu'il y a une source
                )

            # Extraire la date du descriptif si possible
            date_osm = self.parse_date_to_osm(date_desc)

            if isinstance(schedule, dict):
                if schedule.get("ouvert", False):
                    # Jour ouvert avec horaires spécifiques
                    creneaux = schedule.get("creneaux", [])
                    if creneaux:
                        horaires_str = self.parse_creneaux(creneaux)
                        if date_osm:
                            osm_parts.append(f"{date_osm} {horaires_str}")
                        else:
                            # Fallback si on ne peut pas parser la date
                            osm_parts.append(f"PH {horaires_str}")
                    else:
                        if date_osm:
                            osm_parts.append(f"{date_osm} open")
                        else:
                            osm_parts.append("PH open")
                else:
                    # Jour fermé
                    if date_osm:
                        osm_parts.append(f"{date_osm} off")
                    else:
                        osm_parts.append("PH off")
            elif isinstance(schedule, str):
                if schedule.lower() in ["fermé", "ferme", "closed"]:
                    if date_osm:
                        osm_parts.append(f"{date_osm} off")
                    else:
                        osm_parts.append("PH off")
                else:
                    # Horaires sous forme de chaîne
                    if date_osm:
                        osm_parts.append(f"{date_osm} {schedule}")
                    else:
                        osm_parts.append(f"PH {schedule}")

        # Si aucune date n'a de source trouvée, ne pas retourner cette section
        if dates_avec_source == 0:
            return ""

        if osm_parts:
            return "; ".join(osm_parts)

        # Fallback sur le mode si défini
        mode = jours_data.get("mode", "ferme")
        condition = jours_data.get("condition", "PH")
        if mode == "ferme":
            return f"{condition} off"
        elif mode == "ouvert":
            return f"{condition} open"

        return ""

    def parse_date_to_osm(self, date_desc: str) -> Optional[str]:
        """Parse une description de date en format OSM."""
        import re

        # Mapping des mois français vers numéros
        mois_mapping = {
            "janvier": "01",
            "jan": "01",
            "février": "02",
            "fév": "02",
            "fevrier": "02",
            "fev": "02",
            "mars": "03",
            "mar": "03",
            "avril": "04",
            "avr": "04",
            "mai": "05",
            "juin": "06",
            "juillet": "07",
            "juil": "07",
            "août": "08",
            "aout": "08",
            "septembre": "09",
            "sep": "09",
            "sept": "09",
            "octobre": "10",
            "oct": "10",
            "novembre": "11",
            "nov": "11",
            "décembre": "12",
            "déc": "12",
            "decembre": "12",
            "dec": "12",
        }

        # Pattern pour "jour DD mois YYYY"
        pattern = r"(\w+)\s+(\d{1,2})\s+(\w+)\s+(\d{4})"
        match = re.search(pattern, date_desc.lower())

        if match:
            jour_semaine, jour, mois_nom, annee = match.groups()
            mois_num = mois_mapping.get(mois_nom)

            if mois_num:
                # Format OSM pour une date spécifique: YYYY mmm dd
                return f"{annee} {mois_nom.capitalize()[:3]} {int(jour):02d}"

        # Pattern pour "DD/MM/YYYY"
        pattern_numeric = r"(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})"
        match_numeric = re.search(pattern_numeric, date_desc)

        if match_numeric:
            jour, mois, annee = match_numeric.groups()
            mois_names = [
                "",
                "Jan",
                "Feb",
                "Mar",
                "Apr",
                "May",
                "Jun",
                "Jul",
                "Aug",
                "Sep",
                "Oct",
                "Nov",
                "Dec",
            ]
            if 1 <= int(mois) <= 12:
                return f"{annee} {mois_names[int(mois)]} {int(jour):02d}"

        # Si on ne peut pas parser, retourner None pour utiliser le fallback
        return None

    def has_valid_source_in_period(self, period_data: Dict) -> bool:
        """Vérifie si une période a au moins une source valide."""
        if not isinstance(period_data, dict):
            return False

        # Vérifier le source_found de la période elle-même
        if not period_data.get("source_found", False):
            return False

        # Pour les périodes avec horaires hebdomadaires
        if "horaires" in period_data:
            horaires = period_data["horaires"]
            if isinstance(horaires, dict):
                for day_data in horaires.values():
                    if isinstance(day_data, dict) and day_data.get(
                        "source_found", True
                    ):
                        return True
                return False  # Aucun jour n'a source_found = True

        # Pour les périodes avec horaires spécifiques
        if "horaires_specifiques" in period_data:
            horaires_specifiques = period_data["horaires_specifiques"]
            if isinstance(horaires_specifiques, dict):
                for schedule in horaires_specifiques.values():
                    if isinstance(schedule, dict):
                        if schedule.get("source_found", True):
                            return True
                    else:
                        return (
                            True  # Pour les chaînes, on considère qu'il y a une source
                        )
                return False  # Aucune date spécifique n'a source_found = True

        return True  # Par défaut, si pas d'horaires spécifiés

    def convert_to_osm_by_periods(self, data: Dict) -> Dict[str, str]:
        """Convertit les données d'horaires au format OSM en séparant par période."""
        result = {}

        # Vérifier si c'est le nouveau format de schéma
        if "horaires_ouverture" not in data:
            return {"error": "Format JSON non reconnu - 'horaires_ouverture' manquant"}

        horaires_data = data["horaires_ouverture"]
        periodes = horaires_data.get("periodes", {})

        # Traiter chaque période
        for period_key, period_data in periodes.items():
            if not isinstance(period_data, dict):
                continue

            # Vérifier si la période a au moins une source valide
            if not self.has_valid_source_in_period(period_data):
                continue

            if period_key in [
                "hors_vacances_scolaires",
                "vacances_scolaires_ete",
                "petites_vacances_scolaires",
            ]:
                # Traiter les horaires hebdomadaires
                horaires = period_data.get("horaires", {})
                if horaires:
                    osm_schedule = self.convert_horaires_hebdomadaires(horaires)
                    if osm_schedule:  # Seulement si on a des horaires valides
                        result[period_key] = osm_schedule

            elif period_key in ["jours_feries", "jours_speciaux"]:
                # Traiter les jours spéciaux
                osm_special = self.process_jours_speciaux(period_data)
                if osm_special:  # Seulement si on a des horaires valides
                    result[period_key] = osm_special

        return result

    def convert_to_osm(self, data: Dict) -> str:
        """Convertit toutes les données d'horaires au format OSM opening_hours (méthode principale)."""
        # Utiliser la nouvelle méthode par périodes
        periods_result = self.convert_to_osm_by_periods(data)

        if not periods_result:
            return "closed"

        # Assembler toutes les périodes en une seule chaîne OSM
        osm_parts = []

        # Ordre de priorité pour l'assemblage
        period_order = [
            "hors_vacances_scolaires",
            "petites_vacances_scolaires",
            "vacances_scolaires_ete",
            "jours_feries",
            "jours_speciaux",
        ]

        for period in period_order:
            if period in periods_result:
                osm_part = periods_result[period]
                if period == "hors_vacances_scolaires":
                    # Horaires normaux sans condition
                    osm_parts.append(osm_part)
                elif period in [
                    "vacances_scolaires_ete",
                    "petites_vacances_scolaires",
                ]:
                    # Ajouter condition de vacances scolaires
                    osm_parts.append(f'{osm_part} "SH"')
                else:
                    # Jours fériés et spéciaux (déjà formatés avec condition)
                    osm_parts.append(osm_part)

        result = "; ".join(osm_parts)
        return result if result else "closed"

    def convert_file(self, input_file: str, output_file: str = None) -> Dict:
        """Convertit un fichier JSON entier au format OSM."""
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        results = {}

        if isinstance(data, list):
            for i, item in enumerate(data):
                # Extraire l'identifiant depuis les métadonnées
                metadata = item.get("horaires_ouverture", {}).get("metadata", {})
                identifier = metadata.get("identifiant", f"item_{i}")

                osm_periods = self.convert_to_osm_by_periods(item)
                osm_combined = self.convert_to_osm(item)

                results[identifier] = {
                    "original_data": item,
                    "osm_periods": osm_periods,
                    "osm_combined": osm_combined,
                }
        else:
            metadata = data.get("horaires_ouverture", {}).get("metadata", {})
            identifier = metadata.get("identifiant", "single_item")

            osm_periods = self.convert_to_osm_by_periods(data)
            osm_combined = self.convert_to_osm(data)

            results[identifier] = {
                "original_data": data,
                "osm_periods": osm_periods,
                "osm_combined": osm_combined,
            }

        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

        return results


def main():
    """Exemple d'utilisation du convertisseur OSM."""
    converter = OSMConverter()

    # Test avec l'exemple fourni
    test_data = {
        "horaires_ouverture": {
            "metadata": {
                "identifiant": "S3858",
                "nom": "Piscine municipale",
                "type_lieu": "piscine",
                "url": "http://www.oullins.fr/sorties-activites/sports-et-loisirs/piscine-municipale-358.html",
            },
            "periodes": {
                "hors_vacances_scolaires": {
                    "source_found": True,
                    "horaires": {
                        "lundi": {
                            "source_found": True,
                            "ouvert": True,
                            "creneaux": [{"debut": "12:00", "fin": "13:45"}],
                        },
                        "mardi": {
                            "source_found": True,
                            "ouvert": True,
                            "creneaux": [{"debut": "12:00", "fin": "13:45"}],
                        },
                        "mercredi": {
                            "source_found": True,
                            "ouvert": True,
                            "creneaux": [{"debut": "17:00", "fin": "19:30"}],
                        },
                        "jeudi": {
                            "source_found": True,
                            "ouvert": True,
                            "creneaux": [{"debut": "12:00", "fin": "13:45"}],
                        },
                        "vendredi": {
                            "source_found": True,
                            "ouvert": True,
                            "creneaux": [
                                {"debut": "12:00", "fin": "13:45"},
                                {"debut": "17:00", "fin": "19:30"},
                            ],
                        },
                        "samedi": {
                            "source_found": True,
                            "ouvert": True,
                            "creneaux": [
                                {"debut": "10:00", "fin": "12:00"},
                                {"debut": "14:00", "fin": "18:00"},
                            ],
                        },
                        "dimanche": {
                            "source_found": True,
                            "ouvert": True,
                            "creneaux": [{"debut": "8:30", "fin": "12:30"}],
                        },
                    },
                    "condition": "De mi-septembre à début juin",
                },
                "petites_vacances_scolaires": {
                    "source_found": True,
                    "horaires": {
                        "lundi": {
                            "source_found": True,
                            "ouvert": True,
                            "creneaux": [
                                {"debut": "11:30", "fin": "14:00"},
                                {"debut": "16:30", "fin": "19:00"},
                            ],
                        },
                        "mardi": {
                            "source_found": True,
                            "ouvert": True,
                            "creneaux": [
                                {"debut": "11:30", "fin": "14:00"},
                                {"debut": "16:30", "fin": "19:00"},
                            ],
                        },
                        "mercredi": {
                            "source_found": True,
                            "ouvert": True,
                            "creneaux": [
                                {"debut": "11:30", "fin": "14:00"},
                                {"debut": "16:30", "fin": "19:30"},
                            ],
                        },
                        "jeudi": {
                            "source_found": True,
                            "ouvert": True,
                            "creneaux": [
                                {"debut": "11:30", "fin": "14:00"},
                                {"debut": "16:30", "fin": "19:00"},
                            ],
                        },
                        "vendredi": {
                            "source_found": True,
                            "ouvert": True,
                            "creneaux": [
                                {"debut": "11:30", "fin": "14:00"},
                                {"debut": "16:30", "fin": "19:30"},
                            ],
                        },
                        "samedi": {
                            "source_found": True,
                            "ouvert": True,
                            "creneaux": [{"debut": "10:00", "fin": "18:00"}],
                        },
                        "dimanche": {
                            "source_found": True,
                            "ouvert": True,
                            "creneaux": [{"debut": "8:30", "fin": "12:00"}],
                        },
                    },
                },
                "jours_feries": {
                    "source_found": True,
                    "horaires_specifiques": {
                        "lundi 21 avril 2025": {"ouvert": False},
                        "jeudi 1 mai 2025": {"ouvert": False},
                        "jeudi 8 mai 2025": {"ouvert": False},
                        "jeudi 29 mai 2025": {"ouvert": False},
                    },
                },
                "jours_speciaux": {
                    "source_found": True,
                    "horaires_specifiques": {
                        "vendredi 2 mai 2025": {
                            "creneaux": [
                                {"debut": "11:30", "fin": "14:00"},
                                {"debut": "16:30", "fin": "19:30"},
                            ]
                        },
                        "vendredi 30 mai 2025": {
                            "creneaux": [
                                {"debut": "11:30", "fin": "14:00"},
                                {"debut": "16:30", "fin": "19:30"},
                            ]
                        },
                    },
                },
            },
            "extraction_info": {"source_found": True, "confidence": 1},
        }
    }

    print("=== TEST DU CONVERTISSEUR OSM ===")

    # Test de conversion par périodes
    periods_result = converter.convert_to_osm_by_periods(test_data)
    print("\nRésultat par périodes:")
    for period, osm_format in periods_result.items():
        print(f"  {period}: {osm_format}")

    # Test de conversion combinée
    combined_result = converter.convert_to_osm(test_data)
    print(f"\nRésultat combiné OSM: {combined_result}")

    # Test avec base de données
    db_path = r"c:\Users\beranger\Documents\GitHub\smart_watch\data\alerte_modif_horaire_lieu_unique_devstral.db"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Lire tous les enregistrements avec la colonne horaires_llm
        cursor.execute(
            "SELECT identifiant, nom, url, horaires_llm FROM alerte_modif_horaire_lieu_unique WHERE horaires_llm IS NOT NULL LIMIT 5"
        )
        records = cursor.fetchall()

        print("\n=== RÉSULTATS DE LA CONVERSION OSM DEPUIS LA DB ===")

        for record in records:
            item_id, nom, url, horaires_llm = record

            try:
                # Analyser la chaîne JSON de la colonne horaires_llm
                horaires_data = json.loads(horaires_llm)

                # Conversion au format OSM
                osm_combined = converter.convert_to_osm(horaires_data)
                osm_periods = converter.convert_to_osm_by_periods(horaires_data)

                print(f"\nID : {item_id}")
                print(f"Nom : {nom}")
                print(f"OSM combiné : {osm_combined}")

                if osm_periods:
                    print("Périodes détaillées :")
                    for period, osm_format in osm_periods.items():
                        print(f"  {period}: {osm_format}")

                print("-" * 50)

            except json.JSONDecodeError as e:
                print(f"\nID : {item_id} - Erreur lors de l'analyse du JSON : {e}")
            except Exception as e:
                print(f"\nID : {item_id} - Erreur lors de la conversion : {e}")

        conn.close()

    except sqlite3.Error as e:
        print(f"Erreur de base de données : {e}")
    except FileNotFoundError:
        print(f"Fichier de base de données non trouvé : {db_path}")


if __name__ == "__main__":
    main()
