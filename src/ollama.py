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

class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model = "gpt-oss:120b-cloud"
        self.embedding_model = "qwen3-embedding:4b"

        self.chroma_client_races = None
        self.chroma_client_spells = None
        self.chroma_client_classes = None
        self._init_chroma_clients()

    def _get_embedding_function(self):
        """Создает функцию эмбеддингов через Ollama"""
        return OllamaEmbeddingFunction(self.base_url, self.embedding_model)

    def _init_chroma_clients(self):
        """Инициализирует Chroma клиентов для БД рас, заклинаний и классов"""
        try:
            races_db_path = Path("data_pars/chroma_races")
            spells_db_path = Path("data_pars/chroma_spells")
            classes_db_path = Path("data_pars/chroma_classes")
            
            if races_db_path.exists():
                self.chroma_client_races = chromadb.PersistentClient(
                    path=str(races_db_path)
                )

            if spells_db_path.exists():
                self.chroma_client_spells = chromadb.PersistentClient(
                    path=str(spells_db_path)
                )
            
            if classes_db_path.exists():
                self.chroma_client_classes = chromadb.PersistentClient(
                    path=str(classes_db_path)
                )
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
            # Создаём объект эмбеддингов
            embedding_func = self._get_embedding_function()
            # Получаем эмбеддинг для запроса вручную
            query_embedding = embedding_func([query])[0]
            
            collection = None
            if section_type == "races" and self.chroma_client_races:
                # Пробуем получить коллекцию 'dnd_races' (основная) или 'races' (резервная)
                collection_names = ["dnd_races", "races"]
                for coll_name in collection_names:
                    try:
                        collection = self.chroma_client_races.get_collection(name=coll_name)
                        print(f"✅ Используем коллекцию '{coll_name}'")
                        break
                    except Exception:
                        continue
                
                # Если ни одна коллекция не найдена, создаём новую
                if not collection:
                    collection = self.chroma_client_races.get_or_create_collection(
                        name="races",
                        embedding_function=embedding_func
                    )
            elif section_type == "spells" and self.chroma_client_spells:
                # Пробуем получить коллекцию 'dnd_spells' или 'spells'
                collection_names = ["dnd_spells", "spells"]
                for coll_name in collection_names:
                    try:
                        collection = self.chroma_client_spells.get_collection(name=coll_name)
                        print(f"✅ Используем коллекцию '{coll_name}'")
                        break
                    except Exception:
                        continue
                
                # Если ни одна коллекция не найдена, создаём новую
                if not collection:
                    collection = self.chroma_client_spells.get_or_create_collection(
                        name="spells",
                        embedding_function=embedding_func
                    )
            elif section_type == "classes" and self.chroma_client_classes:
                # Пробуем получить коллекцию 'dnd_classes' или 'classes'
                collection_names = ["dnd_classes", "classes"]
                for coll_name in collection_names:
                    try:
                        collection = self.chroma_client_classes.get_collection(name=coll_name)
                        print(f"✅ Используем коллекцию '{coll_name}'")
                        break
                    except Exception:
                        continue
                
                # Если ни одна коллекция не найдена, создаём новую
                if not collection:
                    collection = self.chroma_client_classes.get_or_create_collection(
                        name="classes",
                        embedding_function=embedding_func
                    )
            else:
                return ""
            
            if not collection:
                return ""
            
            # Проверяем количество документов в коллекции
            count = 0
            try:
                count = collection.count()
                print(f"🔍 Коллекция '{section_type}': найдено {count} документов")
                
                if count == 0:
                    print(f"⚠️  Коллекция '{section_type}' пустая! Нужно добавить документы.")
                    # Пробуем получить список всех коллекций для диагностики
                    try:
                        all_collections = self.chroma_client_races.list_collections() if section_type == "races" else self.chroma_client_spells.list_collections()
                        print(f"   Доступные коллекции: {[c.name for c in all_collections]}")
                    except:
                        pass
                    return ""
            except Exception as e:
                print(f"⚠️  Не удалось проверить количество документов: {e}")
                import traceback
                traceback.print_exc()
            
            # Пробуем использовать query_texts если коллекция имеет embedding_function
            # Иначе используем query_embeddings
            n_results = min(5, count) if count > 0 else 5
            try:
                # Если коллекция была создана с embedding_function, используем query_texts
                results = collection.query(
                    query_texts=[query],
                    n_results=n_results
                )
            except Exception as e1:
                # Если не работает query_texts, пробуем query_embeddings
                try:
                    results = collection.query(
                        query_embeddings=[query_embedding],
                        n_results=n_results
                    )
                except Exception as e2:
                    print(f"❌ Ошибка при запросе к коллекции: {e1}, {e2}")
                    return ""
            
            # Форматируем полученные документы
            if results and results.get("documents") and len(results["documents"]) > 0:
                context_parts = []
                for doc in results["documents"][0]:
                    if doc:
                        context_parts.append(doc)
                
                rag_context = "\n\n---\n\n".join(context_parts)
                
                # Отладка: показываем что достали из RAG
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
            import traceback
            traceback.print_exc()
            return ""
    
    def generate_response(self, user_message: str, section_name: str = "",
                           section_content: str = "", use_rag: bool = False,
                           rag_section_type: str = "") -> Optional[str]:
        """
        Генерирует ответ от Ollama с полным контекстом раздела.
        
        Args:
            user_message: Вопрос пользователя
            section_name: Название раздела
            section_content: Базовое содержимое раздела
            use_rag: Использовать ли RAG
            rag_section_type: Тип RAG ("races" или "spells")
        """

        # Получаем контекст из RAG если нужно
        rag_context = ""
        if use_rag:
            rag_context = self._retrieve_rag_context(user_message, rag_section_type)
        
        # Формируем промпт с RAG контекстом
        if use_rag and rag_context:
            prompt = f"""Ты помощник по D&D для новичков.

РАЗДЕЛ: {section_name}

РЕЛЕВАНТНАЯ ИНФОРМАЦИЯ ИЗ БАЗЫ ДАННЫХ:
{rag_context}

---

БАЗОВАЯ ИНФОРМАЦИЯ РАЗДЕЛА:
{section_content}

---

ИНСТРУКЦИИ:
1. Используй информацию из базы данных выше для ответа на вопрос.
2. Ответь кратко, понятно и дружелюбно на русском.
3. Приводи конкретные примеры из полученной информации.
4. Если информация неполная или вопрос выходит за рамки раздела, предложи открыть соответствующий раздел.

ВОПРОС ПОЛЬЗОВАТЕЛЯ:
{user_message}

ОТВЕТ:"""
        else:
            prompt = f"""Ты помощник по D&D для новичков.

    КОНТЕКСТ ТЕКУЩЕГО РАЗДЕЛА "{section_name}":
    {section_content}

    ---

    ИНСТРУКЦИИ:
    1. Если вопрос пользователя относится к содержимому этого раздела - ответь на него кратко, понятно и дружелюбно на русском.
    2. Если вопрос НЕ об этом разделе - предложи открыть соответствующий раздел (укажи его название) НАЗВАНИЯ РАЗДЕЛОВ(/races — список доступных рас,
        /classes — список классов персонажей,
        /rules — основные правила D&D,
        /dice — всё о бросках кубиков,
        /combat — правила боя для новичков,
        /spells — базовая информация о заклинаниях,
        /glossary — словарь терминов D&D,
        /stats — объяснение характеристик).
    3. Всегда приводи примеры из D&D когда это уместно.

    ВОПРОС ПОЛЬЗОВАТЕЛЯ:
    {user_message}

    ОТВЕТ:"""
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.8
                },
                timeout=120
            )
            
            if response.status_code == 200:
                return response.json().get("response", "").strip()
            return None
                
        except requests.exceptions.ConnectionError:
            return "❌ Ошибка подключения к Ollama. Убедись, что сервис запущен."
        except Exception as e:
            return f"❌ Ошибка: {e}"