import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import requests
from mistralai import Mistral


@dataclass
class LLMMessage:
    """Représente un message dans une conversation avec le LLM."""

    role: str  # "user", "assistant", "system"
    content: str


class llm_local:
    """
    Client pour interagir avec des API compatibles OpenAI.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemma3",
        base_url: Optional[str] = None,
        temperature: float = 0.1,
        timeout: int = 30,
    ):
        """
        Initialise le client LLM.

        Args:
            api_key: Clé API (utilise LLM_API_KEY par défaut)
            model: Nom du modèle à utiliser
            base_url: URL de base pour l'API
            temperature: Paramètre de température pour la génération
            timeout: Timeout en secondes pour les requêtes
        """
        self.model = model
        self.temperature = temperature
        self.timeout = timeout

        self.api_key = api_key or os.environ.get("LLM_API_KEY")
        self.base_url = (base_url or "https://api.erasme.homes/v1").rstrip("/")

        # Configuration de la session requests
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

        if self.api_key:
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})

    def call_llm(
        self,
        messages: List[Union[Dict[str, str], LLMMessage]],
        model_override: Optional[str] = None,
        temperature_override: Optional[float] = None,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Effectue un appel au LLM.

        Args:
            messages: Liste des messages de la conversation
            model_override: Modèle à utiliser pour cet appel spécifique
            temperature_override: Température pour cet appel spécifique
            response_format: Format de réponse structuré (OpenAI format)

        Returns:
            str: Réponse du LLM

        Raises:
            Exception: En cas d'erreur lors de l'appel au LLM
        """
        # Normaliser les messages
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, LLMMessage):
                formatted_messages.append({"role": msg.role, "content": msg.content})
            else:
                formatted_messages.append(msg)

        try:
            payload = {
                "model": model_override or self.model,
                "messages": formatted_messages,
                "temperature": temperature_override or self.temperature,
            }

            # Ajouter le format de réponse structuré si fourni
            if response_format:
                payload["response_format"] = response_format

            url = f"{self.base_url}/chat/completions"
            response = self.session.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()

            response_data = response.json()
            return response_data["choices"][0]["message"]["content"]

        except requests.exceptions.Timeout:
            raise Exception(f"Timeout après {self.timeout} secondes")
        except requests.exceptions.ConnectionError:
            raise Exception(f"Impossible de se connecter à {url}")
        except requests.exceptions.HTTPError:
            raise Exception(f"Erreur HTTP {response.status_code}: {response.text}")
        except (KeyError, IndexError) as e:
            raise Exception(f"Structure de réponse inattendue: {e}")

    def send_message(
        self,
        content: str,
        role: str = "user",
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        Envoie un message simple au LLM et retourne la réponse.

        Args:
            content: Le contenu du message à envoyer
            role: Le rôle du message ("user" par défaut)
            system_prompt: Prompt système optionnel
            **kwargs: Arguments supplémentaires pour call_llm

        Returns:
            str: La réponse textuelle du LLM
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": role, "content": content})

        return self.call_llm(messages, **kwargs)

    def conversation(self, messages: List[Union[Dict, LLMMessage]], **kwargs) -> str:
        """
        Méthode de convenance pour une conversation complète.

        Args:
            messages: Liste de messages de la conversation
            **kwargs: Arguments supplémentaires pour call_llm

        Returns:
            str: La réponse textuelle du LLM
        """
        return self.call_llm(messages, **kwargs)


class llm_mistral:
    """
    Client pour interagir avec l'API Mistral AI en utilisant la librairie officielle.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "mistral-large-latest",
        temperature: float = 0.1,
        random_seed: int = 1,
    ):
        """
        Initialise le client Mistral.

        Args:
            api_key: Clé API Mistral (utilise MISTRAL_API_KEY par défaut)
            model: Nom du modèle Mistral à utiliser
            temperature: Paramètre de température pour la génération
            random_seed: Graine aléatoire pour la reproductibilité
        """
        self.model = model
        self.temperature = temperature
        self.random_seed = random_seed

        api_key = api_key or os.environ.get("MISTRAL_API_KEY")
        if not api_key:
            raise ValueError("Clé API Mistral requise (MISTRAL_API_KEY)")

        # Initialiser le client Mistral officiel
        self.client = Mistral(api_key=api_key)

    def call_llm(
        self,
        messages: List[Union[Dict[str, str], LLMMessage]],
        model_override: Optional[str] = None,
        temperature_override: Optional[float] = None,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Effectue un appel au LLM Mistral.

        Args:
            messages: Liste des messages de la conversation
            model_override: Modèle à utiliser pour cet appel spécifique
            temperature_override: Température pour cet appel spécifique
            response_format: Format de réponse structuré

        Returns:
            str: Réponse du LLM

        Raises:
            Exception: En cas d'erreur lors de l'appel au LLM
        """
        # Normaliser les messages
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, LLMMessage):
                formatted_messages.append({"role": msg.role, "content": msg.content})
            else:
                formatted_messages.append(msg)

        try:
            # Préparer les paramètres
            kwargs = {
                "model": model_override or self.model,
                "messages": formatted_messages,
                "temperature": temperature_override or self.temperature,
                "random_seed": self.random_seed,
            }

            # Ajouter le format de réponse structuré si fourni
            if response_format:
                kwargs["response_format"] = response_format

            # Effectuer l'appel avec la librairie officielle
            response = self.client.chat.complete(**kwargs)

            return response.choices[0].message.content

        except Exception as e:
            raise Exception(f"Erreur lors de l'appel à Mistral: {e}")

    def send_message(
        self,
        content: str,
        role: str = "user",
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        Envoie un message simple au LLM Mistral et retourne la réponse.

        Args:
            content: Le contenu du message à envoyer
            role: Le rôle du message ("user" par défaut)
            system_prompt: Prompt système optionnel
            **kwargs: Arguments supplémentaires pour call_llm

        Returns:
            str: La réponse textuelle du LLM
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": role, "content": content})

        return self.call_llm(messages, **kwargs)

    def conversation(self, messages: List[Union[Dict, LLMMessage]], **kwargs) -> str:
        """
        Méthode de convenance pour une conversation complète.

        Args:
            messages: Liste de messages de la conversation
            **kwargs: Arguments supplémentaires pour call_llm

        Returns:
            str: La réponse textuelle du LLM
        """
        return self.call_llm(messages, **kwargs)


# Fonctions utilitaires pour créer des formats de réponse structurés
def create_json_schema(
    properties: Dict[str, Any], required: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Crée un schéma JSON pour les structured outputs OpenAI-compatible.

    Args:
        properties: Propriétés du schéma JSON
        required: Liste des champs requis

    Returns:
        Dict: Schéma JSON formaté pour OpenAI
    """
    schema = {"type": "object", "properties": properties, "additionalProperties": False}

    if required:
        schema["required"] = required

    return schema


def load_opening_hours_schema_template() -> Dict[str, Any]:
    """
    Charge le template de schéma JSON depuis le fichier assets.

    Returns:
        Dict: Schéma JSON pour les horaires chargé depuis le fichier template

    Raises:
        FileNotFoundError: Si le fichier template n'est pas trouvé
        json.JSONDecodeError: Si le fichier JSON est malformé
    """
    # Chemin vers le fichier template
    current_dir = Path(__file__).parent.parent
    template_path = current_dir / "assets" / "opening_hours_schema_template.json"

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        return schema
    except FileNotFoundError:
        raise FileNotFoundError(f"Fichier template non trouvé : {template_path}")
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Erreur de format JSON dans {template_path}: {e}")


def create_opening_hours_schema() -> Dict[str, Any]:
    """
    Crée un schéma spécifique pour l'extraction d'horaires d'ouverture.
    Basé sur le template JSON du fichier assets/opening_hours_schema_template.json

    Returns:
        Dict: Schéma JSON pour les horaires
    """
    try:
        return load_opening_hours_schema_template()
    except (FileNotFoundError, json.JSONDecodeError) as e:
        # Fallback vers un schéma simple en cas d'erreur
        print(f"Attention: Erreur lors du chargement du template schema - {e}")
        print("Utilisation d'un schéma simplifié de fallback.")

        return create_json_schema(
            {
                "horaires_lieux_publics": {
                    "type": "object",
                    "properties": {
                        "metadata": {
                            "type": "object",
                            "properties": {
                                "identifiant": {"type": "string"},
                                "nom": {"type": "string"},
                                "type_lieu": {"type": "string"},
                                "url": {"type": "string"},
                            },
                            "required": ["identifiant", "nom", "type_lieu", "url"],
                        },
                        "generation_osm": {
                            "type": "object",
                            "properties": {
                                "opening_hours_osm": {
                                    "type": "string",
                                    "description": "Horaires au format OSM final",
                                }
                            },
                            "required": ["opening_hours_osm"],
                        },
                        "extraction_info": {
                            "type": "object",
                            "properties": {
                                "source_found": {
                                    "type": "boolean",
                                    "description": "Indique si des horaires ont été trouvés",
                                },
                                "notes": {"type": "string"},
                            },
                            "required": ["source_found"],
                        },
                    },
                    "required": ["metadata", "generation_osm", "extraction_info"],
                }
            },
            required=["horaires_lieux_publics"],
        )


def create_json_schema_with_definitions(
    properties: Dict[str, Any],
    definitions: Optional[Dict[str, Any]] = None,
    required: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Crée un schéma JSON avec des définitions réutilisables.

    Args:
        properties: Propriétés du schéma JSON
        definitions: Définitions réutilisables
        required: Liste des champs requis

    Returns:
        Dict: Schéma JSON formaté avec définitions
    """
    schema = {"type": "object", "properties": properties, "additionalProperties": False}

    if required:
        schema["required"] = required

    if definitions:
        schema["definitions"] = definitions

    return schema


def get_opening_hours_definitions() -> Dict[str, Any]:
    """
    Retourne les définitions réutilisables pour les horaires.

    Returns:
        Dict: Définitions JSON pour les horaires
    """
    return {
        "creneau_horaire": {
            "type": "object",
            "properties": {
                "debut": {
                    "type": "string",
                    "pattern": "^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$",
                    "description": "Heure de début au format HH:MM",
                },
                "fin": {
                    "type": "string",
                    "pattern": "^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$",
                    "description": "Heure de fin au format HH:MM",
                },
            },
            "additionalProperties": False,
            "required": ["debut", "fin"],
        },
        "horaires_jour": {
            "type": "object",
            "properties": {
                "active": {
                    "type": "boolean",
                    "default": True,
                    "description": "Indique si ce jour est pris en compte",
                },
                "ouvert": {
                    "type": "boolean",
                    "description": "Indique si le lieu est ouvert ce jour",
                },
                "creneaux": {
                    "type": "array",
                    "items": {"$ref": "#/definitions/creneau_horaire"},
                    "description": "Liste des créneaux d'ouverture",
                },
            },
            "additionalProperties": False,
            "required": ["active", "ouvert", "creneaux"],
        },
        "horaires_hebdomadaires": {
            "type": "object",
            "properties": {
                "lundi": {"$ref": "#/definitions/horaires_jour"},
                "mardi": {"$ref": "#/definitions/horaires_jour"},
                "mercredi": {"$ref": "#/definitions/horaires_jour"},
                "jeudi": {"$ref": "#/definitions/horaires_jour"},
                "vendredi": {"$ref": "#/definitions/horaires_jour"},
                "samedi": {"$ref": "#/definitions/horaires_jour"},
                "dimanche": {"$ref": "#/definitions/horaires_jour"},
            },
            "additionalProperties": False,
        },
    }


def create_complete_opening_hours_schema() -> Dict[str, Any]:
    """
    Crée le schéma complet pour l'extraction d'horaires.
    Utilise le template JSON avec toutes les définitions incluses.

    Returns:
        Dict: Schéma JSON complet chargé depuis le template
    """
    return create_opening_hours_schema()


def get_structured_response_format(
    schema: Dict[str, Any], name: str = "response"
) -> Dict[str, Any]:
    """
    Formate un schéma pour les structured outputs OpenAI.

    Args:
        schema: Le schéma JSON
        name: Nom du schéma

    Returns:
        Dict: Format de réponse pour l'API
    """
    return {
        "type": "json_schema",
        "json_schema": {"name": name, "strict": True, "schema": schema},
    }


def get_mistral_response_format(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Formate un schéma pour les structured outputs Mistral.

    Args:
        schema: Le schéma JSON

    Returns:
        Dict: Format de réponse pour l'API Mistral
    """
    return {
        "type": "json_object",
    }


# Exemple d'utilisation
if __name__ == "__main__":
    # Test Local
    try:
        local_client = llm_local(base_url="https://api.erasme.homes/v1", model="gemma3")
        response = local_client.send_message("Écris-moi un haiku")
        print("Réponse Local:", response)
    except Exception as e:
        print(f"Erreur Local: {e}")

    # Test Mistral
    try:
        mistral_client = llm_mistral(model="mistral-large-latest")
        response = mistral_client.send_message("Écris-moi un haiku")
        print("Réponse Mistral:", response)
    except Exception as e:
        print(f"Erreur Mistral: {e}")
