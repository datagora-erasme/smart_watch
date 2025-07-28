Modules Processing
==================

Les modules de traitement forment le cœur du pipeline de l'application. Ils exécutent une séquence d'opérations pour extraire, filtrer, analyser et comparer les données d'horaires d'ouverture, depuis la source web jusqu'au résultat final stocké en base de données.

Le Pipeline de Traitement
-------------------------

Le traitement suit un pipeline séquentiel où chaque processeur est responsable d'une étape distincte :

1.  **Setup** : Initialise une nouvelle exécution, charge les lieux à traiter depuis un fichier CSV et prépare la base de données.
2.  **URL** : Récupère le contenu HTML de chaque URL et le convertit en Markdown brut.
3.  **Markdown** : Filtre le Markdown brut en utilisant des embeddings sémantiques pour ne conserver que les sections de texte pertinentes aux horaires, réduisant ainsi la charge pour l'étape suivante.
4.  **LLM** : Envoie le Markdown filtré à un modèle de langage (LLM) pour en extraire les horaires sous forme de JSON structuré, puis convertit ce JSON au format OSM.
5.  **Comparison** : Compare les horaires extraits par le LLM avec les horaires de référence pour détecter les différences.

Le `DatabaseProcessor` n'est pas une étape du pipeline, mais un service central utilisé par tous les autres processeurs pour interagir avec la base de données.

Modules
-------

.. toctree::
   :maxdepth: 1

   setup_processor
   url_processor
   markdown_processor
   llm_processor
   comparison_processor
   database_processor
