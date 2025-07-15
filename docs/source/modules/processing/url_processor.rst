URL Processor
=============

Fonctionnalités
---------------

Le URLProcessor gère l'extraction parallèle du contenu web avec conversion HTML vers markdown. Il utilise un ThreadPoolExecutor pour optimiser les performances et fournit une gestion robuste des erreurs réseau.

**Traitement parallèle :**

- ThreadPoolExecutor avec nombre de threads configurable
- Traitement par batch pour optimiser les mises à jour base de données
- Gestion des timeouts et retry avec délais adaptatifs
- Limitation du taux de requêtes pour éviter les blocages

**Pipeline de conversion :**

- Récupération HTML via URLRetriever avec User-Agent personnalisé
- Conversion HTML → Markdown avec HtmlToMarkdown et BeautifulSoup
- Nettoyage et normalisation du contenu markdown
- Stockage du `markdown_brut` en base avec métadonnées

**Gestion d'erreurs :**

- Codes HTTP détaillés avec messages explicites
- Gestion des timeouts, connexions échouées, et erreurs serveur
- Traçabilité complète dans la chaîne d'erreurs
- Continuation du traitement même en cas d'erreurs partielles

**Statistiques et monitoring :**

- Compteurs de succès/échec par type d'erreur
- Temps de traitement et performance par thread
- Logging détaillé des opérations et erreurs
- Reporting des statistiques consolidées

Modules
-------

.. automodule:: src.smart_watch.processing.url_processor
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__, __call__
   :inherited-members:
   :show-inheritance:
