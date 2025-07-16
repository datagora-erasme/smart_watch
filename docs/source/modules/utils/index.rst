Modules Utils
=============

Fonctionnalités
---------------

Les modules Utils fournissent les utilitaires essentiels pour la conversion de données, le nettoyage et la manipulation de formats. Ils constituent la couche de transformation entre les sources externes et le pipeline de traitement SmartWatch.

**Conversion et transformation :**

- Convertisseurs bidirectionnels JSON ↔ OpenStreetMap opening_hours
- Conversion HTML → Markdown avec parsing robuste BeautifulSoup
- Chargement CSV optimisé avec Polars et détection automatique
- Nettoyage avancé de contenu Markdown avec expressions régulières

**Données temporelles officielles :**

- Récupération des jours fériés français via API gouvernementale
- Périodes de vacances scolaires avec filtrage par zone et localisation
- Formatage et normalisation des dates
- Support des zones métropole et outre-mer

**Optimisations système :**

- Gestion robuste des erreurs réseau et parsing
- Logging détaillé de toutes les opérations
- Performance optimisée avec Polars pour grandes données
- Intégration avec le système ErrorHandler centralisé

**Pipeline d'intégration :**

- Modules conçus pour s'intégrer dans le pipeline principal
- Interfaces standardisées avec classes de résultats
- Gestion des fichiers temporaires avec nettoyage automatique
- Support des sources locales et distantes

Vue d'ensemble
---------------

- **MarkdownCleaner** : Nettoyage du markdown (liens, formatage, caractères spéciaux)
- **HtmlToMarkdown** : Conversion HTML → Markdown avec BeautifulSoup + lxml
- **JSON/OSM Converters** : Conversion bidirectionnelle JSON ↔ OSM opening_hours
- **CSVToPolars** : Chargement efficace des fichiers CSV avec Polars
- **JoursFeries** : Récupération des jours fériés français via API gouvernementale
- **VacancesScolaires** : Périodes de vacances scolaires avec filtrage avancé

Modules
-------

.. toctree::
   :maxdepth: 1

   markdown_cleaner
   html_to_markdown
   json_osm_converters
   csv_polars
   jours_feries
   vacances_scolaires

Utilitaires de données temporelles
----------------------------------

Les modules `JoursFeries` et `VacancesScolaires` accèdent aux APIs officielles françaises :

- **JoursFeries** : API calendrier.api.gouv.fr pour les jours fériés français
- **VacancesScolaires** : API data.education.gouv.fr pour les périodes de vacances scolaires

Ces modules fournissent des données certifiées et mises à jour automatiquement pour l'enrichissement des horaires d'ouverture.
