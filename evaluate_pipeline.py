# Ce script permet de lancer une évaluation complète du pipeline SmartWatch.
# Il prend en entrée un fichier CSV contenant des URLs et les horaires de référence (ground truth)
# au format OSM, puis exécute le pipeline d'extraction pour chaque URL.
#
# Le script compare ensuite les horaires extraits par le pipeline avec les horaires de référence
# et génère un rapport de performance détaillé, incluant un taux de concordance (accuracy)
# et le détail des erreurs et des différences.
#
# Le module d'évaluation est conçu pour être cohérent avec le pipeline principal :
# - Il utilise les mêmes composants de traitement (MarkdownCleaner, LLMProcessor, etc.).
# - Il emploie le même mécanisme de comparaison d'horaires (HorairesComparator).
#
# Usage :
# python evaluate_pipeline.py chemin/vers/votre/fichier_evaluation.csv
#
# Le fichier CSV doit contenir au minimum les colonnes 'url' et 'ground_truth_osm'.

import argparse
import sys

# Ajouter le chemin du projet au sys.path pour permettre les imports relatifs
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.smart_watch.core.ConfigManager import ConfigManager
from src.smart_watch.core.Logger import create_logger
from src.smart_watch.evaluate.evaluator import Evaluator


def main():
    """
    Point d'entrée principal pour le script d'évaluation.
    Parse les arguments de la ligne de commande, initialise les composants
    et lance l'évaluation.
    """
    # --- Configuration de l'ArgParser ---
    parser = argparse.ArgumentParser(
        description="Script d'évaluation du pipeline SmartWatch."
    )
    parser.add_argument(
        "evaluation_file",
        type=str,
        help="Chemin vers le fichier CSV d'évaluation (contenant les colonnes 'url' et 'ground_truth_osm').",
    )
    args = parser.parse_args()

    # --- Initialisation ---
    # Initialiser le gestionnaire de configuration
    config = ConfigManager()
    if not config.validate():
        print(
            "Erreur : Configuration invalide. Vérifiez votre fichier .env et les modèles de configuration."
        )
        sys.exit(1)

    # Initialiser le logger principal pour le script d'évaluation
    logger = create_logger(module_name="EvaluationPipeline")
    logger.info("Initialisation du script d'évaluation.")

    # --- Exécution de l'évaluation ---
    # Instancier l'évaluateur avec la configuration et le logger
    evaluator = Evaluator(config, logger)

    # Lancer le processus d'évaluation sur le fichier fourni
    evaluator.run(args.evaluation_file)

    logger.info("Évaluation terminée.")


if __name__ == "__main__":
    main()
