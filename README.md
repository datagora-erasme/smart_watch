<div align="center">
  <img src="src/smart_watch/assets/images/logo_app.jpg" alt="Logo SmartWatch" />
</div>

# SmartWatch : Extracteur d'Horaires Intelligent

**SmartWatch** est un pipeline de données complet conçu pour extraire, analyser, et comparer les horaires d'ouverture de divers établissements (mairies, piscines, médiathèques) à partir de leurs sites web. Il utilise des modèles de langage pour interpréter le contenu et le comparer à des données de référence, puis génère et envoie par mail des rapports HTML interactifs pour visualiser les résultats.

## ✨ Fonctionnalités

*   **Collecte de Données** : Charge les URLs des établissements à analyser depuis un fichier CSV.
*   **Conversion des Données** : Converti les pages web en Markdown et nettoie ce dernier pour ne garder que l'essentiel
*   **Filtrage de Contenu Intelligent** : Utilise des embeddings (via `nomic-embed`) pour identifier et extraire uniquement les sections de page web pertinentes aux horaires, optimisant ainsi les appels aux LLM.
*   **Extraction par LLM** : Interroge des LLM (compatibles OpenAI ou Mistral) pour extraire les horaires dans un format structuré customisé (JSON).
*   **Conversion des horaires** : Le format JSON customisé est converti au format OSM.
*   **Comparaison Automatisée** : Compare les horaires extraits par le LLM avec des données de référence (depuis data.grandlyon.com) pour détecter les divergences.
*   **Rapports Détaillés** : Génère des rapports HTML interactifs et un résumé simple, permettant de visualiser les statistiques globales, les statuts de traitement, et les détails de chaque URL.
*   **Notifications** : Envoie automatiquement les rapports par email.
*   **Orchestration Robuste** : Un pipeline assure une exécution séquentielle et contrôlée.
*   **Conteneurisation** : Prêt à l'emploi avec Docker et Docker Compose pour un déploiement simplifié.

## 🚀 Installation

1.  **Clonez le dépôt :**
    ```sh
    git clone <url-du-repo>
    cd smart_watch
    ```

2.  **Créez un environnement virtuel et activez-le :**
    ```sh
    python -m venv .venv
    source .venv/bin/activate  # Sur Windows: .venv\Scripts\activate
    ```

3.  **Installez les dépendances :**
    ```sh
    pip install -r requirements.txt
    ```

## ⚙️ Configuration

1.  Créez un fichier `.env` à la racine du projet en vous basant sur le modèle [`env.model`](.env.model).
2.  Configurez les variables d'environnement requises :
    *   `CSV_URL_HORAIRES`: L'URL ou le chemin local du fichier CSV contenant les lieux à analyser.
    *   **Configuration LLM** : Renseignez les clés d'API et les modèles pour le fournisseur de votre choix (OpenAI, Mistral, etc.).
    *   **Configuration Email** : Paramétrez les informations SMTP pour l'envoi des rapports.

## ▶️ Utilisation

Pour lancer le pipeline complet, exécutez le script principal :

```sh
python main.py
```

Le programme effectuera les actions suivantes :
1.  Initialisera la base de données SQLite (`data/SmartWatch.db`).
2.  Traitera chaque URL, filtrera le contenu, et extraira les horaires via le LLM.
3.  Comparera les résultats et stockera tout en base de données.
4.  Enverra un rapport par mail.
5.  Écrira les logs dans `logs/SmartWatch.log`.

## 🐳 Utilisation avec Docker

Vous pouvez également lancer l'application dans un conteneur Docker.

1.  **Construisez l'image :**
    ```sh
    docker build -t smartwatch .
    ```

2.  **Exécutez le conteneur :**
    Assurez-vous que votre fichier `.env` est présent à la racine.
    ```sh
    docker run --env-file .env -v $(pwd)/data:/app/data -v $(pwd)/logs:/app/logs smartwatch
    ```
    Les rapports et la base de données seront générés dans les dossiers `data` et `logs` de votre machine hôte.

## 📄 Licence

Ce projet est sous licence GNU General Public License v3.0. Voir le fichier [LICENCE](LICENCE) pour
