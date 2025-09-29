Scorer
======

Le module ``scorer`` est responsable de la comparaison entre une prédiction et une vérité terrain.

.. admonition:: Rôle

   La classe ``Scorer`` prend en entrée deux chaînes d'horaires au format OSM (une prédite par le pipeline, une autre issue de la vérité terrain), les compare en utilisant le ``ComparateurHoraires`` du module Core, et retourne un objet ``ScoreResult`` structuré.

Fonctionnalités
---------------

- Utilise les composants Core du projet (``OsmToJsonConverter``, ``HorairesComparator``) pour assurer une comparaison cohérente avec le pipeline principal.
- Gère la conversion des chaînes OSM en JSON.
- Analyse la chaîne de différences textuelle pour produire un **décompte d'erreurs atomiques**, permettant une analyse fine.
- Retourne un objet ``ScoreResult`` contenant le statut (Identique, Différent, Erreur), le décompte des différences, et le détail textuel.

Module
------

.. automodule:: src.smart_watch.evaluate.scorer
   :members:
   :undoc-members:
   :private-members: _to_json, _count_atomic_differences
   :special-members: __init__
   :show-inheritance:
