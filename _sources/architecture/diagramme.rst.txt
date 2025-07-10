==========
Diagramme
==========

Flux de données
===============

Le pipeline de données suit un flux séquentiel optimisé :

1. **Configuration** : Chargement et validation des paramètres
2. **Initialisation** : Création de la base de données et chargement des URLs
3. **Extraction** : Récupération parallèle du contenu web, et conversion HTML → Markdown
4. **Nettoyage** : Normalisation et nettoyage du contenu Markdown
5. **Filtrage** : Sélection sémantique des sections pertinentes par embeddings
6. **Extraction LLM** : Interprétation du contenu pour extraire les horaires
7. **Conversion** : Transformation au format OpenStreetMap standardisé
8. **Comparaison** : Analyse des différences avec les données de référence
9. **Rapport** : Génération et envoi du rapport final


Diagramme de flux
=================

.. code-block:: text

   [ main.py ] (Orchestrateur)
      │
      ├─> 1. Initialise [ core.ConfigManager ] (Charge la configuration depuis .env)
      │         └─> Agrège [ config.* ] (LLMConfig, DatabaseConfig, etc.)
      │
      ├─> 2. Instancie les processeurs principaux avec la configuration
      │
      └─> 3. Exécute séquentiellement le pipeline :
            │
            ├─> [1] SETUP : [ utils.CSVToPolars ] -> [ processing.DatabaseManager ]
            │     (Charge les URLs depuis le CSV et prépare une nouvelle exécution)
            │
            ├─> [2] FETCH : [ processing.URLProcessor ]
            │     (Récupère le contenu des URLs)
            │     └─> Utilise [ utils.HtmlToMarkdown ] pour la conversion
            │
            ├─> [3] CLEAN : [ utils.MarkdownCleaner ]
            │     (Nettoie le Markdown brut)
            │
            ├─> [4] FILTER : [ core.MarkdownProcessor ]
            │     (Filtre sémantiquement le Markdown pour ne garder que les sections pertinentes)
            │     └─> Utilise [ core.LLMClient ] pour les embeddings
            │
            ├─> [5] EXTRACT : [ processing.LLMProcessor ]
            │     (Extrait les horaires du Markdown filtré au format JSON)
            │     ├─> Utilise [ core.LLMClient ] pour l'appel au LLM
            │     └─> Utilise [ utils.CustomJsonToOSM ] pour convertir le JSON en format OSM
            │
            ├─> [6] COMPARE : [ processing.ComparisonProcessor ]
            │     (Compare les horaires extraits (OSM) avec les données de référence)
            │     └─> Utilise [ core.ComparateurHoraires ] pour la logique de comparaison
            │
            └─> [7] REPORT : [ reporting.ReportManager ]
                  (Génère et envoie le rapport final)
                  ├─> Utilise [ reporting.GenererRapportHTML ] pour créer le fichier HTML
                  └─> Utilise [ core.EmailSender ] pour envoyer l'email avec pièces jointes
