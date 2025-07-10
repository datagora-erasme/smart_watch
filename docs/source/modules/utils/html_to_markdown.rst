HTML to Markdown
================

.. automodule:: src.smart_watch.utils.HtmlToMarkdown
   :members:
   :undoc-members:
   :show-inheritance:

Fonction principale
===================

.. autofunction:: src.smart_watch.utils.HtmlToMarkdown.convert_html_to_markdown

Exemple d'utilisation
====================

.. code-block:: python

   from src.smart_watch.utils.HtmlToMarkdown import convert_html_to_markdown

   # Conversion HTML vers Markdown
   html_content = "<h1>Titre</h1><p>Contenu</p>"
   markdown = convert_html_to_markdown(html_content)
   
   print(markdown)
   # # Titre
   # Contenu
