Récupérateur d'URL
==================

Le module ``URLRetriever`` gère la récupération de contenu à partir d'URLs web.

.. admonition:: Usage

   Ce module est utilisé par :doc:`URLProcessor <../processing/url_processor>` pour récupérer le contenu des pages web à analyser.

Fonctionnalités
---------------

- Récupère le contenu HTML des pages web à l'aide de Playwright.
- Met en œuvre des stratégies progressives pour gérer les erreurs de certificat SSL.
- Gère les erreurs réseau courantes comme les redirections et les temps morts.
- Convertit automatiquement le contenu HTML récupéré en Markdown à l'aide du module :doc:`HtmlToMarkdown <../utils/HtmlToMarkdown>`.

Modules
-------

.. automodule:: src.smart_watch.core.URLRetriever
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__, __call__
   :inherited-members:
   :show-inheritance:
