===============
Stack technique
===============

Voici un aperçu des technologies employées.

Langage du projet
=================

**Python**
    Langage unique du projet.

Framework et bibliothèques principales
======================================

Traitement de données
---------------------

**Polars**
    Pour le chargement et la manipulation de données tabulaires.

**SQLAlchemy**
    Pour la gestion de la base de données SQLite.

**SQLite**
    Pour stocker les résultats d'extraction et les métadonnées.

Web scraping et traitement HTML
-------------------------------

**BeautifulSoup4**
    Parseur HTML/XML pour extraire le contenu des pages web de manière robuste.

**Requests**
    Bibliothèque HTTP pour récupérer le contenu des pages web.

**html2text**
    Conversion du HTML en Markdown pour faciliter le traitement par les modèles de langage.

Intelligence artificielle
-------------------------

**OpenAI API**
    Interface standardisée pour communiquer avec les modèles de langage.

**Mistral AI**
    Proposé en tant qu'alternative aux interfaces compatibles OpenAI. Utilise la librairie `mistralai` native.

**Embeddings**
    Utilisés pour filtrer le contenu Markdown. Fonctionne avec un modèle accessible via la même API compatible OpenAI que le LLM.

Configuration et environnement
------------------------------

**python-dotenv**
    Gestion des variables d'environnement via fichiers ``.env`` pour une configuration flexible.

**Pydantic / Dataclasses**
    Validation et typage des données.

Parallélisme et performance
--------------------------

**ThreadPoolExecutor**
    Traitement parallèle des URLs pour accélérer la récupération du contenu web.

Logging et monitoring
--------------------

**Logging standard Python**
    Système de journalisation centralisé avec rotation automatique des fichiers.

**Gestion d'erreurs centralisée**
    Capture et traitement uniforme des exceptions avec contexte détaillé.

**CodeCarbon**
    Mesure les émissions de CO2 des appels aux modèles de langage pour un suivi de l'impact environnemental.

Communication
------------

**SMTP (smtplib)**
    Envoi automatique des rapports par email avec support SSL/TLS.

**Jinja2**
    Moteur de templates pour la génération de rapports HTML personnalisés.

Déploiement
===========

**Docker**
    Conteneurisation pour un déploiement simplifié et reproductible.

**GitHub Actions**
    CI/CD pour le déploiement Docker et de la documentation.

**Sphinx + Read the Docs Theme**
    Génération automatique de documentation technique à partir du code.

Formats de données
==================

**CSV**
    Format d'entrée pour les listes d'établissements et données de référence.

**JSON**
    Format intermédiaire pour les horaires extraits par les LLMs.

**OSM (OpenStreetMap)**
    Format de sortie standardisé pour les horaires d'ouverture.

**HTML**
    Format de rapport final avec visualisations interactives.


Performance et parallélisme
===========================

Le système est optimisé pour traiter efficacement de grandes quantités d'URLs :

- **Traitement parallèle** : ThreadPoolExecutor pour les requêtes HTTP
- **Gestion mémoire** : Utilisation de Polars pour les gros datasets
- **Cache intelligent** : Évite le retraitement des données inchangées
- **Rotation des logs** : Prévient l'accumulation excessive de fichiers
- **Timeouts configurables** : Évite les blocages sur les ressources lentes