Get Prompt
==========

Fonctionnalités
---------------

Le module GetPrompt génère des prompts optimisés pour l'extraction d'horaires via LLM. Il intègre le schéma JSON dans le prompt et fournit des instructions spécialisées selon le type d'établissement.

**Génération de prompts :**

- Prompt système avec rôle d'expert en extraction d'horaires
- Instructions détaillées pour le format JSON attendu
- Intégration automatique du schéma JSON dans le prompt
- Contexte spécifique au lieu (nom, type, contenu markdown)

**Instructions spécialisées :**

- Gestion des occurrences spéciales (1er lundi du mois, etc.)
- Format de dates standardisé (YYYY-MM-DD)
- Année de référence automatique pour les dates sans année
- Extraction des jours spéciaux avec dates précises

**Optimisation LLM :**

- Séparation claire entre prompt système et utilisateur
- Instructions pour éviter les inventions de données
- Guidance pour la sélection des horaires les plus pertinents
- Format de sortie JSON exclusif sans formatage supplémentaire

**Gestion des cas complexes :**

- Multiples jeux d'horaires avec sélection du plus pertinent
- Détection des fermetures temporaires ou définitives
- Gestion des services multiples avec priorisation
- Validation des données extraites avant structuration

Modules
-------

.. automodule:: src.smart_watch.core.GetPrompt
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__, __call__
   :inherited-members:
   :show-inheritance: