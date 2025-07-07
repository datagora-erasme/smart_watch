# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# Ajouter le chemin du projet pour que Sphinx puisse importer les modules
# Depuis docs/, on remonte d'un niveau pour accéder à la racine du projet
sys.path.insert(0, os.path.abspath(".."))
# sys.path.insert(0, os.path.abspath("../src"))


# -- Project information -----------------------------------------------------
project = "SmartWatch"
copyright = "2025, Béranger THOMAS, ERASME, Métropole de Lyon"
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
    "sphinx.ext.githubpages",  # Support pour la publication sur GitHub Pages
]


# Configuration autodoc
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

# Configuration de la page web
html_title = "SmartWatch Documentation"
html_short_title = "SmartWatch"
# html_logo = "../src/smart_watch/assets/images/logo_carre.jpg"
html_favicon = "../src/smart_watch/assets/images/favicon.jpg"

# Configuration intersphinx
intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "sqlalchemy": ("https://docs.sqlalchemy.org/en/20/", None),
}

templates_path = ["_templates"]
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    "**/__pycache__",
    "../modules/**",
]

language = "fr"

# -- Options for HTML output -------------------------------------------------
html_theme = "sphinx_rtd_theme"

# Configuration sphinx_rtd_theme
html_theme_options = {
    "display_version": True,
    "prev_next_buttons_location": "bottom",
    "style_external_links": False,
    "vcs_pageview_mode": "",
    "collapse_navigation": True,
    "sticky_navigation": True,
    "navigation_depth": 2,
    "includehidden": False,
    "titles_only": False,
}

# Configuration pour le support du code
pygments_style = "sphinx"
highlight_language = "python"

# Configuration TODO
todo_include_todos = False  # Masquer les TODOs dans la navigation

# Navigation latérale simplifiée
html_sidebars = {
    "**": [
        "about.html",
        "navigation.html",  # Navigation principale seulement
        "searchbox.html",  # Boîte de recherche
    ]
}
