import csv
from typing import List

import pandas as pd

from src.smart_watch.core.ConfigManager import ConfigManager
from src.smart_watch.core.Logger import SmartWatchLogger
from src.smart_watch.core.URLRetriever import retrieve_url
from src.smart_watch.data_models.schema_bdd import Lieux, ResultatsExtraction
from src.smart_watch.processing import (
    LLMProcessor,
    MarkdownProcessor,
)
from src.smart_watch.utils.MarkdownCleaner import MarkdownCleaner

from .metrics import EvaluationMetrics
from .scorer import Scorer, ScoreResult


# Définition des classes mock au niveau du module pour éviter les redéfinitions
class MockLieu(Lieux):
    """Classe mock pour Lieux."""

    def __init__(self, p_url):
        """Initialise MockLieu."""
        self.identifiant = "eval"
        self.nom = "Lieu d'évaluation"
        self.url = p_url
        self.type_lieu = "inconnu"


class MockResultForLLM(ResultatsExtraction):
    """Classe mock pour ResultatsExtraction."""

    def __init__(self, p_md_filtre, p_md_nettoye, p_md_brut):
        """Initialise MockResultForLLM."""
        self.markdown_filtre = p_md_filtre
        self.markdown_nettoye = p_md_nettoye
        self.markdown_brut = p_md_brut


class Evaluator:
    """Orchestre l'évaluation du pipeline sur un jeu de données."""

    def __init__(self, config: ConfigManager, logger: SmartWatchLogger) -> None:
        """
        Initialise l'évaluateur avec la configuration et le logger.

        Cette méthode configure tous les composants nécessaires pour effectuer
        l'évaluation du pipeline : nettoyeur de markdown, processeur de markdown,
        processeur LLM et scoreur.

        Args:
            config (ConfigManager): gestionnaire de configuration du système.
            logger (SmartWatchLogger): instance de logger pour la journalisation des événements.

        Attributes:
            config (ConfigManager): gestionnaire de configuration.
            logger (SmartWatchLogger): instance de logger.
            markdown_cleaner (MarkdownCleaner): nettoyeur de contenu markdown.
            markdown_processor (MarkdownProcessor): processeur de filtrage markdown.
            llm_processor (LLMProcessor): processeur d'extraction LLM.
            scorer (Scorer): scoreur pour comparer les résultats.
            results (List[ScoreResult]): liste des résultats de scoring.
        """
        self.config = config
        self.logger = logger
        # Initialiser les composants nécessaires
        self.markdown_cleaner = MarkdownCleaner(config, logger)
        self.markdown_processor = MarkdownProcessor(config, logger)
        self.llm_processor = LLMProcessor(config, logger)
        self.scorer = Scorer()
        self.results: List[ScoreResult] = []

    def _process_single_item(self, url: str, ground_truth_osm: str) -> ScoreResult:
        """Exécute le pipeline complet pour une seule URL et la score."""
        self.logger.info(f"Traitement de l'URL : {url}")

        # 1. Extraction URL -> Markdown brut
        # Utilisation directe de la fonction `retrieve_url` existante
        row_data = {"url": url, "identifiant": "evaluation"}
        url_result = retrieve_url(
            row_data,
            sortie="markdown",
            encoding_errors="ignore",
            config=self.config,
            index=1,
            total=1,
        )
        if not url_result or url_result.get("statut") != "ok":
            self.logger.error(
                "Échec de la récupération de l'URL. Score de 0 pour cet item."
            )
            return self.scorer.score("", ground_truth_osm, url)

        # 2. Nettoyage Markdown
        # Utilisation de la méthode `clean_markdown_content` existante
        markdown_brut = url_result.get("markdown", "")
        cleaned_markdown = self.markdown_cleaner.clean_markdown_content(markdown_brut)

        # 3. Filtrage Markdown
        # Utilisation de la méthode `filter_markdown` existante
        self.logger.info(f"Démarrage du filtrage par embedding pour l'URL : {url}")
        filtered_markdown, co2_emissions = self.markdown_processor.filter_markdown(
            cleaned_markdown
        )
        self.logger.info(f"Filtrage terminé - Émissions CO2 : {co2_emissions:.6f} kg")
        if not filtered_markdown.strip():
            self.logger.warning(
                "Aucune section pertinente trouvée après filtrage par embedding"
            )
        else:
            self.logger.info(
                f"Contenu filtré : {len(filtered_markdown)} caractères conservés sur {len(cleaned_markdown)}"
            )

        # 4. Extraction LLM
        # Instancier les classes mock (définies au niveau du module)
        mock_lieu = MockLieu(url)
        mock_result = MockResultForLLM(
            filtered_markdown, cleaned_markdown, markdown_brut
        )

        # Utilisation de la méthode interne _process_single_llm
        llm_output = self.llm_processor._process_single_llm(mock_result, mock_lieu)
        predicted_osm = llm_output.get("llm_horaires_osm", "")

        if "Erreur" in predicted_osm:
            self.logger.warning(f"Erreur LLM détectée : {predicted_osm}")
            predicted_osm = ""

        # 5. Scoring
        score = self.scorer.score(predicted_osm, ground_truth_osm, url)
        self.logger.info(f"Résultat du score : {score}")
        self.logger.info(f"  - Prédit : {predicted_osm}")
        self.logger.info(f"  - Attendu: {ground_truth_osm}")

        return score

    def run(self, evaluation_file: str) -> None:
        """Lance l'évaluation sur l'ensemble du fichier."""
        self.logger.section("DÉBUT DE L'ÉVALUATION DU PIPELINE")
        try:
            eval_df = pd.read_csv(evaluation_file, sep=";", quoting=csv.QUOTE_ALL)
        except FileNotFoundError:
            self.logger.critical(f"Fichier d'évaluation non trouvé : {evaluation_file}")
            return

        for _, row in eval_df.iterrows():
            result = self._process_single_item(row["url"], row["ground_truth_osm"])
            self.results.append(result)

        # Calcul et affichage des métriques finales
        metrics = EvaluationMetrics(self.results)
        metrics.display()
        self.logger.section("FIN DE L'ÉVALUATION")
