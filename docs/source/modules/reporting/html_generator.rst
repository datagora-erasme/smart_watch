HTML Generator
==============

.. automodule:: src.smart_watch.reporting.GenererRapportHTML
   :members:
   :undoc-members:
   :show-inheritance:

Fonctionnalités
---------------

Le générateur HTML crée des rapports interactifs sophistiqués avec classification intelligente des résultats et visualisation des données. Il utilise des templates Jinja2 pour générer deux types de rapports.

**Templates et rapports :**
- ReportTemplate.html : rapport complet avec onglets, tri et modals JavaScript
- SimpleReportTemplate.html : résumé concis pour les emails
- Support des données JSON/OSM avec visualisation dans modals
- Fonctionnalités interactives (tri, filtrage, recherche)

**Classification intelligente :**
- Succès (✅) : URLs accessibles, horaires extraits et identiques
- Différences horaires (⚠️) : horaires extraits mais différents de la référence
- Erreurs d'accès (🔒) : URLs inaccessibles, codes HTTP non-200
- Erreurs d'extraction (❌) : URLs accessibles mais échec LLM/parsing

**Extraction et traitement des données :**
- Extraction depuis base SQLite avec jointures optimisées
- Traçabilité complète : markdown_brut → markdown_nettoye → markdown_filtre
- Chaîne d'erreurs avec timestamps et types détaillés
- Statistiques par type de lieu et codes HTTP
- Suivi des émissions de CO2 par requête et pour l'exécution totale

**Fonctionnalités avancées :**
- Gestion des caractères UTF-8 avec encodage base64
- Conversion automatique des données JSON invalides
- Gestion des templates manquants avec erreurs explicites
- Export et impression des données avec JavaScript intégré

Structure des données du rapport
--------------------------------

**Données d'entrée (base SQLite) :**

.. code-block:: sql

   SELECT 
       l.type_lieu, l.identifiant, l.nom, l.url, l.horaires_data_gl,
       r.statut_url, r.message_url, r.code_http,
       r.markdown_brut, r.markdown_nettoye, r.markdown_filtre,
       r.llm_horaires_json, r.llm_horaires_osm,
       r.horaires_identiques, r.differences_horaires,
       r.erreurs_pipeline, r.llm_consommation_requete
   FROM resultats_extraction r 
   JOIN lieux l ON r.lieu_id - l.identifiant

**Données de sortie (template) :**

- ``stats_globales`` : Compteurs totaux et pourcentages
- ``statuts_disponibles`` : Groupement par statut avec URLs détaillées
- ``types_lieu_stats`` : Répartition par type d'établissement
- ``codes_http_stats`` : Distribution des codes de réponse HTTP
- ``execution_data`` : Données de l'exécution, comme la consommation CO2 totale

Gestion des erreurs et edge cases
---------------------------------

- **JSON invalide** : Conversion automatique en chaîne et encodage base64
- **Templates manquants** : Vérification d'existence et erreurs explicites
- **Base corrompue** : Gestion des erreurs SQL avec messages utilisateur
- **Données manquantes** : Valeurs par défaut pour tous les champs requis
- **Caractères UTF-8** : Préservation complète via encodage base64

Le module utilise des décorateurs de gestion d'erreurs pour la traçabilité complète.

Modules
-------

.. automodule:: src.smart_watch.reporting.GenererRapportHTML
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__, __call__
   :inherited-members:
   :show-inheritance: