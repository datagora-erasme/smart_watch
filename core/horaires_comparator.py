"""
Comparateur universel d'horaires d'ouverture.
Peut comparer OSM vs OSM, OSM vs JSON, JSON vs JSON, etc.
"""

import json
from enum import Enum
from typing import Dict, List, Tuple, Union

from assets.model import Horaires
from utils.CustomJsonToOSM import OSMConverter
from utils.OSMToCustomJson import OSMToCustomJsonConverter


class HoraireFormat(Enum):
    """Types de formats d'horaires supportés."""

    OSM = "osm"
    JSON_CUSTOM = "json_custom"
    JSON_STRING = "json_string"
    PYDANTIC = "pydantic"


class ComparisonResult:
    """Résultat d'une comparaison d'horaires."""

    def __init__(self):
        self.identical = False
        self.differences = []
        self.similarity_score = 0.0
        self.errors = []

    def add_difference(self, category: str, description: str, details: Dict = None):
        """Ajoute une différence trouvée."""
        self.differences.append(
            {"category": category, "description": description, "details": details or {}}
        )

    def add_error(self, error: str):
        """Ajoute une erreur rencontrée."""
        self.errors.append(error)

    def calculate_similarity(self):
        """Calcule un score de similarité basé sur les différences."""
        if self.errors:
            self.similarity_score = 0.0
        elif not self.differences:
            self.similarity_score = 1.0
        else:
            # Score basé sur le nombre et la gravité des différences
            major_differences = sum(
                1
                for d in self.differences
                if d["category"] in ["structure", "horaires"]
            )
            minor_differences = sum(
                1 for d in self.differences if d["category"] in ["metadata", "format"]
            )

            penalty = (major_differences * 0.3) + (minor_differences * 0.1)
            self.similarity_score = max(0.0, 1.0 - penalty)

        self.identical = self.similarity_score == 1.0

    def to_dict(self) -> Dict:
        """Convertit le résultat en dictionnaire."""
        return {
            "identical": self.identical,
            "similarity_score": self.similarity_score,
            "differences_count": len(self.differences),
            "differences": self.differences,
            "errors": self.errors,
        }


