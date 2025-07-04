HTML to Markdown
================

.. automodule:: src.smart_watch.utils.HtmlToMarkdown
   :members:
   :undoc-members:
   :show-inheritance:

Classes principales
==================

.. autoclass:: src.smart_watch.utils.HtmlToMarkdown.HtmlToMarkdown
   :members:
   :undoc-members:
   :show-inheritance:

Exemple d'utilisation
====================

.. code-block:: python

   from src.smart_watch.utils.HtmlToMarkdown import HtmlToMarkdown

   # Conversion HTML vers Markdown
   html_content = "<h1>Titre</h1><p>Contenu</p>"
   converter = HtmlToMarkdown(html_content)
   markdown = converter.convert()
   
   print(markdown)
   # # Titre
   # Contenu
