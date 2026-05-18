import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ChatRepository:
    """
    Отвечает за чтение и запись истории чатов с ИИ в файлы JSON (хранилище истории).
    Реализует паттерн Repository (SRP).
    """
    def __init__(self, data_path: str = "backend/data"):
        self.chats_path = Path(data_path) / "chats"

    def ensure_dir(self):
        self.chats_path.mkdir(parents=True, exist_ok=True)

    def load_chats_raw(self, user_id: int) -> List[dict]:
        """Загружает все сырые сессии чатов для пользователя."""
        user_file = self.chats_path / f"user_{user_id}.json"
        if not user_file.exists():
            return []
        try:
            with open(user_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error("Ошибка чтения истории чатов пользователя %d: %s", user_id, e)
            return []

    def get_by_user(self, user_id: int) -> List[dict]:
        """Возвращает список сессий чатов пользователя."""
        return self.load_chats_raw(user_id)

    def get_by_id(self, user_id: int, chat_id: str) -> Optional[dict]:
        """Возвращает конкретную сессию чата по её ID."""
        for chat in self.get_by_user(user_id):
            if chat.get("id") == chat_id:
                return chat
        return None

    def save_chat_session(self, user_id: int, chat_id: str, title: str, messages: List[Dict[str, Any]], is_active: bool = True) -> bool:
        """Сохраняет сессию чата пользователя."""
        self.ensure_dir()
        user_file = self.chats_path / f"user_{user_id}.json"
        chats = self.load_chats_raw(user_id)
        
        now = datetime.now().isoformat()
        
        chat_dict = {
            "id": chat_id,
            "title": title,
            "createdAt": now,
            "lastActivity": now,
            "messageCount": len(messages),
            "messages": messages,
            "isActive": is_active
        }
        
        found = False
        for i, c in enumerate(chats):
            if c.get("id") == chat_id:
                # Сохраняем исходную дату создания
                chat_dict["createdAt"] = c.get("createdAt", now)
                chats[i] = chat_dict
                found = True
                break
                
        if not found:
            chats.append(chat_dict)
            
        try:
            with open(user_file, 'w', encoding='utf-8') as f:
                json.dump(chats, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error("Ошибка записи истории чатов пользователя %d: %s", user_id, e)
            return False
