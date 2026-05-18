import logging
import requests
from typing import List, Optional
from chromadb.api.types import EmbeddingFunction
from backend.ai.interfaces import EmbeddingService, LLMService

logger = logging.getLogger(__name__)


class OllamaConnectionError(Exception):
    """Исключение для ошибок соединения с Ollama API."""
    pass


class OllamaEmbeddingService(EmbeddingService):
    """
    Реализация сервиса эмбеддингов через Ollama API.
    Отвечает только за генерацию векторов (Single Responsibility).
    """
    def __init__(self, base_url: str, model: str = "qwen3-embedding:4b"):
        self.base_url = base_url
        self.model = model

    def name(self) -> str:
        return "ollama_embedding"

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for text in texts:
            try:
                response = requests.post(
                    f"{self.base_url}/api/embed",
                    json={
                        "model": self.model,
                        "input": text
                    },
                    timeout=30
                )
                if response.status_code == 200:
                    embedding = response.json()["embeddings"][0]
                    embeddings.append(embedding)
                else:
                    logger.error(
                        "Ошибка эмбеддинга (status %d): %s",
                        response.status_code, response.text
                    )
                    # Добавляем пустой вектор, чтобы индексы не сдвигались
                    embeddings.append([])
            except Exception as e:
                logger.error("Ошибка при получении эмбеддинга: %s", e)
                # Добавляем пустой вектор, чтобы индексы не сдвигались
                embeddings.append([])
        return embeddings

    def embed_query(self, query: str) -> List[float]:
        results = self.embed_texts([query])
        if results:
            return results[0]
        return []


class OllamaEmbeddingFunction(EmbeddingFunction):
    """
    Обертка над OllamaEmbeddingService для совместимости с ChromaDB.
    Реализует стандартный интерфейс EmbeddingFunction от chromadb.
    """
    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service

    def name(self) -> str:
        return self.embedding_service.name()

    def __call__(self, texts: List[str]) -> List[List[float]]:
        return self.embedding_service.embed_texts(texts)


class OllamaLLMService(LLMService):
    """
    Реализация сервиса генерации текста через Ollama API.
    Отвечает только за текстовую генерацию (Single Responsibility).
    """
    def __init__(self, base_url: str, model: str = "gpt-oss:120b-cloud"):
        self.base_url = base_url
        self.model = model

    def generate(
        self, 
        prompt: str, 
        temperature: float = 0.8, 
        max_tokens: int = 1024
    ) -> Optional[str]:
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                timeout=120
            )
            if response.status_code == 200:
                return response.json().get("response", "").strip()
            logger.error(
                "Ollama вернул статус %d: %s", response.status_code, response.text
            )
            return None
        except requests.exceptions.ConnectionError as e:
            logger.error("Ошибка подключения к Ollama: %s", e)
            raise OllamaConnectionError(
                "Ошибка подключения к Ollama. Убедитесь, что сервис запущен."
            ) from e
        except Exception as e:
            logger.error("Непредвиденная ошибка при генерации: %s", e)
            raise OllamaConnectionError(f"Ошибка генерации: {e}") from e
