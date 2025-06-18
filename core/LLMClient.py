import os
import signal
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

import requests


@dataclass
class LLMMessage:
    """Représente un message dans une conversation avec le LLM."""

    role: str  # "user", "assistant", "system"
    content: str


class llm_openai:
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
            api_key: Clé API (utilise OPENAI_API_KEY par défaut)
            model: Nom du modèle à utiliser
            base_url: URL de base pour l'API
            temperature: Paramètre de température pour la génération
            timeout: Timeout en secondes pour les requêtes
        """
        self.model = model
        self.temperature = temperature
        self.timeout = timeout

        self.api_key = api_key or os.environ.get("API_KEY_LOCAL")
        self.base_url = (base_url or "https://api.openai.com/v1").rstrip("/")

        # Configuration de la session requests
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

        if self.api_key:
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})

    def call_llm(
        self,
        messages: List[Union[Dict[str, str], LLMMessage]],
        response_format: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Effectue un appel au LLM.

        Args:
            messages: Liste des messages de la conversation
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
            payload = {
                "model": self.model,
                "messages": formatted_messages,
                "temperature": self.temperature,
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


class TimeoutError(Exception):
    """Exception levée en cas de timeout."""

    pass


@contextmanager
def timeout_handler(seconds):
    """Context manager pour gérer les timeouts manuellement."""

    # SIGALRM n'est pas disponible sur Windows
    if sys.platform == "win32":
        # Sur Windows, on utilise juste un yield sans timeout
        yield
    else:

        def timeout_signal_handler(signum, frame):
            raise TimeoutError(f"Timeout après {seconds} secondes")

        # Sauvegarder l'ancien handler
        old_handler = signal.signal(signal.SIGALRM, timeout_signal_handler)
        signal.alarm(seconds)

        try:
            yield
        finally:
            # Restaurer l'ancien handler et annuler l'alarme
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
        signal.signal(signal.SIGALRM, old_handler)


class llm_mistral:
    """
    Client pour interagir avec l'API Mistral AI via des requêtes HTTP directes.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "mistral-large-latest",
        temperature: float = 0.1,
        random_seed: int = 1,
        timeout: int = 30,
    ):
        """
        Initialise le client Mistral.

        Args:
            api_key: Clé API Mistral (utilise MISTRAL_API_KEY par défaut)
            model: Nom du modèle Mistral à utiliser
            temperature: Paramètre de température pour la génération
            random_seed: Graine aléatoire pour la reproductibilité
            timeout: Timeout en secondes pour les requêtes
        """
        self.model = model
        self.temperature = temperature
        self.random_seed = random_seed
        self.timeout = timeout
        self.base_url = "https://api.mistral.ai/v1"

        api_key = api_key or os.environ.get("API_KEY_MISTRAL")
        if not api_key:
            raise ValueError("Clé API Mistral requise (MISTRAL_API_KEY)")

        # Configuration de la session requests
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            }
        )

    def call_llm(
        self,
        messages: List[Union[Dict[str, str], LLMMessage]],
        tool_params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Effectue un appel au LLM Mistral, en utilisant le tool calling pour une sortie structurée.

        Args:
            messages: Liste des messages de la conversation.
            tool_params: Paramètres pour le tool calling (contenant `tools` et `tool_choice`).

        Returns:
            str: Réponse du LLM, soit le contenu du message, soit les arguments de l'outil appelé.

        Raises:
            Exception: En cas d'erreur lors de l'appel au LLM.
        """
        # Normaliser les messages en une liste de dictionnaires
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, LLMMessage):
                formatted_messages.append({"role": msg.role, "content": msg.content})
            else:
                formatted_messages.append(msg)

        try:
            # Préparer le payload de la requête
            payload = {
                "model": self.model,
                "messages": formatted_messages,
                "temperature": self.temperature,
                "random_seed": self.random_seed,
            }

            # Ajouter les paramètres de tool calling si fournis
            if tool_params:
                payload.update(tool_params)

            url = f"{self.base_url}/chat/completions"
            response = self.session.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()

            response_data = response.json()
            choice = response_data["choices"][0]

            # Vérifier si le modèle a appelé un outil
            if "tool_calls" in choice["message"] and choice["message"]["tool_calls"]:
                return choice["message"]["tool_calls"][0]["function"]["arguments"]
            else:
                return choice["message"]["content"]

        except requests.exceptions.Timeout:
            raise Exception(f"Timeout après {self.timeout} secondes")
        except requests.exceptions.ConnectionError:
            raise Exception(f"Impossible de se connecter à {self.base_url}")
        except requests.exceptions.HTTPError:
            raise Exception(f"Erreur HTTP {response.status_code}: {response.text}")
        except (KeyError, IndexError) as e:
            raise Exception(f"Structure de réponse inattendue: {e}")

    def send_message(
        self,
        content: str,
        role: str = "user",
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Envoie un message simple au LLM Mistral et retourne la réponse.

        Args:
            content: Le contenu du message à envoyer
            role: Le rôle du message ("user" par défaut)
            system_prompt: Prompt système optionnel

        Returns:
            str: La réponse textuelle du LLM
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": role, "content": content})

        return self.call_llm(messages)

    def conversation(self, messages: List[Union[Dict, LLMMessage]]) -> str:
        """
        Méthode de convenance pour une conversation complète.

        Args:
            messages: Liste de messages de la conversation

        Returns:
            str: La réponse textuelle du LLM
        """
        return self.call_llm(messages)


# Fonctions utilitaires pour les formats de réponse structurés
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


def get_mistral_tool_format(
    schema: Dict[str, Any], function_name: str = "extract_info"
) -> Dict[str, Any]:
    """
    Crée le dictionnaire pour le tool calling avec Mistral, forçant une réponse structurée.

    Args:
        schema: Le schéma JSON que la réponse doit suivre.
        function_name: Le nom de la fonction fictive à appeler.

    Returns:
        Dict: Dictionnaire contenant les `tools` et `tool_choice` pour l'API Mistral.
    """
    return {
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": function_name,
                    "description": "Extraire les informations structurées du texte en suivant le schéma JSON.",
                    "parameters": schema,
                },
            }
        ],
        "tool_choice": "any",  # Force le modèle à appeler l'outil
    }
