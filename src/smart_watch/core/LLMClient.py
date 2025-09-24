# Documentation: https://datagora-erasme.github.io/smart_watch/source/modules/core/LLMClient.html

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import requests
from codecarbon import EmissionsTracker
from fastembed import TextEmbedding

from ..config.markdown_filtering_config import MarkdownFilteringConfig
from .ErrorHandler import ErrorCategory, ErrorHandler, ErrorSeverity, handle_errors
from .Logger import SmartWatchLogger, create_logger

# Initialize logger for this module
logger = create_logger(
    module_name="LLMClient",
)


@dataclass
class LLMResponse:
    """Réponse enrichie d'un appel LLM avec mesure de consommation.

    Attributes:
        content (Union[str, List[Any]]): contenu de la réponse, texte ou liste (pour les embeddings).
        co2_emissions (float): émissions de CO2 en kg.
    """

    content: Union[str, List[Any]]
    co2_emissions: float


@dataclass
class LLMMessage:
    """Représente un message dans une conversation avec le LLM.

    Attributes:
        role (str): rôle du message ("user", "assistant", "system").
        content (str): contenu textuel du message.
    """

    role: str
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
    ) -> None:
        """Initialise le client LLM avec les paramètres de base.

        Args:
            model (str): le nom du modèle LLM.
            temperature (float): la température pour la génération de texte.
            timeout (int): le délai d'attente pour les requêtes API, en secondes.
            api_key (Optional[str]): clé API pour l'authentification.
            base_url (Optional[str]): URL de base de l'API LLM.

        Attributes:
            model (str): nom du modèle LLM.
            temperature (float): température pour la génération.
            timeout (int): délai d'attente pour les requêtes.
            api_key (Optional[str]): clé API.
            base_url (Optional[str]): URL de base de l'API.
            session (requests.Session): session HTTP pour les requêtes.
            error_handler (ErrorHandler): gestionnaire d'erreurs.
        """
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
        """Crée et configure une session requests avec les en-têtes appropriés.

        Returns:
            requests.Session: la session HTTP configurée.
        """
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        if self.api_key:
            session.headers.update({"Authorization": f"Bearer {self.api_key}"})
        return session

    def _normalize_messages(
        self, messages: List[Union[Dict[str, str], LLMMessage]]
    ) -> List[Dict[str, str]]:
        """Convertit les objets LLMMessage en dictionnaires pour l'appel API.

        Args:
            messages (List[Union[Dict[str, str], LLMMessage]]): liste de messages à normaliser.

        Returns:
            List[Dict[str, str]]: liste de messages normalisés au format dictionnaire.
        """

        return [
            {"role": msg.role, "content": msg.content}
            if isinstance(msg, LLMMessage)
            else msg
            for msg in messages
        ]

    @abstractmethod
    def call_llm(
        self,
        messages: List[Union[Dict[str, str], LLMMessage]],
        index: int = 0,
        total: int = 0,
        **kwargs: Any,
    ) -> LLMResponse:
        """Méthode abstraite pour effectuer un appel au LLM avec mesure d'émissions.

        Args:
            messages (List[Union[Dict[str, str], LLMMessage]]): liste de messages à envoyer au LLM.
            index (int): index de l'appel dans une liste, utilisé pour le logging.
            total (int): nombre total d'appels à traiter, utilisé pour le logging.
            **kwargs (Any): arguments supplémentaires pour l'appel LLM.

        Returns:
            LLMResponse: réponse du LLM enrichie avec les émissions de CO2.
        """
        pass

    def send_message(
        self,
        content: str,
        role: str = "user",
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Envoie un message simple au LLM.

        Args:
            content (str): le contenu du message à envoyer.
            role (str): le rôle de l'expéditeur du message ("user", "assistant", "system").
            system_prompt (Optional[str]): un prompt système optionnel pour initialiser la conversation.
            **kwargs (Any): paramètres supplémentaires pour l'appel LLM.

        Returns:
            LLMResponse: réponse du LLM enrichie avec les émissions de CO2.
        """
        messages = []
        if system_prompt:
            messages.append(LLMMessage(role="system", content=system_prompt))
        messages.append(LLMMessage(role=role, content=content))
        return self.call_llm(messages, **kwargs)

    def conversation(
        self, messages: List[Union[Dict[str, str], LLMMessage]], **kwargs: Any
    ) -> LLMResponse:
        """Raccourci pour `call_llm`.

        Args:
            messages (List[Union[Dict[str, str], LLMMessage]]): liste de messages.
            **kwargs (Any): arguments supplémentaires.

        Returns:
            LLMResponse: réponse du LLM.
        """
        return self.call_llm(messages, **kwargs)

    def call_embeddings(self, texts: List[str]) -> LLMResponse:
        """Appel des embeddings via l'API LLM avec mesure d'émissions.

        Args:
            texts (List[str]): liste de textes pour lesquels générer des embeddings.

        Returns:
            LLMResponse: réponse contenant les embeddings et les émissions de CO2.
        """
        # Créer un tracker à la volée pour une mesure isolée
        tracker = EmissionsTracker(
            measure_power_secs=1,
            tracking_mode="machine",
            log_level="error",
            save_to_file=False,
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
            emissions = tracker.stop() or 0.0
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
        api_key: str,
        model: str,
        base_url: str,
        temperature: float = 0.1,
        timeout: int = 30,
        seed: Optional[int] = None,
    ) -> None:
        """Initialise le client pour les API compatibles OpenAI.

        Args:
            api_key (str): la clé API pour l'authentification.
            model (str): le nom du modèle LLM.
            base_url (str): l'URL de base de l'API.
            temperature (float): la température pour la génération de texte.
            timeout (int): le délai d'attente pour les requêtes API.
            seed (Optional[int]): graine aléatoire pour la génération (optionnel).
        """
        super().__init__(model, temperature, timeout, api_key, base_url)
        self.seed = seed  # Stocker le seed

    @handle_errors(
        category=ErrorCategory.LLM,
        severity=ErrorSeverity.MEDIUM,
        user_message="Erreur lors de l'appel au LLM (compatible OpenAI)",
        default_return=LLMResponse(
            content="Erreur Timeout ou API indisponible", co2_emissions=0.0
        ),
    )
    def call_llm(
        self,
        messages: List[Union[Dict[str, str], LLMMessage]],
        response_format: Optional[Dict[str, Any]] = None,
        index: int = 0,
        total: int = 0,
    ) -> LLMResponse:
        """Effectue un appel au LLM.

        Args:
            messages (List[Union[Dict[str, str], LLMMessage]]): liste de messages à envoyer au LLM.
            response_format (Optional[Dict[str, Any]]): format de réponse structuré (si nécessaire).
            index (int): index de l'appel dans une liste, utilisé pour le logging.
            total (int): nombre total d'appels à traiter, utilisé pour le logging.

        Returns:
            LLMResponse: réponse du LLM enrichie avec les émissions de CO2.
        """
        formatted_messages = self._normalize_messages(messages)
        log_message_prefix = ""
        if total > 0:
            log_message_prefix = f"Appel LLM {index}/{total} "
        logger.debug(
            f"{log_message_prefix}Compatible OpenAI {self.model}: {len(formatted_messages)} messages"
        )
        tracker = None  # Initialiser le tracker
        try:
            # Construire le payload de base
            payload = {
                "model": self.model,
                "messages": formatted_messages,
                "temperature": self.temperature,
            }

            # Ajouter le seed s'il est défini
            if self.seed is not None:
                payload["seed"] = self.seed

            # Ajouter le format de réponse si spécifié
            if response_format:
                payload["response_format"] = response_format

            url = f"{self.base_url}/chat/completions"

            # Créer un tracker à la volée pour une mesure isolée
            tracker = EmissionsTracker(
                measure_power_secs=1,
                tracking_mode="machine",
                log_level="error",
                save_to_file=False,
            )
            tracker.start()

            response = self.session.post(url, json=payload, timeout=self.timeout)

            # Log de la réponse en cas d'erreur avant de lever une exception
            if response.status_code != 200:
                logger.error(
                    f"Erreur API compatible OpenAI ({response.status_code}): {response.text}"
                )

            response.raise_for_status()
            response_data = response.json()
            result = response_data["choices"][0]["message"]["content"]
            logger.debug(f"Réponse OpenAI reçue: {len(result)} caractères")

            # Arrêter le tracking et récupérer les émissions
            emissions = tracker.stop() or 0.0
            logger.debug(f"LLM API: {emissions:.6f} kg CO2")

            return LLMResponse(content=result, co2_emissions=emissions)

        except requests.exceptions.Timeout:
            if tracker:
                tracker.stop()
            raise Exception(f"Timeout après {self.timeout} secondes")
        except requests.exceptions.ConnectionError:
            if tracker:
                tracker.stop()
            raise Exception("Erreur de connexion à l'API")
        except requests.exceptions.HTTPError as e:
            if tracker:
                tracker.stop()
            if e.response.status_code == 429:
                raise Exception("Limite de taux API atteinte")
            elif e.response.status_code == 401:
                raise Exception("Clé API invalide")
            else:
                raise Exception(f"Erreur HTTP {e.response.status_code}")
        except (KeyError, IndexError):
            if tracker:
                tracker.stop()
            raise Exception("Format de réponse API invalide")
        except Exception as e:
            if tracker:
                tracker.stop()
            # Log de l'exception détaillée pour un meilleur débogage
            logger.error(
                f"Exception détaillée lors de l'appel au LLM compatible OpenAI: {e}"
            )
            raise e


class MistralAPIClient(BaseLLMClient):
    """Client pour interagir avec l'API officielle de Mistral AI."""

    def __init__(
        self,
        api_key: str,
        model: str,
        temperature: float = 0.1,
        timeout: int = 30,
        seed: Optional[int] = None,
    ) -> None:
        """Initialise le client pour l'API Mistral.

        Args:
            api_key (str): la clé API pour l'authentification.
            model (str): le nom du modèle LLM.
            temperature (float): la température pour la génération de texte.
            timeout (int): le délai d'attente pour les requêtes API.
            seed (Optional[int]): graine aléatoire pour la génération (optionnel).
        """
        # Initialiser la classe de base avec une URL fixe pour Mistral
        super().__init__(
            model=model,
            temperature=temperature,
            timeout=timeout,
            api_key=api_key,
            base_url="https://api.mistral.ai/v1",
        )
        self.seed = seed

    @handle_errors(
        category=ErrorCategory.LLM,
        severity=ErrorSeverity.MEDIUM,
        user_message="Erreur lors de l'appel à l'API Mistral",
        default_return=LLMResponse(
            content="Erreur API Mistral indisponible", co2_emissions=0.0
        ),
    )
    def call_llm(
        self,
        messages: List[Union[Dict[str, str], LLMMessage]],
        tool_params: Optional[Dict[str, Any]] = None,
        index: int = 0,
        total: int = 0,
    ) -> LLMResponse:
        """Effectue un appel vers l'API Mistral.

        Args:
            messages (List[Union[Dict[str, str], LLMMessage]]): liste des messages à envoyer.
            tool_params (Optional[Dict[str, Any]]): paramètres pour l'utilisation d'outils.
            index (int): index de l'appel pour le logging.
            total (int): nombre total d'appels pour le logging.

        Returns:
            LLMResponse: réponse du LLM enrichie avec les émissions de CO2.
        """
        formatted_messages = self._normalize_messages(messages)
        log_message_prefix = ""
        if total > 0:
            log_message_prefix = f"Appel LLM {index}/{total} "
        logger.debug(
            f"{log_message_prefix}Mistral {self.model}: {len(formatted_messages)} messages"
        )
        tracker = None  # Initialiser le tracker
        try:
            # Préparer les paramètres de base
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
            }

            # Ajouter le seed s'il est défini
            if self.seed is not None:
                params["random_seed"] = self.seed  # Mistral utilise "random_seed"

            # Ajouter les outils si spécifiés
            if tool_params:
                params.update(tool_params)

            url = f"{self.base_url}/chat/completions"

            # Créer un tracker à la volée pour une mesure isolée
            tracker = EmissionsTracker(
                measure_power_secs=1,
                tracking_mode="machine",
                log_level="error",
                save_to_file=False,
            )
            tracker.start()

            response = self.session.post(url, json=params, timeout=self.timeout)

            # Log de la réponse en cas d'erreur avant de lever une exception
            if response.status_code != 200:
                logger.error(
                    f"Erreur API Mistral ({response.status_code}): {response.text}"
                )

            response.raise_for_status()
            response_data = response.json()
            choice = response_data["choices"][0]

            if "tool_calls" in choice["message"] and choice["message"]["tool_calls"]:
                result = choice["message"]["tool_calls"][0]["function"]["arguments"]
            else:
                result = choice["message"]["content"]

            logger.debug(f"Réponse Mistral reçue: {len(result)} caractères")

            # Arrêter le tracking et récupérer les émissions
            emissions = tracker.stop() or 0.0
            logger.debug(f"Émissions CO2 mesurées: {emissions:.6f} kg")

            return LLMResponse(content=result, co2_emissions=emissions)

        except (requests.exceptions.RequestException, KeyError, IndexError) as e:
            if tracker:
                tracker.stop()
            # Log de l'exception détaillée pour un meilleur débogage
            logger.error(f"Exception détaillée lors de l'appel Mistral: {e}")
            # Laisse le décorateur @handle_errors gérer l'exception
            raise e

    @handle_errors(
        category=ErrorCategory.LLM,
        severity=ErrorSeverity.MEDIUM,
        user_message="Erreur lors de l'appel aux embeddings Mistral",
        default_return=LLMResponse(content="Erreur API Mistral", co2_emissions=0.0),
    )
    def call_embeddings(self, texts: List[str]) -> LLMResponse:
        """Appel d'embeddings via API Mistral avec mesure d'émissions.

        Args:
            texts (List[str]): liste de textes pour lesquels générer des embeddings.

        Returns:
            LLMResponse: réponse contenant les embeddings et les émissions de CO2.

        Note:
            Utilise l'API embeddings de Mistral qui est compatible avec l'API OpenAI.
        """
        # Créer un tracker à la volée pour une mesure isolée
        tracker = EmissionsTracker(
            measure_power_secs=1,
            tracking_mode="machine",
            log_level="error",
            save_to_file=False,
        )
        tracker.start()

        try:
            # URL de l'endpoint embeddings (compatible OpenAI)
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
            emissions = tracker.stop() or 0.0
            logger.debug(
                f"Embeddings API Mistral: {len(embeddings)} vecteurs, {emissions:.6f} kg CO2"
            )

            return LLMResponse(content=embeddings, co2_emissions=emissions)

        except Exception as e:
            # S'assurer que le tracker est arrêté même en cas d'erreur
            tracker.stop()
            logger.error(f"Erreur calcul embeddings Mistral: {e}")
            raise


