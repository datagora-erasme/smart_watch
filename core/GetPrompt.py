def get_prompt(row: dict) -> list:
    """
    Construit le prompt pour l'extraction d'horaires d'ouverture avec structure JSON complète.

    Args:
        row: Dictionnaire contenant les informations du lieu

    Returns:
        list: Liste des messages pour le LLM
    """
    system_prompt = """Tu es un expert en extraction d'horaires d'ouverture et de fermeture pour des lieux publics.

Ton objectif est d'analyser le contenu markdown fourni et d'extraire les horaires d'ouverture et de fermeture en utilisant la structure JSON définie.

INSTRUCTIONS IMPORTANTES :
1. Analyse minutieusement le contenu pour identifier les horaires d'ouverture et de fermeture du lieu indiqué dans "informations du lieu"
2. Utilise la structure JSON fournie dans le schéma de réponse
3. Remplis au minimum la section "hors_vacances_scolaires" avec les horaires normaux
4. Si tu trouves des horaires spéciaux d'ouverture, quelque soit la période, ajoute les dans vacances d'été, ou vacances hors été, ou jours fériés, ou jours spéciaux
5. Si tu trouves des jours spéciaux de fermeture, ajoute-les dans la section jours_speciaux
6. Indique ton niveau de confiance dans extraction_info.confidence (0.0 à 1.0)
7. Si aucun horaire n'est trouvé, n'invente rien et mets source_found à false et confidence à 0.0
8. Réponds UNIQUEMENT avec le JSON, sans texte supplémentaire
9. N'invente aucune information, utilise uniquement les données fournies
10. Si le lieu est fermé de manière permanente, indique-le clairement dans la section "hors_vacances_scolaires"

SOIS PRÉCIS ET NE FAIS PAS D'HALLUCINATIONS."""

    user_prompt = f"""Analyse le contenu suivant pour extraire les horaires d'ouverture :

INFORMATIONS DU LIEU :
- Identifiant : {row.get("identifiant", "Non renseigné")}
- Nom : {row.get("nom", "Non renseigné")}
- Type de lieu : {row.get("type_lieu", "Non renseigné")}
- URL : {row.get("url", "Non renseignée")}

CONTENU À ANALYSER :
{row.get("markdown", "Aucun contenu disponible")}

Réponds uniquement avec la structure JSON demandée."""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
