import json
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from backend.models.character import Character

logger = logging.getLogger(__name__)


class CharacterRepository:
    """
    Отвечает исключительно за чтение и запись персонажей в файловую систему (БД).
    Реализует паттерн Repository (SRP).
    """
    def __init__(self, data_path: str = "backend/data"):
        self.characters_path = Path(data_path) / "characters"

    def ensure_dir(self):
        self.characters_path.mkdir(parents=True, exist_ok=True)

    def _load_user_characters_raw(self, user_file: Path) -> List[dict]:
        """
        Загружает сырые данные персонажей из файла.
        При повреждённом JSON логирует ошибку и возвращает пустой список
        (вместо молчаливого pass, который мог привести к потере данных).
        """
        if not user_file.exists():
            return []
        try:
            with open(user_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(
                "Повреждённый JSON в файле %s: %s. "
                "Данные НЕ будут перезаписаны для защиты от потери.",
                user_file, e,
            )
            return []
        except Exception as e:
            logger.error("Ошибка чтения файла %s: %s", user_file, e)
            return []

    def save(self, character: Character) -> bool:
        self.ensure_dir()
        
        # Обновляем таймстемпы
        now = datetime.now().isoformat()
        character.updated_at = now
        if not character.created_at:
            character.created_at = now
            
        user_file = self.characters_path / f"user_{character.user_id}.json"
        
        characters = self._load_user_characters_raw(user_file)
        
        # Используем Pydantic метод model_dump для безопасной конвертации в dict
        char_dict = character.model_dump()
        
        found = False
        for i, c in enumerate(characters):
            if c.get("id") == character.id:
                characters[i] = char_dict
                found = True
                break
        
        if not found:
            characters.append(char_dict)
            
        try:
            with open(user_file, 'w', encoding='utf-8') as f:
                json.dump(characters, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error("Ошибка сохранения персонажа: %s", e)
            return False

    def get_by_user(self, user_id: int) -> List[Character]:
        user_file = self.characters_path / f"user_{user_id}.json"
        if not user_file.exists():
            return []
            
        try:
            with open(user_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Используем Pydantic метод model_validate
            return [Character.model_validate(char) for char in data]
        except Exception as e:
            logger.error("Ошибка загрузки персонажей пользователя %d: %s", user_id, e)
            return []

    def get_by_id(self, user_id: int, char_id: str) -> Optional[Character]:
        for char in self.get_by_user(user_id):
            if char.id == char_id:
                return char
        return None

    def delete(self, user_id: int, char_id: str) -> bool:
        user_file = self.characters_path / f"user_{user_id}.json"
        if not user_file.exists():
            return False
            
        try:
            with open(user_file, 'r', encoding='utf-8') as f:
                characters = json.load(f)
            
            initial_len = len(characters)
            characters = [c for c in characters if c.get("id") != char_id]
            
            if len(characters) == initial_len:
                return False
                
            with open(user_file, 'w', encoding='utf-8') as f:
                json.dump(characters, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error("Ошибка удаления персонажа %s: %s", char_id, e)
            return False
