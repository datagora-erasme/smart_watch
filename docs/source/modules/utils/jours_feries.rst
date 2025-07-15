Jours Fériés
============

Fonctionnalités
---------------

Le module JoursFeries récupère les jours fériés français officiels depuis l'API gouvernementale calendrier.api.gouv.fr. Il fournit des fonctions utilitaires pour enrichir automatiquement les horaires des mairies.

**Source de données :**
- API calendrier.api.gouv.fr officielle
- Données gouvernementales françaises certifiées
- Support des zones métropole et outre-mer
- Années configurables avec fallback année courante

**Gestion des zones :**
- Zone métropole par défaut
- Support des départements et territoires d'outre-mer
- Validation automatique des paramètres de zone
- Gestion des erreurs de zone non reconnue

**Fonctionnalités utilitaires :**
- Calcul automatique du jour de la semaine
- Noms des jours en français
- Format de dates standardisé YYYY-MM-DD
- Intégration avec le système d'enrichissement des mairies

**Gestion d'erreurs :**
- Requêtes réseau avec timeout configurable
- Validation des codes de réponse HTTP
- Logging détaillé des opérations et erreurs
- Gestion des erreurs de parsing JSON

Fonctions principales
---------------------

.. automodule:: src.smart_watch.utils.JoursFeries
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__, __call__
   :inherited-members:
   :show-inheritance: