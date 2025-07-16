URL Retriever
=============

Fonctionnalités
---------------

Le URLRetriever gère la récupération robuste de contenu web avec gestion avancée des erreurs SSL et conversion automatique HTML vers Markdown. Il utilise des stratégies progressives pour contourner les problèmes de certificats.

**Récupération robuste :**

- Stratégies SSL progressives (default → no_verify → low_security → full_mitigation)
- Gestion des certificats SSL défaillants ou expirés
- User-Agent réaliste pour éviter les blocages
- Retry automatique avec différentes configurations

**Gestion des erreurs réseau :**

- Détection et gestion des redirections infinies
- Timeouts configurables avec gestion des dépassements
- Codes HTTP détaillés avec messages explicites
- Logging contextuel avec identifiants de lieux

**Conversion automatique :**

- HTML vers Markdown via HtmlToMarkdown
- Fallback HTML si conversion Markdown échoue
- Détection et gestion des encodages de caractères
- Préservation du contenu original en cas d'erreur

**Intégration système :**

- Utilisation du système ErrorHandler centralisé
- Contexte d'erreur enrichi avec URL et identifiant
- Logging détaillé des opérations et stratégies utilisées
- Retour de dictionnaire enrichi avec métadonnées

Modules
-------

.. automodule:: src.smart_watch.core.URLRetriever
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__, __call__
   :inherited-members:
   :show-inheritance: