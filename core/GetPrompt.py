def get_prompt(row: dict) -> list:
    """
    Construit le prompt pour l'extraction d'horaires d'ouverture avec structure JSON complète.

    Args:
        row: Dictionnaire contenant les informations du lieu

    Returns:
        list: Liste des messages pour le LLM
    """
    system_prompt = """Tu es un expert en extraction de périodes et d'horaires d'ouverture et de fermeture pour des lieux publics.

Ton objectif est d'analyser le contenu markdown fourni et d'extraire ces périodes et horaires en utilisant la structure JSON définie.

INSTRUCTIONS IMPORTANTES :
1. Analyse minutieusement le contenu pour extraire toutes les informations en lien avec l'ouverture ou la fermeture du lieu indiqué dans "informations du lieu"
2. Tu dois extraire les périodes d'ouverture avec les horaires correspondants, et les indiquer dans chaque section appropriée du JSON.
3. Tu dois extraire les périodes de fermeture éventuelles, y compris les jours fériés, les jours spéciaux et les vacances scolaires, et les indiquer dans chaque section appropriée du JSON.
4. Les périodes et horaires trouvés doivent être classés dans une des sections suivantes :
- hors_vacances_scolaires
- vacances_scolaires_ete
- petites_vacances_scolaires
- jours_feries
- jours_speciaux
5. La période vacances_scolaires_ete désigne les vacances d'été (juillet-août), petites_vacances_scolaires désigne les vacances de Toussaint, Noël, Hiver et Printemps
6. Les jours fériés et les jours spéciaux doivent être identifiés avec des dates précises si disponibles.
7. Rempli la balise "source_found" avec True si tu trouves des horaires, avec False sinon.
8. Indique ton niveau de confiance dans extraction_info.confidence (0.0 à 1.0)
9. Réponds UNIQUEMENT avec le JSON, sans texte supplémentaire
10. N'invente aucune information, utilise uniquement les données fournies. Si aucun horaire n'est trouvé, n'invente rien et mets source_found à False et confidence à 0.0
11. Si le lieu est fermé de manière permanente, indique-le clairement dans la section "hors_vacances_scolaires"

SOIS PRÉCIS ET NE FAIS PAS D'HALLUCINATIONS."""

    user_prompt = f"""Analyse le contenu suivant pour extraire les périodes et horaires d'ouverture et de fermeture :

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
