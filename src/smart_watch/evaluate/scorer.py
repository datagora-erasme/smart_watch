import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional

from ..core.ComparateurHoraires import HorairesComparator

# Importer la classe existante
from ..utils.OSMToCustomJson import OsmToJsonConverter


class ComparisonStatus(Enum):
    """Définit le statut d'une comparaison."""

    IDENTICAL = "Identique"
    DIFFERENT = "Différent"
    ERROR = "Erreur de comparaison"


@dataclass
class ScoreResult:
    """Structure pour stocker les résultats du scoring pour un item."""

    status: ComparisonStatus
    predicted_osm: str
    ground_truth_osm: str
    url: str = ""
    diff_count: int = 0
    differences: Optional[str] = None


class Scorer:
    """
    Compare une chaîne d'horaires prédite avec une vérité terrain en utilisant
    le ComparateurHoraires du projet.
    """

    def __init__(self) -> None:
        """
        Initialise le Scorer avec les outils de conversion et de comparaison.

        Cette méthode configure les instances nécessaires pour effectuer les comparaisons
        d'horaires : un convertisseur OSM vers JSON et un comparateur d'horaires.

        Attributes:
            converter (OsmToJsonConverter): instance pour convertir les chaînes OSM en JSON.
            comparator (HorairesComparator): instance pour comparer les horaires.
        """
        # Instancier les outils existants du projet
        self.converter = OsmToJsonConverter()
        self.comparator = HorairesComparator()

    def _count_atomic_differences(self, differences_str: Optional[str]) -> int:
        """
        Analyse une chaîne de différences pour compter les erreurs atomiques.

        Args:
            differences_str (Optional[str]): La chaîne de texte des différences.

        Returns:
            int: Le nombre de différences atomiques.
        """
        if not differences_str or "Aucune différence" in differences_str:
            return 0

        count = 0
        # Compte les changements de statut (ex: "ouvert → fermé")
        count += differences_str.count("→")

        # Compte les créneaux ajoutés ou supprimés
        # Chaque créneau est une différence atomique
        added_matches = re.findall(r"ajoutés: (.*?)(?: \||$)", differences_str)
        removed_matches = re.findall(r"supprimés: (.*?)(?: \||$)", differences_str)

        for match in added_matches + removed_matches:
            # Compte le nombre de créneaux dans la liste
            count += len(match.split(","))

        # Si aucun mot-clé n'est trouvé, mais la chaîne n'est pas vide,
        # on compte chaque ligne comme une différence.
        if count == 0 and differences_str:
            return len(differences_str.split("\n"))

        return count

    def _to_json(self, osm_string: str) -> Optional[Dict]:
        """Convertit une chaîne OSM en JSON, gère les erreurs."""
        try:
            if not osm_string or not isinstance(osm_string, str):
                return None
            # Utiliser la méthode de la classe pour la conversion
            return self.converter.convert_osm_string(osm_string)
        except Exception:
            # Si la conversion échoue, on retourne None
            return None

    def score(
        self, predicted_osm: str, ground_truth_osm: str, url: str = ""
    ) -> ScoreResult:
        """
        Compare la chaîne prédite à la vérité terrain et retourne le score.

        Args:
            predicted_osm (str): La chaîne d'horaires au format OSM générée.
            ground_truth_osm (str): La chaîne d'horaires de référence (vérité terrain).
            url (str): L'URL du lieu évalué.

        Returns:
            ScoreResult: Un objet contenant le statut de la comparaison.
        """
        predicted_json = self._to_json(predicted_osm)
        truth_json = self._to_json(ground_truth_osm)

        # Gérer les cas où la conversion a échoué ou les chaînes sont vides
        if not predicted_json or not truth_json:
            status = ComparisonStatus.ERROR
            diff_text = "Erreur de conversion OSM->JSON pour la chaîne prédite ou la vérité terrain."
            diff_count = 1
            if predicted_json == truth_json:  # Cas où les deux sont None/vides
                status = ComparisonStatus.IDENTICAL
                diff_text = ""
                diff_count = 0

            return ScoreResult(
                status=status,
                predicted_osm=predicted_osm,
                ground_truth_osm=ground_truth_osm,
                url=url,
                diff_count=diff_count,
                differences=diff_text,
            )

        try:
            # Utiliser le comparateur existant
            comparison_result = self.comparator.compare_schedules(
                truth_json, predicted_json
            )

            status = (
                ComparisonStatus.IDENTICAL
                if comparison_result.identical
                else ComparisonStatus.DIFFERENT
            )

            # Compter les différences atomiques à partir de la chaîne
            diff_count = self._count_atomic_differences(comparison_result.differences)

            return ScoreResult(
                status=status,
                predicted_osm=predicted_osm,
                ground_truth_osm=ground_truth_osm,
                url=url,
                diff_count=diff_count,
                differences=comparison_result.differences,
            )

        except Exception as e:
            return ScoreResult(
                status=ComparisonStatus.ERROR,
                predicted_osm=predicted_osm,
                ground_truth_osm=ground_truth_osm,
                url=url,
                diff_count=1,
                differences=f"Erreur inattendue du comparateur: {str(e)}",
            )
