# Constructeur de prompts pour l'extraction d'horaires d'ouverture
# Documentation : https://datagora-erasme.github.io/smart_watch/source/modules/core/GetPrompt.html

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from .Logger import create_logger

# Initialize logger for this module
logger = create_logger(
    module_name="GetPrompt",
)


def get_prompt(
    row: Dict[str, Any], json_schema: Optional[Dict[str, Any]] = None
) -> List[Dict[str, str]]:
    """
    Construit le prompt pour l'extraction d'horaires d'ouverture.

    Le schéma JSON est injecté dans le prompt pour guider le LLM.

    Args:
        row (Dict[str, Any]): Dictionnaire contenant les informations du lieu.
        json_schema (Optional[Dict[str, Any]]): Le schéma JSON à suivre pour
            la réponse.

    Returns:
        List[Dict[str, str]]: Liste des messages pour le LLM.
    """
    identifiant = row.get("identifiant", "N/A")
    nom_lieu = row.get("nom", "inconnu")

    logger.debug(f"*{identifiant}* Construction du prompt pour '{nom_lieu}'")

    system_prompt = f"""Tu es un expert en extraction d'horaires d'ouverture à partir de texte.
Ton objectif est d'analyser le contenu Markdown fourni, et d'extraire les horaires en respectant rigoureusement la structure JSON fournie.
- N'invente aucune information. Si une donnée est manquante, ne la mets pas dans le JSON.
- Si aucun horaire ou jour de fermeture n'est trouvé, retourne un JSON avec "ouvert" à false et des listes de créneaux vides.
- les occurences spécifiques (1er lundi du mois, 1er et 3eme mardi du mois, dernier samedi du mois, etc.) doivent être récupérées dans le champ "occurences" du JSON.
- le format des dates doit être "YYYY-MM-DD" pour les dates spécifiques et "YYYY-MM" pour les mois.
- le format des horaires doit être "HH:MM".
- L'année de référence pour les dates sans année est {datetime.now().year}.
- les jours spéciaux (Noël, Jour de l'An, etc.) doivent être récupérés dans le champ "jours_speciaux" du JSON et leur date précise doit être indiquée.
- Ne t'arrête pas lorsque tu passes sur un premier jeu d'horaires, mais analyse l'intégralité du texte reçu.
- S'il y a plusieurs jeux d'horaires, ne fais aucun mélange entre eux, il faut en choisir un seul.
- Pour t'aider à choisir le bon, analyse le contexte de chacun d'eux et utilise le type et nom du lieu fournis dans le prompt utilisateur pour choisir celui qui correspond.
- S'il y a plusieurs jeux contradictoires pour un même lieu, prends le jeu le plus complet.
- Réponds UNIQUEMENT avec le JSON, sans aucun texte ou formatage supplémentaire.
"""

    # Construction du prompt utilisateur
    user_prompt_content = f"""Extrait du Markdown qui suit les horaires et conditions d'ouverture pour la {row.get("type_lieu", "")} nommée "{row.get("nom", "Non renseigné")}".

### Markdown à analyser
```markdown
{row.get("markdown", "Aucun contenu disponible")}
```
"""

    # Ajout du schéma JSON au prompt si fourni
    if json_schema:
        schema_str = json.dumps(json_schema, indent=2, ensure_ascii=False)
        user_prompt_content += f"""
### Format de sortie JSON attendu
Réponds en utilisant exclusivement le format JSON suivant. Respecte scrupuleusement ce schéma :
```json
{schema_str}
```
"""
        logger.debug(
            f"*{identifiant}* Schéma JSON ajouté au prompt pour '{row.get('nom', 'inconnu')}'"
        )
    else:
        user_prompt_content += "\nRéponds uniquement avec la structure JSON demandée."
        logger.warning(
            f"*{identifiant}* Aucun schéma JSON fourni pour '{row.get('nom', 'inconnu')}'"
        )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt_content},
    ]

    logger.debug(
        f"*{identifiant}* Prompt construit pour '{row.get('nom', 'inconnu')}' : {len(messages)} messages"
    )
    return messages
