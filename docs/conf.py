# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# Ajouter le chemin du projet pour que Sphinx puisse importer les modules
# Depuis docs/, on remonte d'un niveau pour accéder à la racine du projet
sys.path.insert(0, os.path.abspath(".."))
sys.path.insert(0, os.path.abspath("../src"))

# -- Project information -----------------------------------------------------
project = "SmartWatch"
copyright = '2025, <a href="https://github.com/berangerthomas">Béranger THOMAS</a>, <a href="https://erasme.org/">ERASME</a>'
author = "Béranger THOMAS"
release = "2025-06"

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",  # Génération automatique de la doc
    "sphinx.ext.autosummary",  # Résumés automatiques
    "sphinx.ext.viewcode",  # Liens vers le code source
    "sphinx.ext.napoleon",  # Support Google/NumPy docstrings
    "sphinx.ext.intersphinx",  # Liens inter-documentation
    "sphinx.ext.todo",  # Support des TODOs
    "sphinx.ext.coverage",  # Couverture de la documentation
]

# Configuration autodoc - RÉDUCTION DE LA VERBOSITÉ
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": False,  # Masquer les membres non documentés
    "exclude-members": "__weakref__,__dict__,__module__",
    "show-inheritance": False,  # Masquer l'héritage pour réduire le bruit
}

# Configuration autosummary
autosummary_generate = True
autosummary_generate_overwrite = True

# Configuration Napoleon pour les docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False

# Configuration intersphinx
intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "sqlalchemy": ("https://docs.sqlalchemy.org/en/20/", None),
}

templates_path = ["_templates"]
exclude_patterns = [
    "build",
    "Thumbs.db",
    ".DS_Store",
    "**/__pycache__",
    "../modules/**",
]

language = "fr"

# -- Options for HTML output -------------------------------------------------
html_theme = "alabaster"  # Utiliser un seul thème
# html_static_path = ["_static"] # Commenté car le dossier n'existe pas

# Configuration alabaster avec navigation réduite
html_theme_options = {
    "description": "Extracteur d'Horaires Intelligent",
    "github_user": "datagora-erasme",
    "github_repo": "smart_watch",
    "github_button": True,
    "github_count": False,
    "show_powered_by": False,
    "sidebar_width": "280px",
    "page_width": "1200px",
    "body_text_align": "left",
    "show_related": False,  # Masquer les liens connexes
    "sidebar_includehidden": False,  # Ne pas inclure les éléments cachés
    "sidebar_collapse": True,  # Permettre la réduction des sections
    "navigation_depth": 2,  # Limiter à 2 niveaux de profondeur max
}

# Configuration pour le support du code
pygments_style = "sphinx"
highlight_language = "python"

# Configuration TODO
todo_include_todos = False  # Masquer les TODOs dans la navigation

# Navigation latérale simplifiée - RÉDUCTION DES ÉLÉMENTS
html_sidebars = {
    "**": [
        "about.html",
        "navigation.html",  # Navigation principale seulement
        "searchbox.html",  # Boîte de recherche
    ]
}
