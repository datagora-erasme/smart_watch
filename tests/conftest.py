"""Configuration pour les tests pytest."""

import os
import sys

# Ajouter le répertoire src au chemin Python pour les tests
src_path = os.path.join(os.path.dirname(__file__), "..", "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Ajouter aussi le répertoire racine du projet
project_root = os.path.join(os.path.dirname(__file__), "..")
if project_root not in sys.path:
    sys.path.insert(0, project_root)


# Gestion des imports circulaires
def safe_import(module_name):
    """Import sécurisé pour éviter les imports circulaires."""
    try:
        return __import__(module_name)
    except ImportError as e:
        if "circular import" in str(e).lower():
            print(f"Warning: Circular import detected for {module_name}")
            return None
        raise


# Configuration pour éviter les imports circulaires dans les tests
os.environ["PYTEST_RUNNING"] = "1"
