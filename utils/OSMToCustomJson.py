"""
Convertisseur du format OSM opening_hours vers le format JSON personnalisé.
Opération inverse de CustomJsonToOSM.
"""

import re
from typing import Dict, List, Optional

from assets.model import (
    CreneauHoraire,
    ExtractionInfo,
    Horaires,
    HorairesHebdomadaires,
    HorairesJour,
    HorairesOuverture,
    HorsVacancesScolaires,
    JoursFeries,
    JoursSpeciaux,
    Metadata,
    Periodes,
    PetitesVacancesScolaires,
    VacancesScolairesEte,
)


class OSMToCustomJsonConverter:
    """Convertisseur du format OSM opening_hours vers le format JSON personnalisé."""

    OSM_DAY_MAPPING = {
        "Mo": "lundi",
        "Tu": "mardi",
        "We": "mercredi",
        "Th": "jeudi",
        "Fr": "vendredi",
        "Sa": "samedi",
        "Su": "dimanche",
    }

    def __init__(self):
        """Initialise le convertisseur."""
        self.debug = False

    def parse_time_range(self, time_range: str) -> Optional[CreneauHoraire]:
        """Parse un créneau horaire du format OSM (HH:MM-HH:MM)."""
        pattern = r"(\d{1,2}:\d{2})-(\d{1,2}:\d{2})"
        match = re.match(pattern, time_range.strip())

        if match:
            debut, fin = match.groups()
            return CreneauHoraire(debut=debut, fin=fin)
        return None

    def parse_time_ranges(self, time_ranges: str) -> List[CreneauHoraire]:
        """Parse plusieurs créneaux séparés par des virgules."""
        if not time_ranges or time_ranges.strip() in ["off", "closed"]:
            return []

        creneaux = []
        for time_range in time_ranges.split(","):
            creneau = self.parse_time_range(time_range.strip())
            if creneau:
                creneaux.append(creneau)

        return creneaux

    def expand_day_range(self, day_range: str) -> List[str]:
        """Étend une plage de jours (Mo-Fr) en liste de jours individuels."""
        if "-" in day_range:
            start_day, end_day = day_range.split("-")
            day_order = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]

            try:
                start_idx = day_order.index(start_day)
                end_idx = day_order.index(end_day)

                if start_idx <= end_idx:
                    return day_order[start_idx : end_idx + 1]
                else:
                    # Gestion du cas Sa-Mo (weekend qui traverse la semaine)
                    return day_order[start_idx:] + day_order[: end_idx + 1]
            except ValueError:
                return [day_range]  # Si les jours ne sont pas reconnus
        else:
            return [day_range]

    def parse_day_specification(self, day_spec: str) -> List[str]:
        """Parse une spécification de jours (Mo,Tu-Fr,Sa)."""
        days = []
        for part in day_spec.split(","):
            days.extend(self.expand_day_range(part.strip()))
        return days

    def parse_osm_rule(self, osm_rule: str) -> Dict:
        """Parse une règle OSM individuelle."""
        osm_rule = osm_rule.strip()

        # Pattern pour une règle standard: jours + horaires
        pattern = r"^([A-Za-z,-]+)\s+(.+)$"
        match = re.match(pattern, osm_rule)

        if not match:
            return {}

        day_spec, time_spec = match.groups()

        # Vérifier si c'est fermé
        is_closed = time_spec.strip() in ["off", "closed"]

        # Parser les jours
        days = self.parse_day_specification(day_spec)

        # Parser les horaires
        if is_closed:
            creneaux = []
            ouvert = False
        else:
            creneaux = self.parse_time_ranges(time_spec)
            ouvert = len(creneaux) > 0

        return {"days": days, "ouvert": ouvert, "creneaux": creneaux}

    def parse_osm_string(self, osm_string: str) -> Dict:
        """Parse une chaîne OSM complète."""
        if not osm_string or osm_string.strip() in ["closed", ""]:
            return {}

        # Séparer les règles par ";"
        rules = [rule.strip() for rule in osm_string.split(";") if rule.strip()]

        parsed_rules = []
        for rule in rules:
            # Ignorer les conditions pour l'instant (SH, PH, etc.)
            if '"' in rule:
                # Retirer les conditions entre guillemets
                rule = re.sub(r'\s*"[^"]*"', "", rule).strip()

            parsed_rule = self.parse_osm_rule(rule)
            if parsed_rule:
                parsed_rules.append(parsed_rule)

        return {"rules": parsed_rules}

    def create_horaires_hebdomadaires(self, parsed_osm: Dict) -> HorairesHebdomadaires:
        """Crée un objet HorairesHebdomadaires à partir des règles OSM parsées."""
        # Initialiser tous les jours
        horaires_data = {}

        # Traiter chaque règle
        if "rules" in parsed_osm:
            for rule in parsed_osm["rules"]:
                for osm_day in rule["days"]:
                    french_day = self.OSM_DAY_MAPPING.get(osm_day)
                    if french_day:
                        horaires_data[french_day] = HorairesJour(
                            source_found=True,
                            ouvert=rule["ouvert"],
                            creneaux=rule["creneaux"],
                        )

        return HorairesHebdomadaires(**horaires_data)

    def convert_osm_to_custom_json(
        self,
        osm_string: str,
        identifiant: str,
        nom: str,
        type_lieu: str,
        url: str,
        timezone: str = "Europe/Paris",
    ) -> Horaires:
        """
        Convertit une chaîne OSM vers le format JSON personnalisé.

        Args:
            osm_string: Chaîne OSM opening_hours
            identifiant: Identifiant unique du lieu
            nom: Nom de l'établissement
            type_lieu: Type de lieu
            url: URL de la page
            timezone: Fuseau horaire

        Returns:
            Instance du modèle Horaires
        """
        # Parser la chaîne OSM
        parsed_osm = self.parse_osm_string(osm_string)

        # Créer les métadonnées
        metadata = Metadata(
            identifiant=identifiant,
            nom=nom,
            type_lieu=type_lieu,
            url=url,
            timezone=timezone,
        )

        # Créer les horaires hebdomadaires
        horaires_hebdo = self.create_horaires_hebdomadaires(parsed_osm)

        # Créer la période principale (hors vacances scolaires)
        hors_vacances = HorsVacancesScolaires(
            source_found=bool(parsed_osm.get("rules")), horaires=horaires_hebdo
        )

        # Créer les périodes
        periodes = Periodes(
            hors_vacances_scolaires=hors_vacances,
            vacances_scolaires_ete=VacancesScolairesEte(),
            petites_vacances_scolaires=PetitesVacancesScolaires(),
            jours_feries=JoursFeries(),
            jours_speciaux=JoursSpeciaux(),
        )

        # Créer les informations d'extraction
        extraction_info = ExtractionInfo(
            source_found=bool(parsed_osm.get("rules")),
            confidence=0.8,  # Confiance moyenne pour une conversion automatique
            notes="Converti depuis le format OSM opening_hours",
        )

        # Créer l'objet principal
        horaires_ouverture = HorairesOuverture(
            metadata=metadata, periodes=periodes, extraction_info=extraction_info
        )

        return Horaires(horaires_ouverture=horaires_ouverture)

    def convert_osm_file(self, input_file: str, output_file: str = None) -> Dict:
        """Convertit un fichier contenant des chaînes OSM."""
        results = {}

        # Ici, vous pourriez implémenter la lecture d'un fichier CSV ou JSON
        # contenant les données OSM et les métadonnées associées

        if output_file:
            import json

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

        return results

    def validate_osm_string(self, osm_string: str) -> bool:
        """Valide une chaîne OSM opening_hours basique."""
        if not osm_string or osm_string.strip() in ["closed", ""]:
            return True

        # Vérification basique des patterns
        basic_pattern = r"^[A-Za-z,-]+\s+(\d{1,2}:\d{2}-\d{1,2}:\d{2}(,\d{1,2}:\d{2}-\d{1,2}:\d{2})*|off|closed)"
        rules = [rule.strip() for rule in osm_string.split(";") if rule.strip()]

        for rule in rules:
            # Retirer les conditions entre guillemets pour la validation
            clean_rule = re.sub(r'\s*"[^"]*"', "", rule).strip()
            if not re.match(basic_pattern, clean_rule):
                return False

        return True


