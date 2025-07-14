"""
Système de statistiques unifié pour le projet smart_watch.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class BaseStats(ABC):
    """Classe de base pour toutes les statistiques."""

    processed: int = 0
    successful: int = 0
    errors: int = 0

    @property
    def success_rate(self) -> float:
        """Calcule le taux de succès."""
        if self.processed == 0:
            return 0.0
        return (self.successful / self.processed) * 100

    @property
    def error_rate(self) -> float:
        """Calcule le taux d'erreur."""
        if self.processed == 0:
            return 0.0
        return (self.errors / self.processed) * 100

    @abstractmethod
    def get_summary(self) -> Dict[str, Any]:
        """Retourne un résumé des statistiques."""
        pass

    def merge(self, other: "BaseStats") -> None:
        """Fusionne avec d'autres statistiques du même type."""
        self.processed += other.processed
        self.successful += other.successful
        self.errors += other.errors

    def __str__(self) -> str:
        return f"{self.successful}/{self.processed} ({self.success_rate:.1f}%)"
