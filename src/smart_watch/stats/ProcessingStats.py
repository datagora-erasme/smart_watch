"""
Statistiques spécialisées pour chaque type de traitement.
"""

from dataclasses import dataclass
from typing import Any, Dict

from .BaseStats import BaseStats


@dataclass
class URLProcessingStats(BaseStats):
    """Statistiques pour le traitement des URLs."""

    markdown_extracted: int = 0
    http_errors: int = 0
    timeout_errors: int = 0

    def get_summary(self) -> Dict[str, Any]:
        return {
            "urls_processed": self.processed,
            "urls_successful": self.successful,
            "urls_errors": self.errors,
            "markdown_extracted": self.markdown_extracted,
            "http_errors": self.http_errors,
            "timeout_errors": self.timeout_errors,
            "success_rate": f"{self.success_rate:.1f}%",
        }


@dataclass
class MarkdownProcessingStats(BaseStats):
    """Statistiques pour le traitement du markdown."""

    chars_cleaned: int = 0
    sections_filtered: int = 0
    embedding_calls: int = 0
    co2_emissions: float = 0.0

    def get_summary(self) -> Dict[str, Any]:
        return {
            "markdown_processed": self.processed,
            "markdown_successful": self.successful,
            "markdown_errors": self.errors,
            "chars_cleaned": self.chars_cleaned,
            "sections_filtered": self.sections_filtered,
            "embedding_calls": self.embedding_calls,
            "co2_emissions": f"{self.co2_emissions:.4f}g",
            "success_rate": f"{self.success_rate:.1f}%",
        }


@dataclass
class LLMProcessingStats(BaseStats):
    """Statistiques pour le traitement LLM."""

    json_extractions: int = 0
    osm_conversions: int = 0
    co2_emissions: float = 0.0
    total_tokens: int = 0

    def get_summary(self) -> Dict[str, Any]:
        return {
            "llm_processed": self.processed,
            "llm_successful": self.successful,
            "llm_errors": self.errors,
            "json_extractions": self.json_extractions,
            "osm_conversions": self.osm_conversions,
            "co2_emissions": f"{self.co2_emissions:.4f}g",
            "total_tokens": self.total_tokens,
            "success_rate": f"{self.success_rate:.1f}%",
        }


@dataclass
class ComparisonProcessingStats(BaseStats):
    """Statistiques pour les comparaisons."""

    identical_schedules: int = 0
    different_schedules: int = 0
    comparison_errors: int = 0

    def get_summary(self) -> Dict[str, Any]:
        return {
            "comparisons_processed": self.processed,
            "comparisons_successful": self.successful,
            "comparisons_errors": self.errors,
            "identical_schedules": self.identical_schedules,
            "different_schedules": self.different_schedules,
            "comparison_errors": self.comparison_errors,
            "success_rate": f"{self.success_rate:.1f}%",
        }
