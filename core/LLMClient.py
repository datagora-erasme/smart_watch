import os
import signal
import sys
from contextlib import contextmanager
from dataclasses import dataclass
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
    Client pour interagir avec l'API Mistral AI en utilisant la librairie officielle.
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

            # Effectuer l'appel avec gestion manuelle du timeout
            with timeout_handler(self.timeout):
                response = self.client.chat.complete(**kwargs)

            return response.choices[0].message.content

        except TimeoutError:
            raise Exception(f"Timeout après {self.timeout} secondes")
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
