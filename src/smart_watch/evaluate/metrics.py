from collections import Counter
from typing import List

from .scorer import ComparisonStatus, ScoreResult


class EvaluationMetrics:
    """Calcule et affiche les métriques d'évaluation à partir d'une liste de scores."""

    def __init__(self, results: List[ScoreResult]) -> None:
        """
        Initialise les métriques d'évaluation avec une liste de résultats.
        """
        self.results = results
        self.total_items = len(results)
        self.counts = Counter(r.status for r in results)
        self.diff_counts = [
            r.diff_count for r in results if r.status == ComparisonStatus.DIFFERENT
        ]

    def calculate_metrics(self) -> dict:
        """Calcule un ensemble de métriques de performance."""
        identical_count = self.counts[ComparisonStatus.IDENTICAL]
        accuracy = identical_count / self.total_items if self.total_items > 0 else 0

        total_differences = sum(self.diff_counts)
        average_differences = (
            total_differences / len(self.diff_counts) if self.diff_counts else 0
        )
        difference_distribution = Counter(self.diff_counts)

        return {
            "accuracy": accuracy,
            "total_differences": total_differences,
            "average_differences": average_differences,
            "difference_distribution": difference_distribution,
        }

    def display(self) -> None:
        """Affiche un rapport complet des métriques."""
        metrics = self.calculate_metrics()
        identical_count = self.counts[ComparisonStatus.IDENTICAL]
        different_count = self.counts[ComparisonStatus.DIFFERENT]
        error_count = self.counts[ComparisonStatus.ERROR]

        print("\n--- RAPPORT D'ÉVALUATION DU PIPELINE ---")
        print("=" * 40)

        print("\n[Résultats Sommaires]")
        print(f"  - Items évalués    : {self.total_items}")
        print(f"  - Identiques       : {identical_count}")
        print(f"  - Différents       : {different_count}")
        print(f"  - Erreurs          : {error_count}")

        print("\n[Métriques de Performance]")
        print(f"  - Taux de Concordance Parfaite   : {metrics['accuracy']:.2%}")
        if different_count > 0:
            print(
                f"  - Total des différences atomiques: {metrics['total_differences']}"
            )
            print(
                f"  - Moyenne de différences par item: {metrics['average_differences']:.2f}"
            )

        print("=" * 40)

        if different_count > 0:
            print("\n[Analyse des Différences]")
            dist = metrics["difference_distribution"]
            for count, num_items in sorted(dist.items()):
                plural = "s" if num_items > 1 else ""
                print(f"  - {num_items} item{plural} avec {count} différence(s)")

        # Afficher les détails des erreurs et différences
        if different_count > 0:
            print("\n[Détail des Différences]")
            for res in self.results:
                if res.status == ComparisonStatus.DIFFERENT:
                    print(f"  ({res.diff_count} différence(s)) - URL: {res.url}")
                    print(f"    - Attendu: {res.ground_truth_osm}")
                    print(f"    - Prédit : {res.predicted_osm}")
                    print(f"    - Détail : {res.differences}\n")

        if error_count > 0:
            print("\n[Détail des Erreurs]")
            for res in self.results:
                if res.status == ComparisonStatus.ERROR:
                    print(f"  - Attendu: {res.ground_truth_osm}")
                    print(f"    Prédit : {res.predicted_osm}")
                    print(f"    Raison : {res.differences}\n")
