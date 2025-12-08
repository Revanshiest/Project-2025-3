import requests
from typing import Optional

class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model = "gpt-oss:120b-cloud"
    
    def generate_response(self, user_message: str, section_name: str = "", section_content: str = "") -> Optional[str]:
        """
        Генерирует ответ от Ollama с полным контекстом раздела.
        За один раз обрабатывает вопрос и проверяет релевантность.
        """
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