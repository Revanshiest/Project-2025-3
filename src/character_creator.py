"""
Character Creator Module - Создание и управление персонажами D&D
"""
import json
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

from .character_data import (
    load_races, get_race_by_name, get_race_names,
    load_classes_structured, get_class_by_id, get_class_names,
    load_backgrounds, get_background_by_id, get_background_names,
    load_skills, get_skill_name,
    load_starting_equipment, get_item_name,
    get_archetypes_for_class,
    get_spellcasting_info, is_spellcaster, get_spells_for_class,
    calculate_modifier, get_proficiency_bonus, get_xp_for_level, get_level_from_xp,
    SPELLCASTING_TABLES, NON_SPELLCASTERS
)


# Путь для сохранения персонажей
CHARACTERS_PATH = Path(__file__).parent.parent / "data" / "characters"


class CreationStep(Enum):
    """Этапы создания персонажа"""
    START = "start"
    RACE = "race"
    CLASS = "class"
    BACKGROUND = "background"
    ABILITIES_METHOD = "abilities_method"
    ABILITIES_ASSIGN = "abilities_assign"
    ABILITIES_POINT_BUY = "abilities_point_buy"
    ABILITIES_ROLL = "abilities_roll"
    SKILLS = "skills"
    EQUIPMENT = "equipment"
    SPELLS_CANTRIPS = "spells_cantrips"
    SPELLS_KNOWN = "spells_known"
    NAME = "name"
    REVIEW = "review"
    COMPLETE = "complete"


@dataclass
class CharacterSpells:
    """Информация о заклинаниях персонажа"""
    cantrips: List[str] = field(default_factory=list)
    known_spells: List[str] = field(default_factory=list)
    prepared_spells: List[str] = field(default_factory=list)
    spellbook: List[str] = field(default_factory=list)  # для волшебника
    max_cantrips: int = 0
    max_known: int = 0
    max_prepared: int = 0
    spell_slots: Dict[int, int] = field(default_factory=dict)
    spell_slots_used: Dict[int, int] = field(default_factory=dict)
    spellcasting_ability: str = ""
    spell_save_dc: int = 0
    spell_attack_bonus: int = 0


