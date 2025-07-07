"""
Script pour générer la documentation Sphinx
"""

import os
import subprocess
import sys
from pathlib import Path


def build_docs():
    """Génère la documentation Sphinx"""
    # Chemin vers le répertoire docs
    docs_dir = Path(__file__).parent.resolve()

    if not docs_dir.exists():
        print(f"Erreur: Le répertoire {docs_dir} n'existe pas")
        return False

    # Changer vers le répertoire docs
    os.chdir(docs_dir)

    # Commande de build Sphinx
    cmd = [
        sys.executable,
        "-m",
        "sphinx",
        "-b",
        "html",  # Format HTML
        "-E",  # Reconstruction complète
        ".",  # Répertoire source
        "_build/html",  # Répertoire de destination
    ]

    try:
        print("Génération de la documentation...")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Documentation générée avec succès!")
        print(
            f"Résultat disponible dans: {docs_dir / '_build' / 'html' / 'index.html'}"
        )
        return True

    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de la génération: {e}")
        print(f"Sortie d'erreur: {e.stderr}")
        return False
    except FileNotFoundError:
        print("Erreur: Sphinx n'est pas installé")
        print("Installez-le avec: pip install sphinx")
        return False


if __name__ == "__main__":
    build_docs()
