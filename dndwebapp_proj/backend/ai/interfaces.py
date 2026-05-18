from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any

class EmbeddingService(ABC):
    """
    Интерфейс для генерации векторных представлений (эмбеддингов).
    (Принцип разделения интерфейса - ISP, Инверсия зависимостей - DIP)
    """
    @abstractmethod
    def name(self) -> str:
        """Возвращает уникальное имя функции эмбеддингов"""
        pass

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Генерирует векторные представления для списка текстов"""
        pass

    @abstractmethod
    def embed_query(self, query: str) -> List[float]:
        """Генерирует векторное представление для одного запроса"""
        pass


class LLMService(ABC):
    """
    Интерфейс для взаимодействия с языковой моделью (LLM).
    (Принцип разделения интерфейса - ISP, Инверсия зависимостей - DIP)
    """
    @abstractmethod
    def generate(
        self, 
        prompt: str, 
        temperature: float = 0.8, 
        max_tokens: int = 1024
    ) -> Optional[str]:
        """Генерирует текстовый ответ на основе промпта"""
        pass


class VectorRepository(ABC):
    """
    Интерфейс репозитория для работы с векторной базой данных.
    (Принцип разделения интерфейса - ISP, Инверсия зависимостей - DIP)
    """
    @abstractmethod
    def list_clients(self) -> List[str]:
        """Возвращает список доступных разделов/клиентов векторной БД"""
        pass

    @abstractmethod
    def retrieve_context(
        self, 
        query: str, 
        section_type: str, 
        query_embedding: List[float]
    ) -> str:
        """
        Ищет и возвращает релевантный контекст из векторной БД по запросу
        """
        pass