@dataclass 
class Character:
    """Класс персонажа D&D"""
    # Базовая информация
    id: str = ""
    user_id: int = 0
    name: str = ""
    
    # Раса
    race_key: str = ""
    race_name: str = ""
    
    # Класс
    class_id: str = ""
    class_name: str = ""
    
    # Архетип (подкласс)
    archetype_name: str = ""
    
    # Предыстория
    background_id: str = ""
    background_name: str = ""
    
    # Уровень и опыт
    level: int = 1
    experience: int = 0
    proficiency_bonus: int = 2
    
    # Характеристики
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10
    
    # Модификаторы (вычисляются автоматически)
    str_mod: int = 0
    dex_mod: int = 0
    con_mod: int = 0
    int_mod: int = 0
    wis_mod: int = 0
    cha_mod: int = 0
    
    # Хиты
    max_hp: int = 0
    current_hp: int = 0
    temp_hp: int = 0
    hit_dice: str = ""
    hit_dice_remaining: int = 0
    
    # Класс доспеха и скорость
    armor_class: int = 10
    speed: int = 30
    
    # Владения
    armor_proficiencies: List[str] = field(default_factory=list)
    weapon_proficiencies: List[str] = field(default_factory=list)
    tool_proficiencies: List[str] = field(default_factory=list)
    saving_throws: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)
    
    # Снаряжение
    equipment: List[str] = field(default_factory=list)
    gold: int = 0
    
    # Способности класса
    features: List[Dict] = field(default_factory=list)
    
    # Заклинания
    spells: CharacterSpells = field(default_factory=CharacterSpells)
    
    # Черты расы
    racial_traits: List[str] = field(default_factory=list)

    # Выданные способности/гранты (id -> {name, uses_total, uses_remaining, recharge, action_type, description, source})
    granted_abilities: Dict[str, Dict] = field(default_factory=dict)
    
    # Черты предыстории
    personality_traits: List[str] = field(default_factory=list)
    ideals: List[str] = field(default_factory=list)
    bonds: List[str] = field(default_factory=list)
    flaws: List[str] = field(default_factory=list)
    background_feature: str = ""
    
    # Метаданные
    created_at: str = ""
    updated_at: str = ""
    
    def __post_init__(self):
        """Вычислить производные значения"""
        self.update_modifiers()
    
    def update_modifiers(self):
        """Обновить модификаторы характеристик"""
        self.str_mod = calculate_modifier(self.strength)
        self.dex_mod = calculate_modifier(self.dexterity)
        self.con_mod = calculate_modifier(self.constitution)
        self.int_mod = calculate_modifier(self.intelligence)
        self.wis_mod = calculate_modifier(self.wisdom)
        self.cha_mod = calculate_modifier(self.charisma)
        self.proficiency_bonus = get_proficiency_bonus(self.level)
    
    def calculate_hp(self):
        """Рассчитать максимальные хиты"""
        if not self.hit_dice:
            return
        
        # Парсим кость хитов (например, "1d10" -> 10)
        dice_value = int(self.hit_dice.split("d")[1])
        
        # На первом уровне - максимум кости + модификатор Телосложения
        self.max_hp = dice_value + self.con_mod
        
        # На каждом последующем уровне добавляем среднее значение + мод Тел
        for _ in range(2, self.level + 1):
            avg_roll = (dice_value // 2) + 1
            self.max_hp += avg_roll + self.con_mod
        
        # Минимум 1 HP
        self.max_hp = max(1, self.max_hp)
        self.current_hp = self.max_hp
        self.hit_dice_remaining = self.level
    
    def update_spell_info(self):
        """Обновить информацию о заклинаниях"""
        spell_info = get_spellcasting_info(self.class_id, self.level)
        if not spell_info:
            return
        
        self.spells.spellcasting_ability = spell_info["ability"]
        
        # Определяем модификатор заклинательной характеристики
        ability_mods = {
            "str": self.str_mod, "dex": self.dex_mod, "con": self.con_mod,
            "int": self.int_mod, "wis": self.wis_mod, "cha": self.cha_mod
        }
        spell_mod = ability_mods.get(spell_info["ability"], 0)
        
        self.spells.spell_save_dc = 8 + self.proficiency_bonus + spell_mod
        self.spells.spell_attack_bonus = self.proficiency_bonus + spell_mod
        
        # Обновляем количество заговоров и известных заклинаний
        self.spells.max_cantrips = spell_info.get("cantrips", 0)
        self.spells.max_known = spell_info.get("spells_known", 0)
        
        # Для подготавливающих классов
        if spell_info.get("prepared"):
            # Количество подготовленных = мод характеристики + уровень класса (минимум 1)
            self.spells.max_prepared = max(1, spell_mod + self.level)
        
        # Ячейки заклинаний
        if spell_info["type"] == "pact":
            pact = spell_info.get("pact_slots", {})
            self.spells.spell_slots = {pact.get("level", 1): pact.get("count", 0)}
        else:
            self.spells.spell_slots = spell_info.get("slots", {})
        
        # Сброс использованных ячеек
        self.spells.spell_slots_used = {k: 0 for k in self.spells.spell_slots.keys()}
    
    def to_dict(self) -> Dict:
        """Преобразовать в словарь для сохранения"""
        data = asdict(self)
        # Преобразуем CharacterSpells в dict
        if isinstance(data.get("spells"), dict):
            pass  # уже словарь
        # granted_abilities уже словарь
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Character":
        """Создать из словаря"""
        # Обработка spells
        spells_data = data.pop("spells", {})
        if isinstance(spells_data, dict):
            spells = CharacterSpells(**spells_data)
        else:
            spells = CharacterSpells()
        # granted_abilities остаются как словарь в data
        char = cls(**data)
        char.spells = spells
        return char


@dataclass
class CreationSession:
    """Сессия создания персонажа"""
    user_id: int
    step: CreationStep = CreationStep.START
    character: Character = field(default_factory=Character)
    
    # Временные данные для выбора
    available_skills: List[str] = field(default_factory=list)
    skills_to_choose: int = 0
    selected_skills: List[str] = field(default_factory=list)
    
    # Для распределения характеристик
    ability_scores: List[int] = field(default_factory=list)
    point_buy_points: int = 27
    ability_assignments: Dict[str, int] = field(default_factory=dict)
    
    # Для выбора снаряжения
    equipment_choices: List[Dict] = field(default_factory=list)  # Варианты выбора из starting_equipment
    current_equipment_choice: int = 0  # Индекс текущего выбора
    selected_equipment: List[List[str]] = field(default_factory=list)  # Выбранные варианты для каждого choice
    take_gold_instead: bool = False  # Взять золото вместо снаряжения
    
    # Для выбора заклинаний
    available_cantrips: List[str] = field(default_factory=list)
    available_spells: Dict[str, List[str]] = field(default_factory=dict)
    cantrips_to_choose: int = 0
    spells_to_choose: int = 0
    selected_cantrips: List[str] = field(default_factory=list)
    selected_spells: List[str] = field(default_factory=list)
    
    # Пагинация
    current_page: int = 1
    items_per_page: int = 8


# Хранилище активных сессий создания
_creation_sessions: Dict[int, CreationSession] = {}


def get_creation_session(user_id: int) -> Optional[CreationSession]:
    """Получить сессию создания"""
    return _creation_sessions.get(user_id)


def create_session(user_id: int) -> CreationSession:
    """Создать новую сессию создания"""
    session = CreationSession(user_id=user_id)
    session.character.user_id = user_id
    session.character.id = f"{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    session.character.created_at = datetime.now().isoformat()
    _creation_sessions[user_id] = session
    return session


def delete_session(user_id: int):
    """Удалить сессию создания"""
    if user_id in _creation_sessions:
        del _creation_sessions[user_id]


# ========== МЕТОДЫ ГЕНЕРАЦИИ ХАРАКТЕРИСТИК ==========

def roll_abilities() -> List[int]:
    """Бросить 4d6, отбросить наименьший для каждой характеристики"""
    scores = []
    for _ in range(6):
        rolls = sorted([random.randint(1, 6) for _ in range(4)], reverse=True)
        score = sum(rolls[:3])  # сумма трёх лучших
        scores.append(score)
    return sorted(scores, reverse=True)


def get_standard_array() -> List[int]:
    """Получить стандартный набор характеристик"""
    return [15, 14, 13, 12, 10, 8]


def get_point_buy_cost(score: int) -> int:
    """Получить стоимость значения характеристики в системе покупки очков"""
    costs = {8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9}
    return costs.get(score, 0)


def validate_point_buy(scores: Dict[str, int], total_points: int = 27) -> bool:
    """Проверить валидность распределения очков"""
    total_cost = sum(get_point_buy_cost(s) for s in scores.values())
    return total_cost <= total_points and all(8 <= s <= 15 for s in scores.values())


# ========== ПРИМЕНЕНИЕ РАСОВЫХ БОНУСОВ ==========

def apply_racial_bonuses(character: Character, race_data: Dict):
    """Применить расовые бонусы к персонажу"""
    # Ищем бонусы к характеристикам
    ability_increase = race_data.get("Увеличение характеристик", "")
    
    if ability_increase:
        # Парсим строку вида "Значение вашей Силы увеличивается на 2..."
        ability_map = {
            "Сил": "strength", "Ловкост": "dexterity", "Телосложени": "constitution",
            "Интеллект": "intelligence", "Мудрост": "wisdom", "Харизм": "charisma"
        }
        
        for ru_name, en_name in ability_map.items():
            if ru_name in ability_increase:
                # Ищем числа
                import re
                numbers = re.findall(r'увеличивается на (\d+)', ability_increase)
                if numbers:
                    bonus = int(numbers[0])
                    current = getattr(character, en_name, 10)
                    setattr(character, en_name, current + bonus)
    
    # Скорость
    speed_text = race_data.get("Скорость", "")
    if speed_text:
        import re
        speed_match = re.search(r'(\d+)\s*фут', speed_text)
        if speed_match:
            character.speed = int(speed_match.group(1))
    
    # Языки
    languages = race_data.get("Язык", race_data.get("Языки", ""))
    if languages:
        # Простой парсинг языков
        common_langs = ["Общий", "Эльфийский", "Дварфийский", "Орочий", "Гоблинский", 
                       "Гигантский", "Драконий", "Бездны", "Инфернальный", "Небесный"]
        for lang in common_langs:
            if lang.lower() in languages.lower():
                character.languages.append(lang)
        if not character.languages:
            character.languages.append("Общий")
    
    # Особенности расы
    # Особенности расы: берем только поле 'traits' (имена и описания)
    traits = race_data.get("traits") or race_data.get("особенности") or []
    if traits and isinstance(traits, list):
        for t in traits:
            if isinstance(t, dict):
                tname = t.get("name") or t.get("Название") or ""
                tdesc = t.get("description") or t.get("Описание") or ""
                if tname and tdesc:
                    character.racial_traits.append(f"{tname}: {tdesc}")
                elif tname:
                    character.racial_traits.append(tname)
                elif tdesc:
                    character.racial_traits.append(tdesc)
            elif isinstance(t, str):
                character.racial_traits.append(t)


# ========== ПРИМЕНЕНИЕ КЛАССА ==========

def apply_class_features(character: Character, class_data: Dict, level: int = 1):
    """Применить особенности класса"""
    character.hit_dice = class_data.get("hit_dice", "1d8")
    character.saving_throws = class_data.get("saving_throws", [])
    character.armor_proficiencies = class_data.get("armor_proficiencies", [])
    character.weapon_proficiencies = class_data.get("weapon_proficiencies", [])
    character.tool_proficiencies.extend(class_data.get("tool_proficiencies", []))
    
    # Применяем способности для уровней 1 до level
    features = class_data.get("features", {})
    for lvl in range(1, level + 1):
        lvl_features = features.get(str(lvl), [])
        for feature in lvl_features:
            if isinstance(feature, dict):
                character.features.append({
                    "level": lvl,
                    "name": feature.get("name", ""),
                    "description": feature.get("description", "")
                })


# ========== ПРИМЕНЕНИЕ ПРЕДЫСТОРИИ ==========

def apply_background(character: Character, background_data: Dict):
    """Применить предысторию"""
    character.background_name = background_data.get("name", "")
    
    # Навыки
    skill_profs = background_data.get("skill_proficiencies", {})
    fixed_skills = skill_profs.get("fixed", [])
    for skill in fixed_skills:
        if skill not in character.skills:
            character.skills.append(skill)
    
    # Языки
    lang_info = background_data.get("languages", {})
    # Добавим позже при выборе
    
    # Снаряжение и золото
    equipment = background_data.get("equipment", {})
    character.gold += equipment.get("gold", 0)
    
    # Особенность предыстории
    feature = background_data.get("feature", {})
    character.background_feature = f"{feature.get('name', '')}: {feature.get('description', '')[:300]}"


# ========== СОХРАНЕНИЕ И ЗАГРУЗКА ==========

def ensure_characters_dir():
    """Создать директорию для персонажей если её нет"""
    CHARACTERS_PATH.mkdir(parents=True, exist_ok=True)


def save_character(character: Character) -> bool:
    """Сохранить персонажа в JSON"""
    ensure_characters_dir()
    
    character.updated_at = datetime.now().isoformat()
    
    # Файл для пользователя
    user_file = CHARACTERS_PATH / f"user_{character.user_id}.json"
    
    # Загружаем существующих персонажей пользователя
    characters = []
    if user_file.exists():
        try:
            with open(user_file, 'r', encoding='utf-8') as f:
                characters = json.load(f)
        except:
            characters = []
    
    # Обновляем или добавляем персонажа
    found = False
    for i, char in enumerate(characters):
        if char.get("id") == character.id:
            characters[i] = character.to_dict()
            found = True
            break
    
    if not found:
        characters.append(character.to_dict())
    
    # Сохраняем
    try:
        with open(user_file, 'w', encoding='utf-8') as f:
            json.dump(characters, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения персонажа: {e}")
        return False


def load_user_characters(user_id: int) -> List[Character]:
    """Загрузить персонажей пользователя"""
    user_file = CHARACTERS_PATH / f"user_{user_id}.json"
    
    if not user_file.exists():
        return []
    
    try:
        with open(user_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return [Character.from_dict(char) for char in data]
    except Exception as e:
        print(f"❌ Ошибка загрузки персонажей: {e}")
        return []


def get_character_by_id(user_id: int, char_id: str) -> Optional[Character]:
    """Получить персонажа по ID"""
    characters = load_user_characters(user_id)
    for char in characters:
        if char.id == char_id:
            return char
    return None


def delete_character(user_id: int, char_id: str) -> bool:
    """Удалить персонажа"""
    user_file = CHARACTERS_PATH / f"user_{user_id}.json"
    
    if not user_file.exists():
        return False
    
    try:
        with open(user_file, 'r', encoding='utf-8') as f:
            characters = json.load(f)
        
        characters = [c for c in characters if c.get("id") != char_id]
        
        with open(user_file, 'w', encoding='utf-8') as f:
            json.dump(characters, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ Ошибка удаления персонажа: {e}")
        return False


# ========== ФОРМАТИРОВАНИЕ ПЕРСОНАЖА ==========

def format_character_summary(character: Character) -> str:
    """Форматировать краткую информацию о персонаже"""
    character.update_modifiers()
    
    text = f"<b>📜 {character.name}</b>\n"
    text += f"<i>{character.race_name} • {character.class_name}</i>\n"
    if character.archetype_name:
        text += f"<i>Архетип: {character.archetype_name}</i>\n"
    text += f"Уровень: {character.level} | XP: {character.experience}\n"
    text += f"❤️ HP: {character.current_hp}/{character.max_hp}\n"
    
    return text


def format_character_full(character: Character) -> str:
    """Форматировать полную информацию о персонаже"""
    character.update_modifiers()
    character.update_spell_info()
    
    lines = []
    lines.append(f"<b>📜 {character.name}</b>")
    lines.append(f"<i>{character.race_name} • {character.class_name} {character.level}</i>")
    
    if character.archetype_name:
        lines.append(f"🎭 Архетип: {character.archetype_name}")
    
    if character.background_name:
        lines.append(f"📖 Предыстория: {character.background_name}")
    
    lines.append("")
    lines.append(f"<b>⚔️ Характеристики:</b>")
    lines.append(f"СИЛ: {character.strength} ({character.str_mod:+d}) | ЛОВ: {character.dexterity} ({character.dex_mod:+d})")
    lines.append(f"ТЕЛ: {character.constitution} ({character.con_mod:+d}) | ИНТ: {character.intelligence} ({character.int_mod:+d})")
    lines.append(f"МДР: {character.wisdom} ({character.wis_mod:+d}) | ХАР: {character.charisma} ({character.cha_mod:+d})")
    
    lines.append("")
    lines.append(f"<b>❤️ Хиты:</b> {character.current_hp}/{character.max_hp}")
    lines.append(f"<b>🛡️ КД:</b> {character.armor_class} | <b>🏃 Скорость:</b> {character.speed} фт")
    lines.append(f"<b>⭐ Бонус мастерства:</b> +{character.proficiency_bonus}")
    
    # Навыки
    if character.skills:
        lines.append("")
        lines.append(f"<b>📚 Навыки:</b>")
        skill_names = [get_skill_name(s) for s in character.skills]
        # Убираем дубликаты
        unique_skills = list(dict.fromkeys(skill_names))
        lines.append(", ".join(unique_skills))
    
    # Спасброски
    if character.saving_throws:
        save_names = {
            "str": "Сила", "dex": "Ловкость", "con": "Телосложение",
            "int": "Интеллект", "wis": "Мудрость", "cha": "Харизма"
        }
        saves = [save_names.get(s, s) for s in character.saving_throws]
        lines.append(f"<b>🎯 Спасброски:</b> {', '.join(saves)}")
    
    # Способности класса
    if character.features:
        lines.append("")
        lines.append(f"<b>⚡ Способности класса:</b>")
        for feature in character.features[:5]:  # Показываем первые 5
            lines.append(f"• {feature.get('name', 'Способность')}")
        if len(character.features) > 5:
            lines.append(f"  <i>...и ещё {len(character.features) - 5}</i>")
    
    # Заклинания
    if is_spellcaster(character.class_id):
        lines.append("")
        lines.append(f"<b>✨ Заклинания:</b>")
        
        if character.spells.cantrips:
            lines.append(f"Заговоры: {', '.join(character.spells.cantrips[:3])}")
            if len(character.spells.cantrips) > 3:
                lines.append(f"  <i>...и ещё {len(character.spells.cantrips) - 3}</i>")
        
        if character.spells.known_spells:
            lines.append(f"Известные: {', '.join(character.spells.known_spells[:3])}")
            if len(character.spells.known_spells) > 3:
                lines.append(f"  <i>...и ещё {len(character.spells.known_spells) - 3}</i>")
        elif character.spells.spellbook:
            lines.append(f"Книга заклинаний: {', '.join(character.spells.spellbook[:3])}")
            if len(character.spells.spellbook) > 3:
                lines.append(f"  <i>...и ещё {len(character.spells.spellbook) - 3}</i>")
        
        if character.spells.spell_slots:
            slots_str = ", ".join([f"{lvl}ур: {cnt}" for lvl, cnt in sorted(character.spells.spell_slots.items())])
            lines.append(f"Ячейки: {slots_str}")
        
        lines.append(f"Сл спасброска: {character.spells.spell_save_dc} | Атака: +{character.spells.spell_attack_bonus}")
    
    # Снаряжение
    if character.equipment:
        lines.append("")
        lines.append(f"<b>🎒 Снаряжение:</b>")
        # Группируем одинаковые предметы
        from collections import Counter
        eq_counts = Counter(character.equipment)
        for item, count in list(eq_counts.items())[:8]:
            if count > 1:
                lines.append(f"• {item} x{count}")
            else:
                lines.append(f"• {item}")
        if len(eq_counts) > 8:
            lines.append(f"  <i>...и ещё {len(eq_counts) - 8} предметов</i>")
    
    lines.append("")
    lines.append(f"<b>💰 Золото:</b> {character.gold} зм")
    lines.append(f"<b>📅 Опыт:</b> {character.experience} XP")
    
    return "\n".join(lines)


def format_abilities_display(scores: Dict[str, int]) -> str:
    """Форматировать распределение характеристик"""
    ability_names = {
        "strength": "СИЛ", "dexterity": "ЛОВ", "constitution": "ТЕЛ",
        "intelligence": "ИНТ", "wisdom": "МДР", "charisma": "ХАР"
    }
    
    lines = []
    for ability, score in scores.items():
        mod = calculate_modifier(score)
        name = ability_names.get(ability, ability)
        lines.append(f"{name}: {score} ({mod:+d})")
    
    return "\n".join(lines)
