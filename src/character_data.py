"""
Character Data Module - Загрузка и работа с игровыми данными D&D
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Any

# Путь к данным
DATA_PATH = Path(__file__).parent.parent / "data_pars"

# Кэши данных
_races_cache: Dict = {}
_classes_cache: Dict = {}
_backgrounds_cache: Dict = {}
_archetypes_cache: Dict = {}
_skills_cache: Dict = {}
_items_cache: Dict = {}
_starting_equipment_cache: Dict = {}
_spells_cache: Dict[str, Dict] = {}


def get_data_path() -> Path:
    """Получить путь к папке с данными"""
    return DATA_PATH


# ========== РАСЫ ==========

def load_races() -> Dict:
    """Загрузить все расы"""
    global _races_cache
    if _races_cache:
        return _races_cache
    
    races_path = DATA_PATH / "races_structured.json"
    try:
        with open(races_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Если JSON представлен списком, преобразуем в словарь по source_key
            if isinstance(data, list):
                tmp: Dict[str, Dict] = {}
                for entry in data:
                    key = entry.get("source_key") or entry.get("name")
                    if key:
                        tmp[key] = entry
                _races_cache = tmp
            else:
                _races_cache = data
    except Exception as e:
        print(f"❌ Ошибка загрузки рас: {e}")
        _races_cache = {}
    return _races_cache


def get_race_names() -> List[str]:
    """Получить список названий рас (только русские названия)"""
    races = load_races()
    names = []
    # Предпочитаем явно заданное поле "name" в записи
    for key, data in races.items():
        if isinstance(data, dict):
            name = data.get("name") or data.get("Название")
            if name:
                names.append(name)
                continue
        # Фоллбэк: извлечь русскую часть из ключа
        name = ""
        for char in key:
            if char.isupper() and name and name[-1].islower():
                break
            name += char
        if name:
            names.append(name)
    return sorted(set(names))


def get_race_by_name(name: str) -> Optional[Dict]:
    """Получить данные расы по названию"""
    races = load_races()
    for key, data in races.items():
        # Сначала сравниваем с полем name внутри данных
        if isinstance(data, dict):
            data_name = data.get("name") or data.get("Название")
            if data_name and data_name == name:
                return {"key": key, "data": data}
        # Фоллбэк: совпадение по началу ключа
        if key.startswith(name) or key.lower().startswith(name.lower()):
            return {"key": key, "data": data}
    return None


def get_race_key_by_name(name: str) -> Optional[str]:
    """Получить ключ расы по названию"""
    races = load_races()
    for key, data in races.items():
        if isinstance(data, dict):
            data_name = data.get("name") or data.get("Название")
            if data_name and data_name == name:
                return key
        if key.startswith(name) or key.lower().startswith(name.lower()):
            return key
    return None


# ========== КЛАССЫ ==========

def load_classes_structured() -> Dict[str, Dict]:
    """Загрузить структурированные данные классов"""
    global _classes_cache
    if _classes_cache:
        return _classes_cache
    
    classes_dir = DATA_PATH / "classes_structured"
    if not classes_dir.exists():
        return {}
    
    for json_file in classes_dir.glob("*.json"):
        if json_file.name == "validation_report.json":
            continue
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                class_id = data.get("id", json_file.stem)
                _classes_cache[class_id] = data
        except Exception as e:
            print(f"❌ Ошибка загрузки класса {json_file.name}: {e}")
    
    return _classes_cache


def get_class_names() -> List[tuple]:
    """Получить список классов [(id, name_ru), ...]"""
    classes = load_classes_structured()
    return [(cid, data.get("name", cid)) for cid, data in classes.items()]


def get_class_by_id(class_id: str) -> Optional[Dict]:
    """Получить класс по ID"""
    classes = load_classes_structured()
    return classes.get(class_id)


def get_class_by_name(name: str) -> Optional[Dict]:
    """Получить класс по русскому названию"""
    classes = load_classes_structured()
    for cid, data in classes.items():
        if data.get("name") == name or data.get("name_en", "").lower() == name.lower():
            return data
    return None


# ========== АРХЕТИПЫ ==========

def load_archetypes() -> Dict[str, Dict]:
    """Загрузить все архетипы"""
    global _archetypes_cache
    if _archetypes_cache:
        return _archetypes_cache
    
    archetypes_dir = DATA_PATH / "archetypes_structured"
    if not archetypes_dir.exists():
        return {}
    
    for json_file in archetypes_dir.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Извлекаем ключ класса из имени файла.
                # Файлы называются например 'barbarian_archetypes.json' — удаляем суффикс '_archetypes'
                stem = json_file.stem.lower()
                if stem.endswith("_archetypes"):
                    class_key = stem.replace("_archetypes", "")
                else:
                    # Фоллбэк: берём первую часть, разделённую через '-' или '_'
                    class_key = stem.split("-")[0].split("_")[0]
                _archetypes_cache[class_key] = data
        except Exception as e:
            print(f"❌ Ошибка загрузки архетипов {json_file.name}: {e}")
    
    return _archetypes_cache


def get_archetypes_for_class(class_name: str) -> Dict:
    """Получить архетипы для класса"""
    archetypes = load_archetypes()
    # Пробуем найти по точному совпадению или по началу
    class_name_lower = class_name.lower()
    
    if class_name_lower in archetypes:
        return archetypes[class_name_lower]
    
    # Маппинг английских названий на русские
    en_to_ru = {
        "barbarian": "варвар",
        "bard": "бард", 
        "cleric": "жрец",
        "druid": "друид",
        "fighter": "воин",
        "monk": "монах",
        "paladin": "паладин",
        "ranger": "следопыт",
        "rogue": "плут",
        "sorcerer": "чародей",
        "warlock": "колдун",
        "wizard": "волшебник"
    }
    # Попробуем распознать русское имя класса, преобразовав в английский ключ
    ru_to_en = {v: k for k, v in en_to_ru.items()}
    if class_name_lower in ru_to_en:
        return archetypes.get(ru_to_en[class_name_lower], {})

    # Ещё: если передали английское имя с суффиксом (например, 'barbarian_archetypes'), убираем суффикс
    if class_name_lower.endswith("_archetypes"):
        base = class_name_lower.replace("_archetypes", "")
        return archetypes.get(base, {})
    
    return {}


# ========== ПРЕДЫСТОРИИ ==========

def load_backgrounds() -> List[Dict]:
    """Загрузить все предыстории"""
    global _backgrounds_cache
    if _backgrounds_cache:
        return _backgrounds_cache
    
    bg_path = DATA_PATH / "parsed_backgrounds" / "all_backgrounds_formatted.json"
    try:
        with open(bg_path, 'r', encoding='utf-8') as f:
            _backgrounds_cache = json.load(f)
    except Exception as e:
        print(f"❌ Ошибка загрузки предысторий: {e}")
        _backgrounds_cache = []
    return _backgrounds_cache


def get_background_names() -> List[tuple]:
    """Получить список предысторий [(id, name), ...]"""
    backgrounds = load_backgrounds()
    return [(bg.get("id", ""), bg.get("name", "")) for bg in backgrounds]


def get_background_by_id(bg_id: str) -> Optional[Dict]:
    """Получить предысторию по ID"""
    backgrounds = load_backgrounds()
    for bg in backgrounds:
        if bg.get("id") == bg_id:
            return bg
    return None


# ========== НАВЫКИ ==========

def load_skills() -> Dict:
    """Загрузить навыки"""
    global _skills_cache
    if _skills_cache:
        return _skills_cache
    
    skills_path = DATA_PATH / "skills.json"
    try:
        with open(skills_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            _skills_cache = data.get("skills", data)
    except Exception as e:
        print(f"❌ Ошибка загрузки навыков: {e}")
        _skills_cache = {}
    return _skills_cache


def get_skill_name(skill_id: str) -> str:
    """Получить русское название навыка по ID"""
    skills = load_skills()
    skill = skills.get(skill_id, {})
    return skill.get("name", skill_id)


# ========== СНАРЯЖЕНИЕ ==========

def load_items() -> Dict:
    """Загрузить предметы"""
    global _items_cache
    if _items_cache:
        return _items_cache
    
    items_path = DATA_PATH / "items.json"
    try:
        with open(items_path, 'r', encoding='utf-8') as f:
            _items_cache = json.load(f)
    except Exception as e:
        print(f"❌ Ошибка загрузки предметов: {e}")
        _items_cache = {}
    return _items_cache


def load_starting_equipment() -> Dict:
    """Загрузить стартовое снаряжение"""
    global _starting_equipment_cache
    if _starting_equipment_cache:
        return _starting_equipment_cache
    
    eq_path = DATA_PATH / "starting_equipment.json"
    try:
        with open(eq_path, 'r', encoding='utf-8') as f:
            _starting_equipment_cache = json.load(f)
    except Exception as e:
        print(f"❌ Ошибка загрузки снаряжения: {e}")
        _starting_equipment_cache = {}
    return _starting_equipment_cache


def get_item_name(item_id: str) -> str:
    """Получить русское название предмета"""
    items = load_items()
    
    # Ищем в разных категориях
    for category in ["weapons", "armor", "gear", "tools", "packs"]:
        if category in items and item_id in items[category]:
            return items[category][item_id].get("name", item_id)
    
    # Маппинг для стандартных предметов
    item_names = {
        # Наборы
        "explorer_pack": "Набор путешественника",
        "diplomat_pack": "Набор дипломата",
        "entertainer_pack": "Набор артиста",
        "priest_pack": "Набор священника",
        "scholar_pack": "Набор учёного",
        "dungeoneer_pack": "Набор исследователя подземелий",
        "burglar_pack": "Набор взломщика",
        
        # Доспехи
        "leather_armor": "Кожаный доспех",
        "studded_leather_armor": "Проклёпанный кожаный доспех",
        "scale_mail": "Чешуйчатый доспех",
        "chain_mail": "Кольчуга",
        "shield": "Щит",
        
        # Магические предметы
        "holy_symbol": "Священный символ",
        "druidic_focus": "Друидический фокус",
        "component_pouch": "Мешочек компонентов",
        "arcane_focus": "Тайный фокус",
        "spellbook": "Книга заклинаний",
        
        # Инструменты
        "lute": "Лютня",
        "musical_instrument": "Музыкальный инструмент",
        "thieves_tools": "Воровские инструменты",
        
        # Оружие
        "dagger": "Кинжал",
        "quarterstaff": "Боевой посох",
        "mace": "Булава",
        "warhammer": "Боевой молот",
        "scimitar": "Скимитар",
        "rapier": "Рапира",
        "longsword": "Длинный меч",
        "shortsword": "Короткий меч",
        "javelin": "Метательное копьё",
        "greataxe": "Секира",
        "greatsword": "Двуручный меч",
        "handaxe": "Ручной топор",
        "dart": "Дротик",
        "light_crossbow": "Лёгкий арбалет",
        "shortbow": "Короткий лук",
        "longbow": "Длинный лук",
        "crossbow_bolts_20": "20 арбалетных болтов",
        "arrows_20": "20 стрел",
        "quiver": "Колчан",
        
        # Категории оружия
        "martial_melee_weapon": "Воинское рукопашное оружие",
        "martial_weapon": "Воинское оружие",
        "simple_weapon": "Простое оружие",
        "simple_melee_weapon": "Простое рукопашное оружие",
    }
    
    return item_names.get(item_id, item_id)


# ========== ЗАКЛИНАНИЯ ==========

def load_spells_by_level(level: str) -> Dict:
    """Загрузить заклинания по уровню"""
    global _spells_cache
    
    if level in _spells_cache:
        return _spells_cache[level]
    
    spells_dir = DATA_PATH / "spells_by_level"
    
    if level == "cantrips" or level == "0":
        filename = "spells_cantrips.json"
    else:
        filename = f"spells_level_{level}.json"
    
    file_path = spells_dir / filename
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            spells_data = json.load(f)
            _spells_cache[level] = spells_data
            return spells_data
    except Exception as e:
        print(f"❌ Ошибка загрузки заклинаний уровня {level}: {e}")
        return {}


def get_spells_for_class(class_name: str, max_level: int = 9) -> Dict[str, List[str]]:
    """Получить заклинания доступные классу по уровням"""
    class_name_lower = class_name.lower()
    
    # Маппинг английских id классов в русские названия (как в JSON)
    en_to_ru = {
        "wizard": "волшебник",
        "bard": "бард",
        "cleric": "жрец",
        "druid": "друид",
        "paladin": "паладин",
        "ranger": "следопыт",
        "sorcerer": "чародей",
        "warlock": "колдун",
        "artificer": "изобретатель"
    }
    
    # Маппинг русских названий (на случай если передали по-русски)
    ru_to_class = {
        "волшебник": "волшебник",
        "бард": "бард",
        "жрец": "жрец",
        "друид": "друид",
        "паладин": "паладин",
        "следопыт": "следопыт",
        "чародей": "чародей",
        "колдун": "колдун",
        "изобретатель": "изобретатель"
    }
    
    # Сначала пробуем английский id, потом русское название
    search_class = en_to_ru.get(class_name_lower, ru_to_class.get(class_name_lower, class_name_lower))
    
    result = {}
    
    # Загружаем заговоры и заклинания 1-9 уровней
    levels = ["cantrips"] + [str(i) for i in range(1, max_level + 1)]
    
    for level in levels:
        spells = load_spells_by_level(level)
        level_spells = []
        
        for spell_name, spell_data in spells.items():
            classes_str = spell_data.get("Классы", "").lower()
            if search_class in classes_str:
                level_spells.append(spell_name)
        
        if level_spells:
            result[level] = sorted(level_spells)
    
    return result


# ========== ТАБЛИЦЫ ЗАКЛИНАНИЙ ==========

# Таблицы прогрессии заклинаний для каждого класса
SPELLCASTING_TABLES = {
    "bard": {
        "type": "full",  # полный заклинатель
        "ability": "cha",
        "cantrips": {1: 2, 4: 3, 10: 4},
        "spells_known": {1: 4, 2: 5, 3: 6, 4: 7, 5: 8, 6: 9, 7: 10, 8: 11, 9: 12, 10: 14, 
                        11: 15, 13: 16, 14: 18, 15: 19, 17: 20, 18: 22},
        "slots": {
            1: {1: 2}, 2: {1: 3}, 3: {1: 4, 2: 2}, 4: {1: 4, 2: 3}, 5: {1: 4, 2: 3, 3: 2},
            6: {1: 4, 2: 3, 3: 3}, 7: {1: 4, 2: 3, 3: 3, 4: 1}, 8: {1: 4, 2: 3, 3: 3, 4: 2},
            9: {1: 4, 2: 3, 3: 3, 4: 3, 5: 1}, 10: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2},
            11: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1}, 12: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1},
            13: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1}, 14: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1},
            15: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1}, 16: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1},
            17: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1, 9: 1}, 18: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 1, 7: 1, 8: 1, 9: 1},
            19: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 1, 8: 1, 9: 1}, 20: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 2, 8: 1, 9: 1}
        }
    },
    "cleric": {
        "type": "full",
        "ability": "wis",
        "cantrips": {1: 3, 4: 4, 10: 5},
        "prepared": True,  # готовит заклинания
        "slots": {
            1: {1: 2}, 2: {1: 3}, 3: {1: 4, 2: 2}, 4: {1: 4, 2: 3}, 5: {1: 4, 2: 3, 3: 2},
            6: {1: 4, 2: 3, 3: 3}, 7: {1: 4, 2: 3, 3: 3, 4: 1}, 8: {1: 4, 2: 3, 3: 3, 4: 2},
            9: {1: 4, 2: 3, 3: 3, 4: 3, 5: 1}, 10: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2},
            11: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1}, 12: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1},
            13: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1}, 14: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1},
            15: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1}, 16: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1},
            17: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1, 9: 1}, 18: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 1, 7: 1, 8: 1, 9: 1},
            19: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 1, 8: 1, 9: 1}, 20: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 2, 8: 1, 9: 1}
        }
    },
    "druid": {
        "type": "full",
        "ability": "wis",
        "cantrips": {1: 2, 4: 3, 10: 4},
        "prepared": True,
        "slots": {
            1: {1: 2}, 2: {1: 3}, 3: {1: 4, 2: 2}, 4: {1: 4, 2: 3}, 5: {1: 4, 2: 3, 3: 2},
            6: {1: 4, 2: 3, 3: 3}, 7: {1: 4, 2: 3, 3: 3, 4: 1}, 8: {1: 4, 2: 3, 3: 3, 4: 2},
            9: {1: 4, 2: 3, 3: 3, 4: 3, 5: 1}, 10: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2},
            11: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1}, 12: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1},
            13: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1}, 14: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1},
            15: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1}, 16: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1},
            17: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1, 9: 1}, 18: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 1, 7: 1, 8: 1, 9: 1},
            19: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 1, 8: 1, 9: 1}, 20: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 2, 8: 1, 9: 1}
        }
    },
    "sorcerer": {
        "type": "full",
        "ability": "cha",
        "cantrips": {1: 4, 4: 5, 10: 6},
        "spells_known": {1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9, 9: 10, 10: 11, 
                        11: 12, 13: 13, 15: 14, 17: 15},
        "slots": {
            1: {1: 2}, 2: {1: 3}, 3: {1: 4, 2: 2}, 4: {1: 4, 2: 3}, 5: {1: 4, 2: 3, 3: 2},
            6: {1: 4, 2: 3, 3: 3}, 7: {1: 4, 2: 3, 3: 3, 4: 1}, 8: {1: 4, 2: 3, 3: 3, 4: 2},
            9: {1: 4, 2: 3, 3: 3, 4: 3, 5: 1}, 10: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2},
            11: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1}, 12: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1},
            13: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1}, 14: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1},
            15: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1}, 16: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1},
            17: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1, 9: 1}, 18: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 1, 7: 1, 8: 1, 9: 1},
            19: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 1, 8: 1, 9: 1}, 20: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 2, 8: 1, 9: 1}
        }
    },
    "warlock": {
        "type": "pact",  # магия договора (особая система)
        "ability": "cha",
        "cantrips": {1: 2, 4: 3, 10: 4},
        "spells_known": {1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9, 9: 10, 11: 11, 
                        13: 12, 15: 13, 17: 14, 19: 15},
        "pact_slots": {
            1: {"count": 1, "level": 1}, 2: {"count": 2, "level": 1},
            3: {"count": 2, "level": 2}, 4: {"count": 2, "level": 2},
            5: {"count": 2, "level": 3}, 6: {"count": 2, "level": 3},
            7: {"count": 2, "level": 4}, 8: {"count": 2, "level": 4},
            9: {"count": 2, "level": 5}, 10: {"count": 2, "level": 5},
            11: {"count": 3, "level": 5}, 12: {"count": 3, "level": 5},
            13: {"count": 3, "level": 5}, 14: {"count": 3, "level": 5},
            15: {"count": 3, "level": 5}, 16: {"count": 3, "level": 5},
            17: {"count": 4, "level": 5}, 18: {"count": 4, "level": 5},
            19: {"count": 4, "level": 5}, 20: {"count": 4, "level": 5}
        }
    },
    "wizard": {
        "type": "full",
        "ability": "int",
        "cantrips": {1: 3, 4: 4, 10: 5},
        "spellbook": True,  # использует книгу заклинаний
        "spells_in_book": {1: 6},  # начальные заклинания в книге
        "spells_per_level": 2,  # заклинания добавляемые при повышении уровня
        "slots": {
            1: {1: 2}, 2: {1: 3}, 3: {1: 4, 2: 2}, 4: {1: 4, 2: 3}, 5: {1: 4, 2: 3, 3: 2},
            6: {1: 4, 2: 3, 3: 3}, 7: {1: 4, 2: 3, 3: 3, 4: 1}, 8: {1: 4, 2: 3, 3: 3, 4: 2},
            9: {1: 4, 2: 3, 3: 3, 4: 3, 5: 1}, 10: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2},
            11: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1}, 12: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1},
            13: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1}, 14: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1},
            15: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1}, 16: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1},
            17: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1, 9: 1}, 18: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 1, 7: 1, 8: 1, 9: 1},
            19: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 1, 8: 1, 9: 1}, 20: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 2, 8: 1, 9: 1}
        }
    },
    "paladin": {
        "type": "half",  # полузаклинатель
        "ability": "cha",
        "prepared": True,
        "start_level": 2,  # получает заклинания с 2 уровня
        "slots": {
            2: {1: 2}, 3: {1: 3}, 4: {1: 3}, 5: {1: 4, 2: 2},
            6: {1: 4, 2: 2}, 7: {1: 4, 2: 3}, 8: {1: 4, 2: 3},
            9: {1: 4, 2: 3, 3: 2}, 10: {1: 4, 2: 3, 3: 2},
            11: {1: 4, 2: 3, 3: 3}, 12: {1: 4, 2: 3, 3: 3},
            13: {1: 4, 2: 3, 3: 3, 4: 1}, 14: {1: 4, 2: 3, 3: 3, 4: 1},
            15: {1: 4, 2: 3, 3: 3, 4: 2}, 16: {1: 4, 2: 3, 3: 3, 4: 2},
            17: {1: 4, 2: 3, 3: 3, 4: 3, 5: 1}, 18: {1: 4, 2: 3, 3: 3, 4: 3, 5: 1},
            19: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2}, 20: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2}
        }
    },
    "ranger": {
        "type": "half",
        "ability": "wis",
        "start_level": 2,
        "spells_known": {2: 2, 3: 3, 5: 4, 7: 5, 9: 6, 11: 7, 13: 8, 15: 9, 17: 10, 19: 11},
        "slots": {
            2: {1: 2}, 3: {1: 3}, 4: {1: 3}, 5: {1: 4, 2: 2},
            6: {1: 4, 2: 2}, 7: {1: 4, 2: 3}, 8: {1: 4, 2: 3},
            9: {1: 4, 2: 3, 3: 2}, 10: {1: 4, 2: 3, 3: 2},
            11: {1: 4, 2: 3, 3: 3}, 12: {1: 4, 2: 3, 3: 3},
            13: {1: 4, 2: 3, 3: 3, 4: 1}, 14: {1: 4, 2: 3, 3: 3, 4: 1},
            15: {1: 4, 2: 3, 3: 3, 4: 2}, 16: {1: 4, 2: 3, 3: 3, 4: 2},
            17: {1: 4, 2: 3, 3: 3, 4: 3, 5: 1}, 18: {1: 4, 2: 3, 3: 3, 4: 3, 5: 1},
            19: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2}, 20: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2}
        }
    },
    "artificer": {
        "type": "half",
        "ability": "int",
        "cantrips": {1: 2, 10: 3, 14: 4},
        "prepared": True,
        "slots": {
            1: {1: 2}, 2: {1: 2}, 3: {1: 3}, 4: {1: 3}, 5: {1: 4, 2: 2},
            6: {1: 4, 2: 2}, 7: {1: 4, 2: 3}, 8: {1: 4, 2: 3},
            9: {1: 4, 2: 3, 3: 2}, 10: {1: 4, 2: 3, 3: 2},
            11: {1: 4, 2: 3, 3: 3}, 12: {1: 4, 2: 3, 3: 3},
            13: {1: 4, 2: 3, 3: 3, 4: 1}, 14: {1: 4, 2: 3, 3: 3, 4: 1},
            15: {1: 4, 2: 3, 3: 3, 4: 2}, 16: {1: 4, 2: 3, 3: 3, 4: 2},
            17: {1: 4, 2: 3, 3: 3, 4: 3, 5: 1}, 18: {1: 4, 2: 3, 3: 3, 4: 3, 5: 1},
            19: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2}, 20: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2}
        }
    }
}

# Классы без магии
NON_SPELLCASTERS = ["barbarian", "fighter", "monk", "rogue"]


def get_spellcasting_info(class_id: str, level: int) -> Optional[Dict]:
    """Получить информацию о заклинательных способностях класса на уровне"""
    if class_id in NON_SPELLCASTERS:
        return None
    
    table = SPELLCASTING_TABLES.get(class_id)
    if not table:
        return None
    
    # Проверяем минимальный уровень для получения заклинаний
    start_level = table.get("start_level", 1)
    if level < start_level:
        return None
    
    info = {
        "type": table["type"],
        "ability": table["ability"],
        "prepared": table.get("prepared", False),
        "spellbook": table.get("spellbook", False)
    }
    
    # Получаем количество заговоров
    if "cantrips" in table:
        cantrips = 0
        for lvl, count in sorted(table["cantrips"].items()):
            if level >= lvl:
                cantrips = count
        info["cantrips"] = cantrips
    
    # Получаем известные заклинания
    if "spells_known" in table:
        spells_known = 0
        for lvl, count in sorted(table["spells_known"].items()):
            if level >= lvl:
                spells_known = count
        info["spells_known"] = spells_known
    
    # Получаем ячейки заклинаний
    if table["type"] == "pact":
        pact_info = table["pact_slots"].get(level, {"count": 0, "level": 0})
        info["pact_slots"] = pact_info
    else:
        slots = table.get("slots", {}).get(level, {})
        info["slots"] = slots
    
    # Максимальный уровень заклинаний
    if table["type"] == "pact":
        info["max_spell_level"] = table["pact_slots"].get(level, {}).get("level", 0)
    elif info.get("slots"):
        info["max_spell_level"] = max(info["slots"].keys())
    else:
        info["max_spell_level"] = 0
    
    return info


def is_spellcaster(class_id: str) -> bool:
    """Проверить, является ли класс заклинателем"""
    return class_id not in NON_SPELLCASTERS


# ========== МОДИФИКАТОРЫ ХАРАКТЕРИСТИК ==========

def calculate_modifier(score: int) -> int:
    """Рассчитать модификатор характеристики"""
    return (score - 10) // 2


def get_proficiency_bonus(level: int) -> int:
    """Получить бонус мастерства по уровню"""
    return (level - 1) // 4 + 2


# ========== ОПЫТ ==========

XP_TABLE = {
    1: 0, 2: 300, 3: 900, 4: 2700, 5: 6500,
    6: 14000, 7: 23000, 8: 34000, 9: 48000, 10: 64000,
    11: 85000, 12: 100000, 13: 120000, 14: 140000, 15: 165000,
    16: 195000, 17: 225000, 18: 265000, 19: 305000, 20: 355000
}


def get_level_from_xp(xp: int) -> int:
    """Определить уровень по опыту"""
    for level in range(20, 0, -1):
        if xp >= XP_TABLE[level]:
            return level
    return 1


def get_xp_for_level(level: int) -> int:
    """Получить требуемый опыт для уровня"""
    return XP_TABLE.get(level, 0)
