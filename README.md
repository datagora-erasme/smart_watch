# Smart Watch - Extracteur d'Horaires Web

Un système automatisé d'extraction et de vérification des horaires d'ouverture des lieux publics via l'analyse de pages web et l'intelligence artificielle.

## 🎯 Objectif

Ce projet permet de :
- Vérifier automatiquement la disponibilité d'URLs de lieux publics
- Extraire les horaires d'ouverture à partir du contenu web
- Générer des rapports HTML interactifs avec statistiques détaillées
- Envoyer des rapports par email
- Structurer les données d'horaires au format OpenStreetMap (OSM)

## 🏗️ Architecture

```
smart_watch/
├── main.py                              # Point d'entrée principal
├── requirements.txt                     # Dépendances Python
├── assets/                              # Templates et schémas
│   ├── ReportTemplate.html             # Template de rapport complet
│   ├── SimpleReportTemplate.html       # Template de rapport simplifié
│   └── opening_hours_schema_template.json # Schéma JSON pour les horaires
├── core/                               # Modules métier
│   ├── EnvoyerMail.py                 # Envoi d'emails
│   ├── GenererRapportHTML.py          # Génération de rapports
│   ├── GetPrompt.py                   # Construction des prompts LLM
│   ├── LLMClient.py                   # Clients pour LLM (local/Mistral)
│   └── URLRetriever.py                # Récupération de contenu web
└── utils/                             # Utilitaires
    ├── CSVToPolars.py                 # Conversion CSV vers Polars
    └── HtmlToMarkdown.py              # Conversion HTML vers Markdown
```

## 🚀 Fonctionnalités

### Extraction Web
- **Récupération robuste** : Gestion des erreurs SSL, redirections, timeouts
- **Conversion automatique** : HTML vers Markdown pour analyse LLM
- **Traitement concurrent** : Jusqu'à 100 URLs en parallèle

### Intelligence Artificielle
- **Support multi-LLM** : Compatible avec APIs locales et Mistral AI
- **Extraction structurée** : Format JSON standardisé pour les horaires
- **Validation de schéma** : Respect du format OpenStreetMap
- **Gestion des périodes** : Horaires normaux, vacances scolaires, jours fériés

### Rapports et Analytics
- **Rapports HTML interactifs** : Onglets, tri, recherche, graphiques
- **Statistiques complètes** : Par statut, type de lieu, codes HTTP
- **Export de données** : JSON intégré avec copie en presse-papiers
- **Envoi automatique** : Rapports par email avec pièces jointes

## 📋 Prérequis

- Python 3.11+
- Clé API Mistral AI (optionnel)
- Accès à une API LLM locale (optionnel)
- Serveur SMTP pour l'envoi d'emails

## 🛠️ Installation

1. **Cloner le repository**
```bash
git clone <url-du-repo>
cd smart_watch
```

2. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

3. **Configuration environnement**
Créer un fichier `.env` :
```env
# LLM Configuration
API_KEY_LOCAL=votre_cle_api_locale
API_KEY_MISTRAL=votre_cle_mistral

# Email Configuration
MAIL_EMETTEUR=emetteur@example.com
MAIL_RECEPTEUR=recepteur@example.com
MDP_EMETTEUR=mot_de_passe_emetteur
SMTP_SERVER=smtp.example.com
SMTP_PORT=587
```

4. **Préparer les données**
Placer votre fichier CSV dans le dossier `data/` avec les colonnes :
- `identifiant` : ID unique du lieu
- `nom` : Nom de l'établissement
- `type_lieu` : Type (Mairie, École, etc.)
- `url` : URL à analyser

## 🎮 Utilisation

### Lancement standard
```bash
python main.py
```

### Configuration avancée
Modifier les variables dans `main.py` :

```python
# Fichier de données
NOM_FIC = "alerte_modif_horaire_lieu"

# Choix du LLM
LLM = "mistral"  # "local" ou "mistral"
MODELE_LLM = "mistral-large-latest"
```

## 📊 Format des Données de Sortie

### Schéma JSON des Horaires
```json
{
  "horaires_lieux_publics": {
    "metadata": {
      "identifiant": "LIEU_001",
      "nom": "Mairie du 1er",
      "type_lieu": "Mairie",
      "url": "https://example.com"
    },
    "periodes": {
      "hors_vacances_scolaires": {
        "active": true,
        "horaires": {
          "lundi": {
            "ouvert": true,
            "creneaux": [
              {"debut": "08:30", "fin": "12:00"},
              {"debut": "14:00", "fin": "17:00"}
            ]
          }
        }
      }
    },
    "generation_osm": {
      "opening_hours_osm": "Mo-Fr 08:30-12:00,14:00-17:00"
    },
    "extraction_info": {
      "source_found": true,
      "confidence": 0.95
    }
  }
}
```

### Base de Données SQLite
Le système génère automatiquement une base SQLite avec :
- **Table principale** : Toutes les données d'URLs et horaires
- **Colonnes** : `identifiant`, `nom`, `type_lieu`, `url`, `statut`, `message`, `code_http`, `markdown`, `horaires_llm`

## 🔧 Modules Principaux

### `core/LLMClient.py`
- Clients unifiés pour différents LLMs
- Support des réponses structurées (JSON Schema)
- Gestion d'erreurs et timeouts

### `core/URLRetriever.py`
- Récupération robuste avec gestion SSL/TLS
- Conversion HTML vers Markdown
- Gestion des encodages et redirections

### `core/GenererRapportHTML.py`
- Templates Jinja2 pour rapports HTML
- Statistiques automatiques et graphiques
- Interface interactive avec JavaScript

## 📈 Statuts de Traitement

| Statut | Description | Icône |
|--------|-------------|-------|
| `ok` | URL accessible, horaires extraits | ✅ |
| `warning` | URL accessible, problèmes mineurs | ⚠️ |
| `critical` | URL inaccessible, erreur critique | ❌ |
| `unknown` | Statut indéterminé | ❓ |

## 🤝 Contribution

1. Fork du projet
2. Créer une branche feature (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Commit des changements (`git commit -am 'Ajout nouvelle fonctionnalité'`)
4. Push vers la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Créer une Pull Request

## 📝 Licence

Ce projet est sous licence GNU GPL. Voir le fichier `LICENSE` pour plus de détails.

## 🆘 Support

Pour obtenir de l'aide :
1. Consulter la documentation dans les commentaires du code
2. Vérifier les logs de sortie pour les erreurs
3. Ouvrir une issue sur GitHub avec les détails de votre problème

## 🔮 Roadmap

- [ ] Comparaison d'horaires pour vérifier l'adéquation entre sources
- [ ] Récupération des sites par API sur data.grandlyon.fr
- [ ] Interface Gradio pour configuration et monitoring