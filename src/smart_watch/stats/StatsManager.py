"""
Gestionnaire global des statistiques du pipeline.
"""

from dataclasses import dataclass
from typing import Any, Dict

from .ProcessingStats import (
    ComparisonProcessingStats,
    LLMProcessingStats,
    MarkdownProcessingStats,
    URLProcessingStats,
)


@dataclass
class PipelineStats:
    """Statistiques globales du pipeline."""

    def __init__(self):
        self.url_stats = URLProcessingStats()
        self.markdown_stats = MarkdownProcessingStats()
        self.llm_stats = LLMProcessingStats()
        self.comparison_stats = ComparisonProcessingStats()

        # Statistiques globales
        self.total_processing_time: float = 0.0
        self.total_co2_emissions: float = 0.0
        self.pipeline_success: bool = False

    def get_global_summary(self) -> Dict[str, Any]:
        """Retourne un résumé global de toutes les statistiques."""
        return {
            "pipeline_success": self.pipeline_success,
            "total_processing_time": f"{self.total_processing_time:.2f}s",
            "total_co2_emissions": f"{self.total_co2_emissions:.4f}g",
            "url_processing": self.url_stats.get_summary(),
            "markdown_processing": self.markdown_stats.get_summary(),
            "llm_processing": self.llm_stats.get_summary(),
            "comparison_processing": self.comparison_stats.get_summary(),
        }

    def get_summary_for_report(self) -> Dict[str, Any]:
        """Retourne un résumé formaté pour le rapport."""
        return {
            "URLs traitées": str(self.url_stats),
            "Markdown traité": str(self.markdown_stats),
            "Extractions LLM": str(self.llm_stats),
            "Comparaisons": str(self.comparison_stats),
            "Temps total": f"{self.total_processing_time:.2f}s",
            "CO2 total": f"{self.total_co2_emissions:.4f}g",
        }

    def update_co2_emissions(self):
        """Met à jour les émissions CO2 totales."""
        self.total_co2_emissions = (
            self.markdown_stats.co2_emissions + self.llm_stats.co2_emissions
        )
