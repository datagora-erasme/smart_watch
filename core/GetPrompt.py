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
1. Analyse minutieusement le contenu pour extraire toutes les informations en lien avec l'ouverture ou la fermeture du lieu indiqué dans "informations du lieu".
2. Extrait les périodes d'ouverture avec les horaires correspondants, et indique-les dans chaque section appropriée du JSON.
3. Extrait les périodes de fermeture éventuelles, y compris les jours fériés, les jours spéciaux et les vacances scolaires, et indique-les dans chaque section appropriée du JSON.
4. Les périodes et horaires trouvés doivent être classés dans une des sections suivantes :
   - hors_vacances_scolaires
   - vacances_scolaires_ete
   - petites_vacances_scolaires
   - jours_feries
   - jours_speciaux
5. La période "vacances_scolaires_ete" désigne les vacances d'été (juillet-août), "petites_vacances_scolaires" désigne les vacances de Toussaint, Noël, Hiver et Printemps.
6. Les jours fériés et les jours spéciaux doivent être identifiés avec des dates précises si disponibles.
7. Remplis la balise "source_found" avec True si des informations pertinentes (horaires ou fermetures) sont trouvées, avec False uniquement si aucune information pertinente n'est trouvée.
8. Indique ton niveau de confiance dans "extraction_info.confidence" (0.0 à 1.0).
9. Réponds UNIQUEMENT avec le JSON, sans texte supplémentaire.
10. N'invente aucune information, utilise uniquement les données fournies. Si aucun horaire n'est trouvé, n'invente rien et mets "source_found" à False et "confidence" à 0.0.
11. Si le lieu est fermé de manière permanente, indique-le clairement dans la section "hors_vacances_scolaires".
12. Si des jours de fermeture sont explicitement précisés, "source_found" doit être mis à True.
13. Prends en compte les cas où un lieu peut être ouvert seulement une partie de la journée (par exemple, ouvert le matin mais fermé l'après-midi). Assure-toi de bien noter ces différences dans les horaires d'ouverture.
14. En cas de doublon incohérent dans les horaires (deux ou plusieurs horaires différents pour le même jour), prend un seul horaire, celui qui est le plus proche du lieu indiqué dans "informations du lieu", et met "confidence" à 0.5.

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