def main():
    """Exemple d'utilisation du convertisseur OSM vers JSON."""
    converter = OSMToCustomJsonConverter()

    # Test avec quelques exemples OSM
    test_cases = [
        {
            "osm": "Mo-Fr 09:00-17:00; Sa 09:00-12:00",
            "identifiant": "TEST001",
            "nom": "Mairie de Test",
            "type_lieu": "mairie",
            "url": "https://example.com",
        },
        {
            "osm": "Mo-We,Fr 08:30-12:00,13:00-17:00; Th 08:30-12:00; Sa 09:00-12:00; Su off",
            "identifiant": "TEST002",
            "nom": "Service Public Test",
            "type_lieu": "service_public",
            "url": "https://example2.com",
        },
        {
            "osm": "closed",
            "identifiant": "TEST003",
            "nom": "Lieu Fermé",
            "type_lieu": "autre",
            "url": "https://example3.com",
        },
    ]

    print("=== TEST DU CONVERTISSEUR OSM VERS JSON ===")

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test {i} ---")
        print(f"OSM: {test_case['osm']}")

        # Validation
        is_valid = converter.validate_osm_string(test_case["osm"])
        print(f"Valide: {is_valid}")

        if is_valid:
            # Conversion
            try:
                result = converter.convert_osm_to_custom_json(
                    osm_string=test_case["osm"],
                    identifiant=test_case["identifiant"],
                    nom=test_case["nom"],
                    type_lieu=test_case["type_lieu"],
                    url=test_case["url"],
                )

                print("Conversion réussie!")
                print("JSON généré:")
                import json

                print(json.dumps(result.dict(), indent=2, ensure_ascii=False))

            except Exception as e:
                print(f"Erreur lors de la conversion: {e}")

        print("-" * 50)


if __name__ == "__main__":
    main()
