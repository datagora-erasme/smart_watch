Module d'évaluation
===================

Le module d'évaluation permet de tester et comparer différents LLM et paramètres sur la tâche d'extraction d'horaires.

.. toctree::
   :maxdepth: 2

Vue d'ensemble
==============

Le système d'évaluation comprend :

**Dataset d'évaluation :**
- Pages web avec horaires
- Vérité terrain annotée manuellement  
- Métadonnées (difficulté, tags, annotateur)

**Configurations de test :**
- Différents modèles LLM (GPT-4, Mistral, etc.)
- Variations de température
- Templates de prompt personnalisés
- Options de traitement (filtrage markdown, etc.)

**Métriques d'évaluation :**
- Score de similarité (0-1)
- Exactitude binaire (identique/différent)
- Temps de réponse
- Émissions CO2
- Métriques détaillées par composant

**Analyse des résultats :**
- Comparaisons par modèle
- Impact de la température
- Performance selon la difficulté
- Visualisations interactives
- Identification des cas difficiles

Workflow d'évaluation
=====================

1. **Préparation du dataset**
   
   .. code-block:: python
   
      db = EvaluationDatabase()
      db.add_dataset_item(
          identifiant="mairie_001",
          nom="Mairie de Lyon 1er",
          type_lieu="mairie", 
          url="https://mairie1.lyon.fr/horaires",
          ground_truth_json=horaires_veridiques,
          markdown_content=contenu_web,
          difficulte=3
      )

2. **Configuration des tests**
   
   .. code-block:: python
   
      # Test de différents modèles
      db.add_configuration(
          nom="GPT4_temp_0",
          llm_provider="OPENAI",
          llm_model="gpt-4",
          llm_temperature=0.0
      )
      
      db.add_configuration(
          nom="Mistral_Large", 
          llm_provider="MISTRAL",
          llm_model="mistral-large-latest",
          llm_temperature=0.1
      )

3. **Exécution de l'évaluation**
   
   .. code-block:: python
   
      manager = EvaluationManager()
      manager.run_batch_evaluation(batch_id)

4. **Analyse des résultats**
   
   .. code-block:: python
   
      analyzer = EvaluationAnalyzer()
      
      # Statistiques par modèle
      model_stats = analyzer.analyze_by_model()
      
      # Impact de la température
      temp_impact = analyzer.analyze_by_temperature()
      
      # Rapport complet avec graphiques
      analyzer.generate_performance_report()

Métriques et comparaisons
=========================

**Score de similarité :**

Mesure la proximité entre horaires extraits et vérité terrain (0 = complètement différent, 1 = identique).

**Exactitude binaire :**

Détermine si les horaires sont strictement identiques selon le comparateur.

**Métriques temporelles :**

- Temps de réponse LLM
- Durée totale d'exécution
- Temps de traitement markdown

**Impact environnemental :**

- Émissions CO2 par modèle
- Consommation énergétique relative

**Métriques détaillées :**

- Longueur du prompt généré
- Longueur du markdown traité
- Détails de comparaison par période
