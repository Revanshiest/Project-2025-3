import requests
from typing import Optional
import chromadb
from pathlib import Path

class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model = "gpt-oss:120b-cloud"

        # Инициализируем Chroma клиент для RAG
        self.chroma_client_races = None
        self.chroma_client_spells = None
        self._init_chroma_clients()

    def _init_chroma_clients(self):
        """Инициализирует Chroma клиентов для БД рас и заклинаний"""

        try:
            races_db_path = Path("data_pars/chroma_races")
            spells_db_path = Path("data_pars/chroma_spells")

            if races_db_path.exists():
                self.chroma_client_races = chromadb.PersistentClient(
                    path=str(races_db_path)
                )

            if spells_db_path.exists():
                self.chroma_client_spells = chromadb.PersistentClient(
                    path=str(spells_db_path)
                )
        except Exception as e:
            print(f"Ошибка инициализации Chroma клиентов: {e}")

    def _retrieve_rag_context(self, query: str, section_type: str) -> str:
        """
        Получает релевантные документы из Chroma для RAG контекста
        
        Args:
            query: Вопрос пользователя
            section_type: "races" или "spells"
        
        Returns:
            Отформатированный контекст из БД
        """
        try:
            if section_type == "races" and self.chroma_client_races:
                collection = self.chroma_client_races.get_or_create_collection(
                    name="races"
                )
                results = collection.query(
                    query_texts=[query],
                    n_results=5
                )
            elif section_type == "spells" and self.chroma_client_spells:
                collection = self.chroma_client_spells.get_or_create_collection(
                    name="spells"
                )
                results = collection.query(
                    query_texts=[query],
                    n_results=5
                )
            else:
                return ""
            
            # Форматируем полученные документы
            if results and results.get("documents"):
                context_parts = []
                for doc in results["documents"][0]:
                    if doc:
                        context_parts.append(doc)
                return "\n\n---\n\n".join(context_parts)
            return ""
            
        except Exception as e:
            print(f"❌ Ошибка при поиске в Chroma: {e}")
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