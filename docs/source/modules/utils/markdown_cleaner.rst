Markdown Cleaner
================

Fonctionnalités
---------------

Le MarkdownCleaner nettoie et normalise le contenu markdown brut pour optimiser l'extraction d'horaires. Il utilise des expressions régulières avancées et applique des règles de nettoyage configurables.

**Suppression des éléments indésirables :**
- Liens markdown sous toutes formes [texte](url), [texte](url "titre")
- Images standalone ![alt](img) et liens avec images [![alt](img)](url)
- Liens automatiques <http://example.com>
- Lignes de formatage (caractères décoratifs, séparateurs)

**Normalisation du contenu :**
- Remplacement de caractères selon dictionnaire configurable
- Suppression des sauts de ligne multiples (3+ → 2)
- Élimination des lignes en double consécutives
- Nettoyage des espaces et caractères de formatage

**Traitement par lot :**
- Pipeline intégré avec DatabaseManager
- Traitement des markdown_brut → markdown_nettoye
- Statistiques détaillées des opérations de nettoyage
- Gestion d'erreurs avec continuation du traitement

**Optimisation pour LLM :**
- Réduction significative de la taille des prompts
- Préservation du contenu pertinent aux horaires
- Suppression du bruit visuel et navigationnel
- Amélioration de la précision d'extraction

Classes principales
-------------------

.. automodule:: src.smart_watch.utils.MarkdownCleaner
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__, __call__
   :inherited-members:
   :show-inheritance:
