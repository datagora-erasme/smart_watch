HTML to Markdown
================

Le module HtmlToMarkdown convertit du contenu HTML au format Markdown, en ne renvoyant que le texte.

Fonctionnalités
---------------

- Conversion avec inscriptis
- Extraction du texte brut (pas d'images ou liens)

.. admonition:: Usage

   La fonction ``convert_html_to_markdown`` est utilisée dans :
   
   - la fonction ``retrieve_url`` du module :doc:`URLRetriever <../core/URLRetriever>`, pour convertir en Markdown le contenu HTML des pages web indiquées dans le csv ``CSV_URL_HORAIRES``.

Modules
-------

.. automodule:: src.smart_watch.utils.HtmlToMarkdown
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__, __call__
   :inherited-members:
   :show-inheritance:
