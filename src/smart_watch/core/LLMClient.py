import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

import requests
from codecarbon import EmissionsTracker

from .ErrorHandler import ErrorCategory, ErrorHandler, ErrorSeverity, handle_errors
from .Logger import create_logger

# Initialize logger for this module
logger = create_logger(
    module_name="LLMClient",
)


@dataclass
class LLMResponse:
    """Réponse enrichie d'un appel LLM avec mesure de consommation."""

    content: str
    co2_emissions: float  # En kg CO2


@dataclass
class LLMMessage:
    """Représente un message dans une conversation avec le LLM."""

    role: str  # "user", "assistant", "system"
    content: str


class BaseLLMClient(ABC):
    """Classe de base abstraite pour les clients LLM."""

    def __init__(
        self,
        model: str,
        temperature: float,
        timeout: int,
        api_key: Optional[str],
        base_url: Optional[str],
    ):
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        self.api_key = api_key
        self.base_url = base_url.rstrip("/") if base_url else None
        self.session = self._create_session()
        self.error_handler = ErrorHandler()

        logger.debug(
            f"Client {self.__class__.__name__} initialisé pour le modèle {self.model}"
        )

    def _create_session(self) -> requests.Session:
        """Crée et configure une session requests."""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        if self.api_key:
            session.headers.update({"Authorization": f"Bearer {self.api_key}"})
        return session

    def _normalize_messages(
        self, messages: List[Union[Dict, LLMMessage]]
    ) -> List[Dict]:
        """Normalise les messages au format dictionnaire."""
        return [
            {"role": msg.role, "content": msg.content}
            if isinstance(msg, LLMMessage)
            else msg
            for msg in messages
        ]

    @abstractmethod
    def call_llm(
        self, messages: List[Union[Dict, LLMMessage]], **kwargs
    ) -> LLMResponse:
        """Méthode abstraite pour effectuer un appel au LLM avec mesure d'émissions."""
        pass

    def send_message(
        self,
        content: str,
        role: str = "user",
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> LLMResponse:
        """Envoie un message simple au LLM."""
        messages = []
        if system_prompt:
            messages.append(LLMMessage(role="system", content=system_prompt))
        messages.append(LLMMessage(role=role, content=content))
        return self.call_llm(messages, **kwargs)

    def conversation(
        self, messages: List[Union[Dict, LLMMessage]], **kwargs
    ) -> LLMResponse:
        """Raccourci pour `call_llm`."""
        return self.call_llm(messages, **kwargs)

    def call_embeddings(self, texts: List[str]) -> LLMResponse:
        """Appel d'embeddings avec mesure d'émissions."""
        # Créer un tracker à la volée pour une mesure isolée
        tracker = EmissionsTracker(
            measure_power_secs=1,
            tracking_mode="machine",
            log_level="error",
        )
        tracker.start()

        try:
            # URL de l'endpoint embeddings
            url = f"{self.base_url}/embeddings"

            # Préparer la requête
            payload = {
                "model": self.model,
                "input": texts,
            }

            response = self.session.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()

            result = response.json()
            embeddings = [data["embedding"] for data in result["data"]]

            # Arrêter le tracking et récupérer les émissions
            emissions = tracker.stop()
            logger.debug(
                f"Embeddings API: {len(embeddings)} vecteurs, {emissions:.6f} kg CO2"
            )

            return LLMResponse(content=embeddings, co2_emissions=emissions)

        except Exception as e:
            # S'assurer que le tracker est arrêté même en cas d'erreur
            tracker.stop()
            logger.error(f"Erreur calcul embeddings: {e}")
            raise


class OpenAICompatibleClient(BaseLLMClient):
    """Client pour interagir avec des API compatibles OpenAI (Ollama, etc.)."""

    def __init__(
        self,
        model: str,
        base_url: str,
        temperature: float = 0.1,
        timeout: int = 30,
        api_key: Optional[str] = None,
    ):
        api_key = api_key or os.environ.get("API_KEY_LOCAL")
        super().__init__(model, temperature, timeout, api_key, base_url)

    @handle_errors(
        category=ErrorCategory.LLM,
        severity=ErrorSeverity.MEDIUM,
        user_message="Erreur lors de l'appel au LLM (type OpenAI)",
        default_return=LLMResponse(
            content="Erreur Timeout ou API indisponible", co2_emissions=0.0
        ),
    )
    def call_llm(
        self,
        messages: List[Union[Dict, LLMMessage]],
        response_format: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        """Effectue un appel au LLM."""
        formatted_messages = self._normalize_messages(messages)
        logger.debug(f"Appel OpenAI {self.model}: {len(formatted_messages)} messages")

        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": self.temperature,
        }
        if response_format:
            payload["response_format"] = response_format

        url = f"{self.base_url}/chat/completions"

        # Créer un tracker à la volée pour une mesure isolée
        tracker = EmissionsTracker(
            measure_power_secs=1,
            tracking_mode="machine",
            log_level="error",
        )
        tracker.start()

        try:
            response = self.session.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            response_data = response.json()
            result = response_data["choices"][0]["message"]["content"]
            logger.debug(f"Réponse OpenAI reçue: {len(result)} caractères")

            # Arrêter le tracking et récupérer les émissions
            emissions = tracker.stop()
            logger.debug(f"LLM API: {emissions:.6f} kg CO2")

            return LLMResponse(content=result, co2_emissions=emissions)

        except requests.exceptions.Timeout:
            tracker.stop()
            raise Exception(f"Timeout après {self.timeout} secondes")
        except requests.exceptions.ConnectionError:
            tracker.stop()
            raise Exception("Erreur de connexion à l'API")
        except requests.exceptions.HTTPError as e:
            tracker.stop()
            if e.response.status_code == 429:
                raise Exception("Limite de taux API atteinte")
            elif e.response.status_code == 401:
                raise Exception("Clé API invalide")
            else:
                raise Exception(f"Erreur HTTP {e.response.status_code}")
        except (KeyError, IndexError):
            tracker.stop()
            raise Exception("Format de réponse API invalide")
        except Exception as e:
            tracker.stop()
            raise e


class MistralAPIClient(BaseLLMClient):
    """Client pour interagir avec l'API officielle de Mistral AI."""

    def __init__(
        self,
        model: str = "mistral-large-latest",
        temperature: float = 0.1,
        random_seed: int = 1,
        timeout: int = 30,
        api_key: Optional[str] = None,
    ):
        api_key = api_key or os.environ.get("API_KEY_MISTRAL")
        if not api_key:
            raise ValueError("Clé API Mistral requise (API_KEY_MISTRAL)")

        super().__init__(
            model, temperature, timeout, api_key, "https://api.mistral.ai/v1"
        )
        self.random_seed = random_seed

    @handle_errors(
        category=ErrorCategory.LLM,
        severity=ErrorSeverity.MEDIUM,
        user_message="Erreur lors de l'appel au LLM Mistral",
        default_return=LLMResponse(content="Erreur API Mistral", co2_emissions=0.0),
    )
    def call_llm(
        self,
        messages: List[Union[Dict, LLMMessage]],
        tool_params: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        """Effectue un appel au LLM Mistral."""
        formatted_messages = self._normalize_messages(messages)
        logger.debug(f"Appel Mistral {self.model}: {len(formatted_messages)} messages")

        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": self.temperature,
            "random_seed": self.random_seed,
        }
        if tool_params:
            payload.update(tool_params)

        url = f"{self.base_url}/chat/completions"

        # Créer un tracker à la volée pour une mesure isolée
        tracker = EmissionsTracker(
            measure_power_secs=1,
            tracking_mode="machine",
            log_level="error",
        )
        tracker.start()

        try:
            response = self.session.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            response_data = response.json()
            choice = response_data["choices"][0]

            if "tool_calls" in choice["message"] and choice["message"]["tool_calls"]:
                result = choice["message"]["tool_calls"][0]["function"]["arguments"]
            else:
                result = choice["message"]["content"]

            logger.debug(f"Réponse Mistral reçue: {len(result)} caractères")

            # Arrêter le tracking et récupérer les émissions
            emissions = tracker.stop()
            logger.debug(f"Émissions CO2 mesurées: {emissions:.6f} kg")

            return LLMResponse(content=result, co2_emissions=emissions)

        except (requests.exceptions.RequestException, KeyError, IndexError) as e:
            tracker.stop()
            # Laisse le décorateur @handle_errors gérer l'exception
            raise e


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
