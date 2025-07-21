Markdown Processor
==================

Fonctionnalités
---------------

Le MarkdownProcessor utilise des embeddings sémantiques pour filtrer intelligemment le contenu markdown et extraire uniquement les sections pertinentes aux horaires d'ouverture. Il optimise les appels LLM en réduisant la taille des prompts.

**Filtrage sémantique :**

- Segmentation du contenu en phrases avec patterns configurables
- Calcul d'embeddings via API OpenAI/Mistral compatibles
- Comparaison de similarité cosinus avec phrases de référence
- Sélection des sections au-dessus du seuil de pertinence

**Optimisation des embeddings :**

- Pré-calcul des embeddings de référence une seule fois par exécution
- Réutilisation des embeddings pour tous les documents
- Accumulation des émissions CO2 pour reporting global
- Gestion des erreurs d'API avec fallback vers contenu original

**Enrichissement contextuel :**

- Fenêtre de contexte autour des phrases pertinentes
- Préservation du sens avec phrases adjacentes
- Reconstruction du contenu filtré avec ponctuation
- Validation de la longueur minimale avant filtrage

**Gestion d'erreurs :**

- Fallback vers markdown nettoyé en cas d'erreur
- Traçabilité des erreurs dans la chaîne pipeline
- Logging détaillé des opérations et statistiques
- Mise à jour des émissions CO2 en base de données

Modules
-------

.. automodule:: smart_watch.processing.markdown_processor
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__, __call__
   :inherited-members:
   :show-inheritance:
