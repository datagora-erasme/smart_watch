Comparateur d'Horaires
======================

Fonctionnalités
---------------

Le ComparateurHoraires effectue une comparaison intelligente et robuste entre deux structures d'horaires JSON personnalisées. Il normalise les données avant comparaison et génère des rapports détaillés des différences.

**Normalisation intelligente :**

- Tri automatique des créneaux par heure de début
- Gestion des occurrences spéciales (1er mardi du mois, etc.)
- Normalisation des formats de données inconsistants
- Support des horaires spéciaux et jours fériés

**Comparaison par période :**

- Périodes hors vacances scolaires vs vacances
- Jours fériés avec horaires spécifiques
- Jours spéciaux avec conditions particulières
- Détection des fermetures définitives

**Détection des différences :**

- Changements d'état (ouvert/fermé)
- Modification des créneaux horaires (ajout/suppression)
- Changements d'occurrence (1er → 3ème mardi)
- Modifications des horaires spéciaux

**Rapport détaillé :**

- Statut identique ou différent avec justification
- Description textuelle des différences par période
- Détails structurés pour analyse programmatique
- Gestion des cas d'erreur avec messages explicites

Modules
-------

.. automodule:: src.smart_watch.core.ComparateurHoraires
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__, __call__
   :inherited-members:
   :show-inheritance: