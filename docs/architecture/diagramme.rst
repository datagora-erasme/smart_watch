======================
Pipeline de traitement
======================

Les données sont traitées séquentiellement par un pipeline, orchestré par le fichier `main.py` :

1. **Création** : Initialisation de la base de données
2. **Initialisation** : Chargement des URLs et préparation de l'exécution
3. **Extraction URL** : Récupération du contenu web et conversion HTML → Markdown
4. **Nettoyage** : Normalisation et nettoyage du contenu Markdown
5. **Filtrage** : Sélection sémantique des sections pertinentes par embeddings
6. **Extraction LLM** : Interprétation du contenu et extraction des horaires au format JSON structuré
7. **Comparaison** : Analyse des différences avec les données de référence
8. **Rapport** : Génération et envoi du rapport final

Diagramme de flux
=================

.. code-block:: text

   [ main.py ] (Orchestrateur)
      │
      ├─> A. Charge la configuration [ core.ConfigManager ] (depuis .env)
      │         └─> Agrège [ config.* ] (LLMConfig, DatabaseConfig, etc.)
      │
      ├─> B. Instancie les processeurs principaux avec la configuration
      │
      └─> C. Exécute séquentiellement le pipeline :
            │
            ├─> [1] Création : [ processing.DatabaseProcessor ]
            │     (Créé la base de données et les tables nécessaires)
            |
            ├─> [2] Initialisation : [ utils.CSVToPolars ] -> [ processing.SetupProcessor ]
            │     (Charge les URLs depuis le CSV et prépare une nouvelle exécution)
            │
            ├─> [3] Extraction URL : [ processing.URLProcessor ]
            │     (Récupère le contenu des URLs)
            │     └─> Utilise [ utils.HtmlToMarkdown ] pour la conversion
            │
            ├─> [4] Nettoyage : [ utils.MarkdownCleaner ]
            │     (Nettoie le Markdown brut)
            │
            ├─> [5] Filtrage : [ core.MarkdownProcessor ]
            │     (Filtre le Markdown sémantiquement par embeddings, pour ne garder que les sections pertinentes)
            │     └─> Utilise [ core.LLMClient ] pour les embeddings
            │
            ├─> [6] Extraction LLM : [ processing.LLMProcessor ]
            │     (Extrait par LLM et au format JSON les horaires du Markdown filtré)
            │     ├─> Utilise [ core.LLMClient ] pour l'appel au LLM
            │     └─> Utilise [ utils.CustomJsonToOSM ] pour convertir le JSON en format OSM
            │
            ├─> [7] Comparaison : [ processing.ComparisonProcessor ]
            │     (Compare les horaires extraits (OSM) avec les données de référence issues de data.grandlyon.com)
            │     └─> Utilise [ core.ComparateurHoraires ] pour la logique de comparaison
            │
            └─> [8] Rapport : [ reporting.ReportManager ]
                  (Génère et envoie le rapport final)
                  ├─> Utilise [ reporting.GenererRapportHTML ] pour créer le fichier HTML
                  └─> Utilise [ core.EmailSender ] pour envoyer l'email avec pièces jointes

Les différents modules exploités par le pipeline sont décrits dans la section :doc:`modules`.
