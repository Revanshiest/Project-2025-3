import requests
from typing import Optional
import chromadb
from chromadb.api.types import EmbeddingFunction
from pathlib import Path

class OllamaEmbeddingFunction(EmbeddingFunction):
    """Класс для эмбеддингов через Ollama"""
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url
        self.model = model
    
    def name(self):
        """Возвращает имя функции эмбеддингов"""
        return "ollama_embedding"
    
    def __call__(self, texts):
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
                    print(f"❌ Ошибка эмбеддинга: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Ошибка при получении эмбеддинга: {e}")
                
        return embeddings

import os
import json

class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model = "gpt-oss:120b-cloud"
        self.embedding_model = "qwen3-embedding:4b"

        # Словарь для всех найденных Chroma клиентов
        self.chroma_clients = {}
        self._init_chroma_clients()

    def _get_embedding_function(self):
        """Создает функцию эмбеддингов через Ollama"""
        return OllamaEmbeddingFunction(self.base_url, self.embedding_model)

    def _init_chroma_clients(self):
        """Автоматически инициализирует все найденные Chroma PersistentClient в VectorDB"""
        try:
            vector_db_root = Path("data_pars/VectorDB")
            if not vector_db_root.exists():
                print(f"❌ Папка VectorDB не найдена: {vector_db_root}")
                return
            for subdir in vector_db_root.iterdir():
                if subdir.is_dir() and (subdir / "chroma.sqlite3").exists():
                    db_name = subdir.name.replace("chroma_", "")
                    self.chroma_clients[db_name] = chromadb.PersistentClient(path=str(subdir))
                    print(f"✅ Найдена векторная БД: {db_name} -> {subdir}")
        except Exception as e:
            print(f"Ошибка инициализации Chroma клиентов: {e}")

    def _retrieve_rag_context(self, query: str, section_type: str) -> str:
        """ 
        Получает релевантные документы из Chroma для RAG контекста

        Args:
            query: Вопрос пользователя
            section_type: "races", "spells" или "classes"

        Returns:
            Отформатированный контекст из БД
        """
        try:
            embedding_func = self._get_embedding_function()
            query_embedding = embedding_func([query])[0]
            db_client = self.chroma_clients.get(section_type)
            if not db_client:
                print(f"❌ Нет клиента для типа: {section_type}")
                return ""
            # Для races — приоритет dnd_races, иначе fallback на первую доступную
            collections = db_client.list_collections()
            collection = None
            if section_type == "races":
                for coll in collections:
                    if coll.name == "dnd_races":
                        try:
                            collection = db_client.get_collection(name="dnd_races")
                            print(f"✅ Используем коллекцию 'dnd_races' для 'races'")
                            break
                        except Exception:
                            continue
            if not collection:
                for coll in collections:
                    try:
                        collection = db_client.get_collection(name=coll.name)
                        print(f"✅ Используем коллекцию '{coll.name}' для '{section_type}'")
                        break
                    except Exception:
                        continue
            if not collection:
                print(f"❌ Нет коллекций в БД {section_type}")
                return ""
            count = 0
            try:
                count = collection.count()
                print(f"🔍 Коллекция '{section_type}': найдено {count} документов")
                if count == 0:
                    print(f"⚠️  Коллекция '{section_type}' пустая!")
                    return ""
            except Exception as e:
                print(f"⚠️  Не удалось проверить количество документов: {e}")
            n_results = min(5, count) if count > 0 else 5
            try:
                results = collection.query(query_texts=[query], n_results=n_results)
            except Exception as e1:
                try:
                    results = collection.query(query_embeddings=[query_embedding], n_results=n_results)
                except Exception as e2:
                    print(f"❌ Ошибка при запросе к коллекции: {e1}, {e2}")
                    return ""
            if results and results.get("documents") and len(results["documents"]) > 0:
                context_parts = [doc for doc in results["documents"][0] if doc]
                rag_context = "\n\n---\n\n".join(context_parts)
                print(f"📚 RAG контекст для '{section_type}' (запрос: '{query}'):")
                print(f"   Найдено документов: {len(context_parts)}")
                for i, part in enumerate(context_parts, 1):
                    print(f"   [{i}] {part[:100]}..." if len(part) > 100 else f"   [{i}] {part}")
                print("---")
                return rag_context
            else:
                print(f"⚠️  RAG не нашёл документы для '{section_type}' (запрос: '{query}')")
                print(f"   Результат запроса: {results}")
                return ""
        except Exception as e:
            print(f"❌ Ошибка при поиске в Chroma: {e}")
            return ""
    
    def generate_response(self, user_message: str, section_name: str = "", section_content: str = "") -> Optional[str]:
        """
        Генерирует ответ от Ollama, позволяя самой модели обращаться к RAG через функцию.
        Args:
            user_message: Вопрос пользователя
            section_name: Название раздела
            section_content: Базовое содержимое раздела
        """
        # Инструкция для модели: если нужны внешние данные, запрашивай их через функцию RAG
        rag_db_types = list(self.chroma_clients.keys())
                # Разделы, по которым есть собственные тексты (не использовать RAG):
        manual_sections = [
                        "rules", "dice", "combat", "glossary", "stats", "start", "help"
                ]
        rag_tools_description = f"""
Если вопрос пользователя относится к разделам: {', '.join('/' + s for s in manual_sections)}, отвечай только на основе предоставленного контента раздела (не используй rag_request).
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

        prompt = f"""Ты помощник по D&D для новичков.

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
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.8,
                    "max_tokens": 1024
                },
                timeout=120
            )
            if response.status_code == 200:
                answer = response.json().get("response", "").strip()
                # Проверяем, вернула ли модель JSON с rag_request
                try:
                    parsed = json.loads(answer)
                    if isinstance(parsed, dict) and "rag_request" in parsed:
                        rag_req = parsed["rag_request"]
                        db_type = rag_req.get("type")
                        rag_query = rag_req.get("query")
                        print(f"[DEBUG] RAG-запрос: type={db_type}, query={rag_query}")
                        rag_context = self._retrieve_rag_context(rag_query, db_type)
                        # Повторяем запрос, добавляя найденный контекст
                        prompt2 = f"""Ты помощник по D&D для новичков.

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
                        response2 = requests.post(
                            f"{self.base_url}/api/generate",
                            json={
                                "model": self.model,
                                "prompt": prompt2,
                                "stream": False,
                                "temperature": 0.8,
                                "max_tokens": 1024
                            },
                            timeout=120
                        )
                        if response2.status_code == 200:
                            final_answer = response2.json().get("response", "").strip()
                            return final_answer
                        else:
                            return "Ошибка генерации ответа после RAG-запроса."
                except Exception:
                    pass
                # Если не JSON, возвращаем обычный ответ
                return answer
            return None
        except requests.exceptions.ConnectionError:
            return "❌ Ошибка подключения к Ollama. Убедись, что сервис запущен."
        except Exception as e:
            return f"❌ Ошибка: {e}"