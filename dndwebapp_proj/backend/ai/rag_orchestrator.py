import json
import logging
from typing import Optional, List
from backend.ai.interfaces import LLMService, EmbeddingService, VectorRepository
from backend.ai.ollama_client import OllamaConnectionError

logger = logging.getLogger(__name__)

class RAGOrchestrator:
    """
    Класс для координации RAG-процесса (Retrieval-Augmented Generation).
    Отвечает только за логику оркестрации, сборку промптов и разбор ответов (Single Responsibility).
    Зависит исключительно от абстракций (Dependency Inversion Principle).
    """
    
    MANUAL_SECTIONS = [
        "rules", "dice", "combat", "glossary", "stats", "start", "help"
    ]

    def __init__(
        self,
        llm_service: LLMService,
        embedding_service: EmbeddingService,
        vector_repository: VectorRepository
    ):
        self.llm_service = llm_service
        self.embedding_service = embedding_service
        self.vector_repository = vector_repository

    def _build_rag_tools_description(self, rag_db_types: List[str]) -> str:
        """Собирает описание RAG-инструментов для первого промпта."""
        return f"""
Если вопрос пользователя относится к разделам: {', '.join('/' + s for s in self.MANUAL_SECTIONS)}, отвечай только на основе предоставленного контента раздела (не используй rag_request).
Если вопрос пользователя НЕ относится к этим разделам, но касается темы, по которой есть векторная база данных (RAG) — а именно: {', '.join(rag_db_types)} — ты ОБЯЗАН сначала запросить данные из этой базы (через rag_request), а уже затем дать ответ пользователю.
Формат запроса:
{{
    "rag_request": {{
        "type": "<тип>",
        "query": "<текст запроса к RAG>"
    }}
}}
Если вопрос не относится ни к одной из этих тем — отвечай обычным текстом.

ОФОРМЛЯЙ все ответы в html-формате (используй <b>, <i>, <br> и другие html-теги для выделения, абзацев и списков, не используй ** или __ для выделения).

Пример:
Вопрос пользователя: "Расскажи подробнее про расу эльфов?"
Твой ответ:
{{
    "rag_request": {{
        "type": "races",
        "query": "описание эльфов"
    }}
}}
        """

    def _build_initial_prompt(
        self, user_message: str, section_name: str, 
        section_content: str, rag_tools_description: str
    ) -> str:
        """Собирает первый промпт для LLM."""
        return f"""Ты помощник по D&D для новичков.

КОНТЕКСТ ТЕКУЩЕГО РАЗДЕЛА "{section_name}":
{section_content}

---

{rag_tools_description}

ИНСТРУКЦИИ:
1. Если вопрос пользователя относится к теме, по которой есть векторная БД (см. выше), всегда сначала верни JSON с rag_request (см. пример выше), а затем дай ответ, используя полученные данные.
2. Если вопрос пользователя не относится ни к одной из этих тем — ответь кратко, понятно и дружелюбно на русском.
3. Если вопрос НЕ об этом разделе — предложи открыть соответствующий раздел (укажи его название) НАЗВАНИЯ РАЗДЕЛОВ(/races — список доступных рас, /classes — список классов персонажей, /rules — основные правила D&D, /dice — всё о бросках кубиков, /combat — правила боя для новичков, /spells — базовая информация о заклинаниях, /glossary — словарь терминов D&D, /stats — объяснение характеристик).
4. Всегда приводи примеры из D&D когда это уместно.

Вопрос пользователя:
{user_message}

Ответ:"""

    def _build_rag_followup_prompt(
        self, user_message: str, section_name: str, 
        section_content: str, db_type: str, rag_context: str
    ) -> str:
        """Собирает второй промпт после получения RAG-контекста."""
        return f"""Ты помощник по D&D для новичков.

КОНТЕКСТ ТЕКУЩЕГО РАЗДЕЛА "{section_name}":
{section_content}

---

ДОПОЛНИТЕЛЬНЫЕ ДАННЫЕ ИЗ RAG ({db_type}):
{rag_context}

---

ИНСТРУКЦИИ:
1. Используй данные из RAG выше для ответа на вопрос.
2. Ответь кратко, понятно и дружелюбно на русском.
3. Приводи конкретные примеры из полученной информации.
4. Если информации недостаточно, предложи открыть другой раздел.
5. Не упоминай rag_request и не показывай технические детали пользователю.
6. Ответ не должен превышать 1024 символа.
7. Всегда проверяй себя на грамматические нормы языка.

Вопрос пользователя:
{user_message}

Ответ:"""

    def _try_parse_rag_request(self, answer: str) -> Optional[dict]:
        """
        Пытается разобрать ответ LLM как RAG-запрос.
        Возвращает словарь с ключами 'type' и 'query' или None.
        """
        try:
            parsed = json.loads(answer)
            if isinstance(parsed, dict) and "rag_request" in parsed:
                return parsed["rag_request"]
        except (json.JSONDecodeError, KeyError, TypeError):
            # Ответ не является JSON — это нормальный текстовый ответ
            pass
        return None

    def generate_response(
        self, 
        user_message: str, 
        section_name: str = "", 
        section_content: str = ""
    ) -> Optional[str]:
        """
        Генерирует ответ от модели, позволяя ей обращаться к RAG при необходимости.
        """
        rag_db_types = self.vector_repository.list_clients()
        rag_tools_description = self._build_rag_tools_description(rag_db_types)
        prompt = self._build_initial_prompt(
            user_message, section_name, section_content, rag_tools_description
        )

        try:
            # Первый вызов к LLM
            answer = self.llm_service.generate(prompt)
            if answer is None:
                return None

            # Пробуем разобрать JSON-ответ для RAG-запроса
            rag_req = self._try_parse_rag_request(answer)
            if rag_req is not None:
                db_type = rag_req.get("type")
                rag_query = rag_req.get("query")
                logger.debug("RAG-запрос: type=%s, query=%s", db_type, rag_query)

                # Генерируем эмбеддинг для поиска
                query_embedding = self.embedding_service.embed_query(rag_query)

                # Получаем контекст из репозитория
                rag_context = self.vector_repository.retrieve_context(
                    rag_query, db_type, query_embedding
                )

                prompt2 = self._build_rag_followup_prompt(
                    user_message, section_name, section_content, db_type, rag_context
                )

                # Второй вызов к LLM с контекстом RAG
                final_answer = self.llm_service.generate(prompt2)
                if final_answer is not None:
                    return final_answer
                else:
                    return "Ошибка генерации ответа после RAG-запроса."

            return answer
        except OllamaConnectionError:
            logger.error("Не удалось подключиться к LLM-сервису")
            return None
        except Exception as e:
            logger.error("Ошибка в RAG-оркестраторе: %s", e)
            return None
