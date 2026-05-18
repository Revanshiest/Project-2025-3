import os
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """
    Централизованная конфигурация приложения.
    Загружает настройки из переменных окружения и .env файла.
    Паттерн: Configuration Object (вместо разбросанных хардкодов).
    """

    # Приложение
    app_title: str = "D&D Helper Web API"
    app_version: str = "1.0.0"
    debug: bool = True

    # CORS
    cors_origins: List[str] = [
        "http://localhost:5173",
    ]
    cors_allow_methods: List[str] = ["GET", "POST", "PUT", "DELETE"]
    cors_allow_headers: List[str] = ["Content-Type", "Authorization"]

    # Ollama AI
    ollama_host: str = "http://localhost:11434"
    ollama_llm_model: str = "gpt-oss:120b-cloud"
    ollama_embedding_model: str = "qwen3-embedding:4b"

    # Пути к данным
    data_path: str = "backend/data"
    vector_db_path: str = "backend/data/VectorDB"

    # Сервер
    server_host: str = "0.0.0.0"
    server_port: int = 8000

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    """
    Возвращает кэшированный экземпляр настроек.
    Используется @lru_cache, чтобы .env читался только один раз.
    """
    return Settings()