class HorairesComparator:
    """Comparateur universel d'horaires d'ouverture."""

    def __init__(self):
        """Initialise le comparateur avec les convertisseurs."""
        self.osm_converter = OSMConverter()
        self.json_converter = OSMToCustomJsonConverter()

    def detect_format(self, horaires: Union[str, Dict, Horaires]) -> HoraireFormat:
        """Détecte automatiquement le format des horaires."""
        if isinstance(horaires, Horaires):
            return HoraireFormat.PYDANTIC
        elif isinstance(horaires, str):
            # Tenter de détecter si c'est du JSON ou de l'OSM
            if horaires.strip().startswith("{"):
                try:
                    json.loads(horaires)
                    return HoraireFormat.JSON_STRING
                except json.JSONDecodeError:
                    return HoraireFormat.OSM
            else:
                return HoraireFormat.OSM
        elif isinstance(horaires, dict):
            # Vérifier si c'est notre format JSON personnalisé
            if "horaires_ouverture" in horaires:
                return HoraireFormat.JSON_CUSTOM
            else:
                return HoraireFormat.JSON_CUSTOM  # Assume custom format
        else:
            raise ValueError(f"Format non reconnu pour : {type(horaires)}")

    def normalize_to_json(
        self,
        horaires: Union[str, Dict, Horaires],
        horaires_format: HoraireFormat = None,
        default_metadata: Dict = None,
    ) -> Dict:
        """Normalise les horaires vers le format JSON personnalisé."""
        if horaires_format is None:
            horaires_format = self.detect_format(horaires)

        default_meta = default_metadata or {
            "identifiant": "TEMP_ID",
            "nom": "Lieu temporaire",
            "type_lieu": "autre",
            "url": "https://example.com",
        }

        try:
            if horaires_format == HoraireFormat.JSON_CUSTOM:
                return horaires if isinstance(horaires, dict) else json.loads(horaires)

            elif horaires_format == HoraireFormat.JSON_STRING:
                return json.loads(horaires)

            elif horaires_format == HoraireFormat.PYDANTIC:
                return horaires.dict()

            elif horaires_format == HoraireFormat.OSM:
                # Convertir OSM vers JSON
                converted = self.json_converter.convert_osm_to_custom_json(
                    osm_string=horaires, **default_meta
                )
                return converted.dict()

            else:
                raise ValueError(f"Format non supporté : {horaires_format}")

        except Exception as e:
            raise ValueError(f"Erreur de normalisation : {e}")

    def normalize_to_osm(
        self,
        horaires: Union[str, Dict, Horaires],
        horaires_format: HoraireFormat = None,
    ) -> str:
        """Normalise les horaires vers le format OSM."""
        if horaires_format is None:
            horaires_format = self.detect_format(horaires)

        try:
            if horaires_format == HoraireFormat.OSM:
                return horaires

            elif horaires_format in [
                HoraireFormat.JSON_CUSTOM,
                HoraireFormat.JSON_STRING,
            ]:
                json_data = (
                    horaires if isinstance(horaires, dict) else json.loads(horaires)
                )
                return self.osm_converter.convert_to_osm(json_data)

            elif horaires_format == HoraireFormat.PYDANTIC:
                return self.osm_converter.convert_to_osm(horaires.dict())

            else:
                raise ValueError(f"Format non supporté : {horaires_format}")

        except Exception as e:
            raise ValueError(f"Erreur de normalisation vers OSM : {e}")

    def compare_json_structures(self, json1: Dict, json2: Dict) -> ComparisonResult:
        """Compare deux structures JSON d'horaires."""
        result = ComparisonResult()

        try:
            # Comparer les métadonnées
            meta1 = json1.get("horaires_ouverture", {}).get("metadata", {})
            meta2 = json2.get("horaires_ouverture", {}).get("metadata", {})

            for key in ["nom", "type_lieu"]:
                if meta1.get(key) != meta2.get(key):
                    result.add_difference(
                        "metadata",
                        f"Métadonnée '{key}' différente",
                        {"value1": meta1.get(key), "value2": meta2.get(key)},
                    )

            # Comparer les périodes
            periodes1 = json1.get("horaires_ouverture", {}).get("periodes", {})
            periodes2 = json2.get("horaires_ouverture", {}).get("periodes", {})

            self._compare_periods(periodes1, periodes2, result)

        except Exception as e:
            result.add_error(f"Erreur lors de la comparaison JSON : {e}")

        result.calculate_similarity()
        return result

    def _compare_periods(
        self, periodes1: Dict, periodes2: Dict, result: ComparisonResult
    ):
        """Compare les périodes d'horaires."""
        all_periods = set(periodes1.keys()) | set(periodes2.keys())

        for period in all_periods:
            p1 = periodes1.get(period, {})
            p2 = periodes2.get(period, {})

            if not p1 and not p2:
                continue
            elif not p1 or not p2:
                result.add_difference(
                    "structure",
                    f"Période '{period}' présente dans un seul horaire",
                    {"present_in_1": bool(p1), "present_in_2": bool(p2)},
                )
                continue

            # Comparer source_found
            if p1.get("source_found") != p2.get("source_found"):
                result.add_difference(
                    "structure",
                    f"source_found différent pour '{period}'",
                    {
                        "value1": p1.get("source_found"),
                        "value2": p2.get("source_found"),
                    },
                )

            # Comparer les horaires hebdomadaires
            if period in [
                "hors_vacances_scolaires",
                "vacances_scolaires_ete",
                "petites_vacances_scolaires",
            ]:
                h1 = p1.get("horaires", {})
                h2 = p2.get("horaires", {})
                self._compare_weekly_schedules(h1, h2, period, result)

    def _compare_weekly_schedules(
        self,
        horaires1: Dict,
        horaires2: Dict,
        period_name: str,
        result: ComparisonResult,
    ):
        """Compare les horaires hebdomadaires."""
        all_days = set(horaires1.keys()) | set(horaires2.keys())

        for day in all_days:
            day1 = horaires1.get(day, {})
            day2 = horaires2.get(day, {})

            if not day1 and not day2:
                continue
            elif not day1 or not day2:
                result.add_difference(
                    "horaires",
                    f"Jour '{day}' présent dans un seul horaire ({period_name})",
                    {"day": day, "period": period_name},
                )
                continue

            # Comparer ouvert/fermé
            if day1.get("ouvert") != day2.get("ouvert"):
                result.add_difference(
                    "horaires",
                    f"Statut ouvert/fermé différent pour '{day}' ({period_name})",
                    {
                        "day": day,
                        "period": period_name,
                        "ouvert1": day1.get("ouvert"),
                        "ouvert2": day2.get("ouvert"),
                    },
                )

            # Comparer les créneaux
            creneaux1 = day1.get("creneaux", [])
            creneaux2 = day2.get("creneaux", [])

            if len(creneaux1) != len(creneaux2):
                result.add_difference(
                    "horaires",
                    f"Nombre de créneaux différent pour '{day}' ({period_name})",
                    {
                        "day": day,
                        "period": period_name,
                        "count1": len(creneaux1),
                        "count2": len(creneaux2),
                    },
                )
            else:
                # Comparer chaque créneau
                for i, (c1, c2) in enumerate(zip(creneaux1, creneaux2)):
                    if c1.get("debut") != c2.get("debut") or c1.get("fin") != c2.get(
                        "fin"
                    ):
                        result.add_difference(
                            "horaires",
                            f"Créneau {i + 1} différent pour '{day}' ({period_name})",
                            {
                                "day": day,
                                "period": period_name,
                                "creneau_index": i,
                                "creneau1": f"{c1.get('debut')}-{c1.get('fin')}",
                                "creneau2": f"{c2.get('debut')}-{c2.get('fin')}",
                            },
                        )

    def compare_osm_strings(self, osm1: str, osm2: str) -> ComparisonResult:
        """Compare deux chaînes OSM."""
        result = ComparisonResult()

        try:
            # Normalisation basique
            osm1_norm = osm1.strip().replace(" ", "").replace(";", "; ")
            osm2_norm = osm2.strip().replace(" ", "").replace(";", "; ")

            if osm1_norm == osm2_norm:
                result.identical = True
                result.similarity_score = 1.0
            else:
                # Analyser les différences
                result.add_difference(
                    "format", "Chaînes OSM différentes", {"osm1": osm1, "osm2": osm2}
                )

                # Calculer similarité basique
                common_chars = sum(1 for a, b in zip(osm1_norm, osm2_norm) if a == b)
                max_length = max(len(osm1_norm), len(osm2_norm))
                if max_length > 0:
                    result.similarity_score = common_chars / max_length
                else:
                    result.similarity_score = (
                        1.0 if osm1_norm == osm2_norm == "" else 0.0
                    )

        except Exception as e:
            result.add_error(f"Erreur lors de la comparaison OSM : {e}")
            result.similarity_score = 0.0

        return result

    def compare(
        self,
        horaires1: Union[str, Dict, Horaires],
        horaires2: Union[str, Dict, Horaires],
        format1: HoraireFormat = None,
        format2: HoraireFormat = None,
        comparison_format: str = "json",
    ) -> ComparisonResult:
        """
        Compare deux horaires, quel que soit leur format initial.

        Args:
            horaires1: Premier horaire à comparer
            horaires2: Deuxième horaire à comparer
            format1: Format du premier horaire (détecté auto si None)
            format2: Format du deuxième horaire (détecté auto si None)
            comparison_format: Format pour la comparaison ("json" ou "osm")

        Returns:
            ComparisonResult: Résultat de la comparaison
        """
        result = ComparisonResult()

        try:
            # Détecter les formats si non spécifiés
            if format1 is None:
                format1 = self.detect_format(horaires1)
            if format2 is None:
                format2 = self.detect_format(horaires2)

            if comparison_format == "osm":
                # Normaliser vers OSM et comparer
                osm1 = self.normalize_to_osm(horaires1, format1)
                osm2 = self.normalize_to_osm(horaires2, format2)
                result = self.compare_osm_strings(osm1, osm2)

            elif comparison_format == "json":
                # Normaliser vers JSON et comparer
                default_meta = {
                    "identifiant": "COMPARE_ID",
                    "nom": "Comparaison",
                    "type_lieu": "comparaison",
                    "url": "https://comparison.example.com",
                }

                json1 = self.normalize_to_json(horaires1, format1, default_meta)
                json2 = self.normalize_to_json(horaires2, format2, default_meta)
                result = self.compare_json_structures(json1, json2)

            else:
                raise ValueError(
                    f"Format de comparaison non supporté : {comparison_format}"
                )

        except Exception as e:
            result.add_error(f"Erreur générale de comparaison : {e}")
            result.similarity_score = 0.0

        return result

    def batch_compare(
        self,
        horaires_list: List[Tuple[Union[str, Dict, Horaires], str]],
        comparison_format: str = "json",
    ) -> Dict[str, ComparisonResult]:
        """
        Compare plusieurs horaires entre eux.

        Args:
            horaires_list: Liste de tuples (horaires, identifiant)
            comparison_format: Format pour la comparaison

        Returns:
            Dict: Résultats de comparaison avec clés "id1_vs_id2"
        """
        results = {}

        for i in range(len(horaires_list)):
            for j in range(i + 1, len(horaires_list)):
                horaires1, id1 = horaires_list[i]
                horaires2, id2 = horaires_list[j]

                comparison_key = f"{id1}_vs_{id2}"
                results[comparison_key] = self.compare(
                    horaires1, horaires2, comparison_format=comparison_format
                )

        return results


