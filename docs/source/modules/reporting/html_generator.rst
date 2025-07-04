HTML Generator (GenererRapportHTML)
===================================

.. automodule:: src.smart_watch.reporting.GenererRapportHTML
   :members:
   :undoc-members:
   :show-inheritance:

Fonctions principales
=====================

.. autofunction:: src.smart_watch.reporting.GenererRapportHTML.generer_rapport_html

.. autofunction:: src.smart_watch.reporting.GenererRapportHTML.to_json

Fonctionnalités
===============

Le générateur HTML crée des rapports interactifs sophistiqués :

**Templates Jinja2 :**
- **ReportTemplate.html** : Rapport complet avec onglets, filtres et modaux
- **SimpleReportTemplate.html** : Résumé concis pour les emails

**Classification intelligente :**
- **Succès** (✅) : URLs accessibles, horaires extraits et identiques
- **Différences horaires** (⚠️) : Horaires extraits mais différents de la référence
- **Erreurs d'accès** (🔒) : URLs inaccessibles, codes HTTP non-200
- **Erreurs d'extraction** (❌) : URLs accessibles mais échec LLM/OSM

**Données extraites :**
- Extraction depuis base SQLite avec jointures optimisées
- Traçabilité complète : markdown_brut → markdown_nettoye → markdown_filtre
- Chaîne d'erreurs avec timestamps et types détaillés
- Statistiques par type de lieu et codes HTTP

**Fonctionnalités interactives :**
- Tri et filtrage dynamique par JavaScript
- Modals pour visualiser les données JSON/OSM
- Recherche dans les URLs et noms d'établissements
- Export des données et impression

Exemple d'utilisation
=====================

.. code-block:: python

   from src.smart_watch.reporting.GenererRapportHTML import generer_rapport_html

   # Configuration du modèle
   model_info = {
       "modele": "gpt-4",
       "fournisseur": "OpenAI",
       "base_url": "https://api.openai.com/v1"
   }

   # Génération du rapport
   resume_html, fichier_html = generer_rapport_html(
       db_file="data/SmartWatch.db",
       table_name="resultats_extraction",
       titre_rapport="Rapport de vérification des URLs",
       model_info=model_info
   )
   
   print(f"Rapport généré: {fichier_html}")
   print(f"Résumé: {len(resume_html)} caractères")

Structure des données du rapport
================================

**Données d'entrée (base SQLite) :**

.. code-block:: sql

   SELECT 
       l.type_lieu, l.identifiant, l.nom, l.url, l.horaires_data_gl,
       r.statut_url, r.message_url, r.code_http,
       r.markdown_brut, r.markdown_nettoye, r.markdown_filtre,
       r.llm_horaires_json, r.llm_horaires_osm,
       r.horaires_identiques, r.differences_horaires,
       r.erreurs_pipeline
   FROM resultats_extraction r 
   JOIN lieux l ON r.lieu_id = l.identifiant

**Données de sortie (template) :**

- ``stats_globales`` : Compteurs totaux et pourcentages
- ``statuts_disponibles`` : Groupement par statut avec URLs détaillées
- ``types_lieu_stats`` : Répartition par type d'établissement
- ``codes_http_stats`` : Distribution des codes de réponse HTTP

Gestion des erreurs et edge cases
=================================

- **JSON invalide** : Conversion automatique en chaîne et encodage base64
- **Templates manquants** : Vérification d'existence et erreurs explicites
- **Base corrompue** : Gestion des erreurs SQL avec messages utilisateur
- **Données manquantes** : Valeurs par défaut pour tous les champs requis
- **Caractères UTF-8** : Préservation complète via encodage base64

Le module utilise des décorateurs de gestion d'erreurs pour la traçabilité complète.
