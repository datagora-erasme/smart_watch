Vue d'ensemble
===============

- **MarkdownCleaner** : Nettoyage du markdown (liens, formatage, caractères spéciaux)
- **HtmlToMarkdown** : Conversion HTML → Markdown avec BeautifulSoup + lxml
- **JSON/OSM Converters** : Conversion bidirectionnelle JSON ↔ OSM
- **CSVToPolars** : Chargement efficace des fichiers CSV avec Polars
- **JoursFeries** : Enrichissement des horaires des mairies avec jours fériés français
- **VacancesScolaires** : Récupération des périodes de vacances scolaires via API gouvernementale

Modules
========

Les modules Utils fournissent les utilitaires essentiels pour la conversion de données, le nettoyage et la manipulation de formats.

.. toctree::
   :maxdepth: 1

   markdown_cleaner
   html_to_markdown
   json_osm_converters
   csv_polars
   jours_feries
   vacances_scolaires

Utilitaires de données temporelles
==================================

Les modules `JoursFeries` et `VacancesScolaires` récupèrent des données officielles :

- **JoursFeries** : API calendrier.api.gouv.fr pour les jours fériés français
- **VacancesScolaires** : API data.education.gouv.fr pour les périodes de vacances scolaires
