Database Processor
==================

Fonctionnalités
---------------

Le DatabaseProcessor gère la base de données SQLite avec un schéma relationnel à 3 tables. Il fournit une interface complète pour les opérations CRUD, la gestion des exécutions et la traçabilité des erreurs.

**Schéma relationnel :**

- Table `lieux` : référentiel des établissements avec horaires de référence
- Table `executions` : historique des exécutions avec métadonnées LLM
- Table `resultats_extraction` : résultats détaillés par lieu et exécution
- Relations avec contraintes d'intégrité référentielle

**Gestion des exécutions :**

- Setup automatique des exécutions avec détection de reprises
- Classification des résultats selon l'état du pipeline
- Traçabilité complète des étapes (URL, nettoyage, LLM, comparaison)
- Accumulation des émissions CO2 par exécution

**Traçabilité des erreurs :**

- Chaîne d'erreurs avec timestamps : `[HH:MM:SS] TYPE: message`
- Types d'erreur : URL, NETTOYAGE, FILTRAGE, LLM, OSM, COMPARAISON
- Accumulation des erreurs par étape avec préservation historique
- Méthodes spécialisées pour ajouter des erreurs par type

**Optimisations :**

- Mises à jour par batch pour l'insertion des lieux
- Requêtes optimisées avec jointures pour la récupération
- Gestion des transactions pour assurer la cohérence
- Indexation sur les clés étrangères pour les performances

Modules
-------

.. automodule:: src.smart_watch.processing.database_processor
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__, __call__
   :inherited-members:
   :show-inheritance: