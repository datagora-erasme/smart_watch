import json
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from core.Logger import LogOutput, create_logger

# Charger la variable d'environnement pour le nom du fichier log
load_dotenv()
csv_name = os.getenv("CSV_URL_HORAIRES")

# Initialize logger for this module
logger = create_logger(
    outputs=[LogOutput.CONSOLE, LogOutput.FILE],
    log_file=Path(__file__).parent.parent / "logs" / f"{csv_name}.log",
    module_name="GetPrompt",
)


def get_prompt(row: dict, json_schema: dict = None) -> list:
    """
    Construit le prompt pour l'extraction d'horaires d'ouverture.
    Le schéma JSON est injecté dans le prompt pour guider le LLM.

    Args:
        row: Dictionnaire contenant les informations du lieu.
        json_schema: Le schéma JSON à suivre pour la réponse.

    Returns:
        list: Liste des messages pour le LLM.
    """
    logger.debug(f"Construction prompt pour: {row.get('nom', 'inconnu')}")

    system_prompt = f"""Tu es un expert en extraction d'horaires d'ouverture à partir de texte.
Ton objectif est d'analyser le contenu markdown fourni et d'extraire les horaires en respectant rigoureusement la structure JSON fournie.
- N'invente aucune information. Si une information n'est pas présente, ne la mets pas dans le JSON.
- Si aucun horaire ou jour de fermeture n'est trouvé, retourne un JSON avec "ouvert" à false et des listes de créneaux vides.
- les occurences spécifiques (1er lundi du mois, 1er et 3eme mardi du mois, dernier samedi du mois, etc.) doivent être récupérées dans le champ "occurences" du JSON.
- le format des dates doit être "YYYY-MM-DD" pour les dates spécifiques et "YYYY-MM" pour les mois.
- L'année de référence pour les dates sans année est {datetime.now().year}.
- Réponds UNIQUEMENT avec le JSON, sans aucun texte ou formatage supplémentaire.
"""

    # Construction du prompt utilisateur
    user_prompt_content = f"""Analyse le contenu markdown suivant pour le lieu "{row.get("nom", "Non renseigné")}" et extrais les horaires d'ouverture.

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
        logger.debug("Schéma JSON ajouté au prompt")
    else:
        user_prompt_content += "\nRéponds uniquement avec la structure JSON demandée."
        logger.warning("Aucun schéma JSON fourni")

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt_content},
    ]

    logger.debug(f"Prompt construit: {len(messages)} messages")
    return messages