def main():
    """Exemple d'utilisation du comparateur."""
    comparator = HorairesComparator()

    # Exemples de test
    osm1 = "Mo-Fr 09:00-17:00; Sa 09:00-12:00"
    osm2 = "Mo-Fr 09:00-17:00; Sa 09:00-13:00"  # Différence sur samedi

    json_example = {
        "horaires_ouverture": {
            "metadata": {
                "identifiant": "TEST001",
                "nom": "Mairie Test",
                "type_lieu": "mairie",
                "url": "https://example.com",
            },
            "periodes": {
                "hors_vacances_scolaires": {
                    "source_found": True,
                    "horaires": {
                        "lundi": {
                            "source_found": True,
                            "ouvert": True,
                            "creneaux": [{"debut": "09:00", "fin": "17:00"}],
                        }
                    },
                }
            },
            "extraction_info": {"source_found": True, "confidence": 1.0},
        }
    }

    print("=== TEST DU COMPARATEUR D'HORAIRES ===")

    # Test 1: OSM vs OSM
    print("\n--- Test 1: OSM vs OSM ---")
    result1 = comparator.compare(osm1, osm2, comparison_format="osm")
    print(f"Identiques: {result1.identical}")
    print(f"Score similarité: {result1.similarity_score:.2f}")
    print(f"Différences: {len(result1.differences)}")

    # Test 2: OSM vs JSON
    print("\n--- Test 2: OSM vs JSON ---")
    result2 = comparator.compare(osm1, json_example, comparison_format="json")
    print(f"Identiques: {result2.identical}")
    print(f"Score similarité: {result2.similarity_score:.2f}")
    print(f"Différences: {len(result2.differences)}")
    for diff in result2.differences:
        print(f"  - {diff['category']}: {diff['description']}")

    # Test 3: Comparaison identique
    print("\n--- Test 3: Comparaison identique ---")
    result3 = comparator.compare(osm1, osm1, comparison_format="osm")
    print(f"Identiques: {result3.identical}")
    print(f"Score similarité: {result3.similarity_score:.2f}")


if __name__ == "__main__":
    main()
