Modules Utils
=============

Les modules Utils constituent une boîte à outils pour **analyser**, **convertir** et **nettoyer** des données de sources variées afin de les normaliser et de les préparer pour le reste de l'application.
Ils gèrent des formats standards (CSV, HTML, JSON, API externes) et spécifiques (JSON personnalisé et OSM pour les horaires d'ouverture), ainsi que des données contextuelles françaises (jours fériés, vacances scolaires).

Modules
-------

.. toctree::
   :maxdepth: 1

   CSVToPolars
   CustomJsonToOSM
   HtmlToMarkdown
   JoursFeries
   MarkdownCleaner
   OSMToCustomJson
   VacancesScolaires