# Fonctions utilitaires pour les formats de réponse structurés
def get_structured_response_format(
    schema: Dict[str, Any], name: str = "response"
) -> Dict[str, Any]:
    """Formate un schéma pour les structured outputs OpenAI.

    Args:
        schema (Dict[str, Any]): le schéma JSON que la réponse doit suivre.
        name (str): le nom de la réponse.

    Returns:
        Dict[str, Any]: format de réponse pour l'API.
    """
    return {"type": "json_object", "json_schema": schema}


def get_mistral_tool_format(
    schema: Dict[str, Any], function_name: str = "extract_info"
) -> Dict[str, Any]:
    """Crée le dictionnaire pour le tool calling avec Mistral.

    Cette fonction force une réponse structurée.

    Args:
        schema (Dict[str, Any]): le schéma JSON que la réponse doit suivre.
        function_name (str): le nom de la fonction à appeler.

    Returns:
        Dict[str, Any]: format de réponse pour l'API Mistral avec tool calling.
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


class EmbeddingModel:
    """
    Classe d'abstraction pour gérer la génération d'embeddings,
    qu'elle soit locale ou via une API distante.
    """

    def __init__(self, md_config: MarkdownFilteringConfig, logger: SmartWatchLogger):
        self.config = md_config
        self.logger = logger
        self.client: Any = None  # Pour accepter TextEmbedding ou BaseLLMClient

        provider = self.config.embed_fournisseur
        model_name = self.config.embed_modele

        self.logger.debug(
            f"Initialisation de EmbeddingModel avec le fournisseur: {provider}"
        )

        if provider == "LOCAL":
            try:
                if not model_name:
                    raise ValueError(
                        "Le nom du modèle local (EMBED_MODELE_LOCAL) est manquant."
                    )
                cpu_count = os.cpu_count() or 1
                threads = max(1, cpu_count // 4)
                self.client = TextEmbedding(model_name=model_name, threads=threads)
                self.logger.info(f"Modèle d'embedding local chargé: {model_name}")
            except Exception as e:
                self.logger.error(f"Erreur lors du chargement du modèle local: {e}")
                raise
        elif provider in ["MISTRAL", "OPENAI", "OLLAMA"]:
            api_key = self.config.embed_api_key
            if not api_key:
                raise ValueError(
                    f"La clé API (EMBED_API_KEY) est manquante pour le fournisseur {provider}."
                )
            if not model_name:
                raise ValueError(
                    f"Le nom du modèle (EMBED_MODELE) est manquant pour le fournisseur {provider}."
                )

            if provider == "MISTRAL":
                self.client = MistralAPIClient(api_key=api_key, model=model_name)
            elif provider in ["OPENAI", "OLLAMA"]:
                base_url = self.config.embed_base_url
                if not base_url:
                    raise ValueError(
                        f"L'URL de base (EMBED_BASE_URL) est manquante pour le fournisseur {provider}."
                    )
                self.client = OpenAICompatibleClient(
                    api_key=api_key,
                    model=model_name,
                    base_url=base_url,
                )
        else:
            raise ValueError(f"Fournisseur d'embedding non supporté: {provider}")

    def get_text_embedding(
        self, texts: List[str], with_co2: bool = False
    ) -> Tuple[Optional[np.ndarray], float]:
        """Génère les embeddings pour une liste de textes."""
        if not self.client:
            raise ValueError("Client d'embedding non initialisé.")

        if self.config.embed_fournisseur == "LOCAL":
            embeddings = list(self.client.embed(texts))
            return np.array(embeddings), 0.0
        else:
            # Les clients API retournent un LLMResponse
            response: LLMResponse = self.client.call_embeddings(texts)
            if isinstance(response.content, list):
                return np.array(response.content), response.co2_emissions
            return None, 0.0
