import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class DataRepository:
    """
    Репозиторий для работы с игровыми данными D&D.
    Отвечает только за чтение и предоставление данных (принцип Single Responsibility).
    """
    def __init__(self, data_path: str = "backend/data"):
        self.data_path = Path(data_path)
        
        # Кэши данных
        self._races_cache: Dict = {}
        self._classes_cache: Dict = {}
        self._backgrounds_cache: Dict = {}
        self._archetypes_cache: Dict = {}
        self._skills_cache: Dict = {}
        self._items_cache: Dict = {}
        self._starting_equipment_cache: Dict = {}
        self._spells_cache: Dict[str, Dict] = {}

    def get_data_path(self) -> Path:
        return self.data_path

    # ========== РАСЫ ==========

    def load_races(self) -> Dict:
        """Загрузить все расы"""
        if self._races_cache:
            return self._races_cache
        
        races_path = self.data_path / "races_structured.json"
        try:
            with open(races_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    tmp: Dict[str, Dict] = {}
                    for entry in data:
                        key = entry.get("source_key") or entry.get("name")
                        if key:
                            tmp[key] = entry
                    self._races_cache = tmp
                else:
                    self._races_cache = data
        except Exception as e:
            logger.error("Ошибка загрузки рас: %s", e)
            self._races_cache = {}
        return self._races_cache

    def _get_race_display_name(self, key: str, data: Any) -> Optional[str]:
        """
        Извлекает отображаемое имя расы из данных.
        Приоритет: поле 'name' → поле 'Название' → сам ключ.
        """
        if isinstance(data, dict):
            name = data.get("name") or data.get("Название")
            if name:
                return name
        # Fallback: используем сам ключ как имя (вместо хрупкого CamelCase-парсинга)
        return key if key else None

    def get_race_names(self) -> List[str]:
        """Получить список названий рас (только русские названия)"""
        races = self.load_races()
        names = []
        for key, data in races.items():
            name = self._get_race_display_name(key, data)
            if name:
                names.append(name)
        return sorted(set(names))

    def get_race_by_name(self, name: str) -> Optional[Dict]:
        """Получить данные расы по названию (точное сравнение)"""
        races = self.load_races()
        for key, data in races.items():
            # Точное сравнение по полю name/Название
            if isinstance(data, dict):
                data_name = data.get("name") or data.get("Название")
                if data_name and data_name == name:
                    return {"key": key, "data": data}
            # Точное сравнение по ключу (case-insensitive)
            if key.lower() == name.lower():
                return {"key": key, "data": data}
        return None

    def get_race_key_by_name(self, name: str) -> Optional[str]:
        """Получить ключ расы по названию (точное сравнение)"""
        races = self.load_races()
        for key, data in races.items():
            # Точное сравнение по полю name/Название
            if isinstance(data, dict):
                data_name = data.get("name") or data.get("Название")
                if data_name and data_name == name:
                    return key
            # Точное сравнение по ключу (case-insensitive)
            if key.lower() == name.lower():
                return key
        return None

    # ========== КЛАССЫ ==========

    def load_classes_structured(self) -> Dict[str, Dict]:
        """Загрузить структурированные данные классов"""
        if self._classes_cache:
            return self._classes_cache
        
        classes_dir = self.data_path / "classes_structured"
        if not classes_dir.exists():
            return {}
        
        for json_file in classes_dir.glob("*.json"):
            if json_file.name == "validation_report.json":
                continue
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    class_id = data.get("id", json_file.stem)
                    self._classes_cache[class_id] = data
            except Exception as e:
                logger.error("Ошибка загрузки класса %s: %s", json_file.name, e)
        
        return self._classes_cache

    def get_class_names(self) -> List[tuple]:
        """Получить список классов [(id, name_ru), ...]"""
        classes = self.load_classes_structured()
        return [(cid, data.get("name", cid)) for cid, data in classes.items()]

    def get_class_by_id(self, class_id: str) -> Optional[Dict]:
        """Получить класс по ID"""
        classes = self.load_classes_structured()
        return classes.get(class_id)

    def get_class_by_name(self, name: str) -> Optional[Dict]:
        """Получить класс по русскому названию"""
        classes = self.load_classes_structured()
        for cid, data in classes.items():
            if data.get("name") == name or data.get("name_en", "").lower() == name.lower():
                return data
        return None

    def is_spellcaster(self, class_id: str) -> bool:
        """
        Определяет, является ли класс заклинателем.
        Проверяет наличие feature с id, содержащим 'spellcasting',
        в данных класса (например, 'spellcasting' у bard, cleric, wizard и т.д.).
        """
        class_data = self.get_class_by_id(class_id)
        if not class_data:
            return False
        features = class_data.get("features", {})
        for level_features in features.values():
            for feature in level_features:
                if isinstance(feature, dict):
                    feature_id = feature.get("id", "")
                    if "spellcasting" in feature_id.lower():
                        return True
        return False

    # ========== ПРЕДЫСТОРИИ ==========

    def load_backgrounds(self) -> Dict:
        """Загрузить все предыстории"""
        if self._backgrounds_cache:
            return self._backgrounds_cache
        
        bg_path = self.data_path / "parsed_backgrounds" / "all_backgrounds_formatted.json"
        try:
            with open(bg_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    tmp = {}
                    for bg in data:
                        if isinstance(bg, dict):
                            bg_id = bg.get("id")
                            if bg_id:
                                tmp[bg_id] = bg
                    self._backgrounds_cache = tmp
                else:
                    self._backgrounds_cache = data
        except Exception as e:
            logger.error("Ошибка загрузки предысторий: %s", e)
            self._backgrounds_cache = {}
        return self._backgrounds_cache

    # ========== ЗАКЛИНАНИЯ ==========

    def load_spells_by_level(self, level: str) -> Dict:
        """Загрузить заклинания по уровню"""
        if level in self._spells_cache:
            return self._spells_cache[level]
        
        spells_dir = self.data_path / "spells_by_level"
        
        if level == "cantrips" or level == "0":
            filename = "spells_cantrips.json"
        else:
            filename = f"spells_level_{level}.json"
        
        file_path = spells_dir / filename
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                spells_data = json.load(f)
                self._spells_cache[level] = spells_data
                return spells_data
        except Exception as e:
            logger.error("Ошибка загрузки заклинаний уровня %s: %s", level, e)
            return {}

    # ========== НАВЫКИ И ПРЕДМЕТЫ ==========
    
    def load_items(self) -> Dict:
        """Загрузить все предметы"""
        if self._items_cache:
            return self._items_cache
        
        items_path = self.data_path / "items.json"
        try:
            with open(items_path, 'r', encoding='utf-8') as f:
                self._items_cache = json.load(f)
        except Exception as e:
            logger.error("Ошибка загрузки предметов: %s", e)
            self._items_cache = {}
        return self._items_cache
    
    def load_skills(self) -> Dict:
        """Загрузить навыки"""
        if self._skills_cache:
            return self._skills_cache
        
        skills_path = self.data_path / "skills.json"
        try:
            with open(skills_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._skills_cache = data.get("skills", data)
        except Exception as e:
            logger.error("Ошибка загрузки навыков: %s", e)
            self._skills_cache = {}
        return self._skills_cache

    def get_skill_name(self, skill_id: str) -> str:
        """Получить русское название навыка по ID"""
        skills = self.load_skills()
        skill = skills.get(skill_id, {})
        return skill.get("name", skill_id)
