HTML to Markdown
================

.. automodule:: src.smart_watch.utils.HtmlToMarkdown
   :members:
   :undoc-members:
   :show-inheritance:

Fonctionnalités
---------------

Le module HtmlToMarkdown convertit le contenu HTML en format Markdown avec une approche robuste utilisant BeautifulSoup pour le parsing. Il gère les balises HTML malformées et produit un Markdown propre.

**Conversion robuste :**
- Parsing HTML avec BeautifulSoup et moteur lxml
- Nettoyage automatique des balises malformées
- Gestion des caractères spéciaux et encodages
- Fallback gracieux en cas d'erreur

**Pipeline de traitement :**
- Validation et nettoyage du HTML d'entrée
- Parsing avec BeautifulSoup pour structure DOM valide
- Conversion via bibliothèque html-to-markdown
- Retour de chaîne vide en cas d'échec

**Intégration système :**
- Gestion d'erreurs via décorateur @handle_errors
- Logging détaillé des opérations de conversion
- Traitement des contenus vides avec validation
- Optimisé pour le pipeline URLRetriever

Module
-------

.. automodule:: src.smart_watch.utils.HtmlToMarkdown
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__, __call__
   :inherited-members:
   :show-inheritance: