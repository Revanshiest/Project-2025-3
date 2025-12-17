"""
Level Up Module - Система повышения уровня персонажей D&D
"""
import random
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

from character_creator import (
    Character, CharacterSpells, save_character,
    apply_class_features
)
from character_data import (
    get_class_by_id, get_archetypes_for_class,
    get_spellcasting_info, is_spellcaster, get_spells_for_class,
    calculate_modifier, get_proficiency_bonus, get_xp_for_level, get_level_from_xp,
    SPELLCASTING_TABLES, load_classes_structured
)


class LevelUpStep(Enum):
    """Этапы повышения уровня"""
    START = "start"
    SHOW_GAINS = "show_gains"  # Показать что получено
    HP_ROLL = "hp_roll"  # Бросок хитов (или среднее)
    ABILITY_INCREASE = "ability_increase"  # Повышение характеристик
    ARCHETYPE = "archetype"  # Выбор архетипа (на определённых уровнях)
    NEW_SPELLS = "new_spells"  # Выбор новых заклинаний
    NEW_CANTRIPS = "new_cantrips"  # Выбор новых заговоров
    EXPERTISE = "expertise"  # Выбор экспертизы (для некоторых классов)
    FEATURE_CHOICE = "feature_choice"  # Выбор варианта способности
    COMPLETE = "complete"


@dataclass
class LevelUpGains:
    """Что получает персонаж при повышении уровня"""
    new_level: int = 0
    hp_gain: int = 0
    hp_roll_options: Tuple[int, int] = (0, 0)  # (среднее, кость)
    
    # Новые способности
    new_features: List[Dict] = field(default_factory=list)
    
    # Повышение характеристик (на 4, 8, 12, 16, 19 уровнях)
    ability_score_improvement: bool = False
    
    # Архетип
    archetype_choice: bool = False
    archetype_level: int = 0
    available_archetypes: List[str] = field(default_factory=list)
    
    # Заклинания
    new_cantrips: int = 0
    new_spells_known: int = 0
    new_spell_slots: Dict[int, int] = field(default_factory=dict)
    max_spell_level: int = 0
    
    # Особые выборы
    expertise_choice: bool = False
    expertise_count: int = 0


@dataclass
class LevelUpSession:
    """Сессия повышения уровня"""
    user_id: int
    character_id: str
    character: Character
    step: LevelUpStep = LevelUpStep.START
    gains: LevelUpGains = field(default_factory=LevelUpGains)
    
    # Временные данные
    hp_choice: str = ""  # "roll" или "average"
    selected_abilities: Dict[str, int] = field(default_factory=dict)  # куда распределить +2
    selected_archetype: str = ""
    selected_spells: List[str] = field(default_factory=list)
    selected_cantrips: List[str] = field(default_factory=list)
    selected_expertise: List[str] = field(default_factory=list)
    
    # Пагинация
    current_page: int = 1
    items_per_page: int = 8


# Хранилище активных сессий повышения уровня
_levelup_sessions: Dict[int, LevelUpSession] = {}


def get_levelup_session(user_id: int) -> Optional[LevelUpSession]:
    """Получить сессию повышения уровня"""
    return _levelup_sessions.get(user_id)


def create_levelup_session(user_id: int, character: Character) -> LevelUpSession:
    """Создать сессию повышения уровня"""
    session = LevelUpSession(
        user_id=user_id,
        character_id=character.id,
        character=character
    )
    _levelup_sessions[user_id] = session
    return session


def delete_levelup_session(user_id: int):
    """Удалить сессию повышения уровня"""
    if user_id in _levelup_sessions:
        del _levelup_sessions[user_id]


# ========== РАСЧЁТ ЧТО ПОЛУЧАЕТ ПЕРСОНАЖ ==========

def calculate_level_up_gains(character: Character) -> LevelUpGains:
    """Рассчитать что получает персонаж при повышении уровня"""
    new_level = character.level + 1
    gains = LevelUpGains(new_level=new_level)
    
    class_data = get_class_by_id(character.class_id)
    if not class_data:
        return gains
    
    # Хиты
    hit_dice = class_data.get("hit_dice", "1d8")
    dice_value = int(hit_dice.split("d")[1])
    average_hp = (dice_value // 2) + 1
    gains.hp_roll_options = (average_hp, dice_value)
    
    # Новые способности класса
    features = class_data.get("features", {})
    level_features = features.get(str(new_level), [])
    
    for feature in level_features:
        if isinstance(feature, dict):
            feature_info = {
                "name": feature.get("name", ""),
                "name_en": feature.get("name_en", ""),
                "description": feature.get("description", "")
            }
            
            # Проверяем, это выбор архетипа?
            if feature.get("subclass_feature"):
                gains.archetype_choice = True
                gains.archetype_level = new_level
                # Загружаем доступные архетипы
                archetypes = get_archetypes_for_class(character.class_name)
                gains.available_archetypes = list(archetypes.keys())
            
            # Проверяем, это повышение характеристик?
            if feature.get("id") == "ability_score_improvement":
                gains.ability_score_improvement = True
            
            gains.new_features.append(feature_info)
    
    # Проверяем архетипные способности
    if character.archetype_name:
        archetypes = get_archetypes_for_class(character.class_name)
        archetype_data = archetypes.get(character.archetype_name, {})
        
        # Способности архетипа для этого уровня
        archetype_skills = archetype_data.get("skills", {})
        level_skills = archetype_skills.get(str(new_level), [])
        for skill_desc in level_skills:
            skill_text = skill_desc if isinstance(skill_desc, str) else str(skill_desc)
            # Извлекаем имя способности
            skill_name = skill_text.split('.')[0][:50] if '.' in skill_text else skill_text[:50]
            gains.new_features.append({
                "name": f"[{character.archetype_name}] {skill_name}",
                "description": skill_text
            })
        
        # Заклинания архетипа для этого уровня (добавляем как способности)
        archetype_spells = archetype_data.get("spells", {})
        level_spells = archetype_spells.get(str(new_level), [])
        if level_spells:
            spells_list = ", ".join(level_spells) if isinstance(level_spells, list) else str(level_spells)
            gains.new_features.append({
                "name": f"[{character.archetype_name}] Заклинания архетипа",
                "description": f"Вы получаете доступ к следующим заклинаниям архетипа: {spells_list}. Эти заклинания всегда считаются подготовленными."
            })
    
    # Заклинания
    if is_spellcaster(character.class_id):
        current_spell_info = get_spellcasting_info(character.class_id, character.level)
        new_spell_info = get_spellcasting_info(character.class_id, new_level)
        
        if new_spell_info:
            # Новые заговоры
            old_cantrips = current_spell_info.get("cantrips", 0) if current_spell_info else 0
            new_cantrips = new_spell_info.get("cantrips", 0)
            if new_cantrips > old_cantrips:
                gains.new_cantrips = new_cantrips - old_cantrips
            
            # Новые известные заклинания
            old_known = current_spell_info.get("spells_known", 0) if current_spell_info else 0
            new_known = new_spell_info.get("spells_known", 0)
            if new_known > old_known:
                gains.new_spells_known = new_known - old_known
            
            # Новые ячейки
            old_slots = current_spell_info.get("slots", {}) if current_spell_info else {}
            new_slots = new_spell_info.get("slots", {})
            
            for level, count in new_slots.items():
                old_count = old_slots.get(level, 0)
                if count > old_count:
                    gains.new_spell_slots[level] = count - old_count
            
            gains.max_spell_level = new_spell_info.get("max_spell_level", 0)
    
    # Экспертиза (для плута и барда)
    if character.class_id in ["rogue", "bard"]:
        expertise_levels = {"rogue": [1, 6], "bard": [3, 10]}
        if new_level in expertise_levels.get(character.class_id, []):
            gains.expertise_choice = True
            gains.expertise_count = 2
    
    return gains


def format_level_up_gains(gains: LevelUpGains) -> str:
    """Форматировать информацию о том, что получает персонаж"""
    lines = []
    lines.append(f"<b>🎉 Повышение до {gains.new_level} уровня!</b>\n")
    
    # Хиты
    avg, dice = gains.hp_roll_options
    lines.append(f"<b>❤️ Хиты:</b> +{avg} (среднее) или бросок 1d{dice}")
    
    # Новые способности
    if gains.new_features:
        lines.append("\n<b>✨ Новые способности:</b>")
        for feature in gains.new_features:
            name = feature.get("name", "Способность")
            desc = feature.get("description", "")[:200]
            if desc:
                lines.append(f"• <b>{name}</b>: {desc}...")
            else:
                lines.append(f"• <b>{name}</b>")
    
    # Повышение характеристик
    if gains.ability_score_improvement:
        lines.append("\n<b>📈 Повышение характеристик:</b>")
        lines.append("Вы можете увеличить одну характеристику на 2 или две на 1")
    
    # Архетип
    if gains.archetype_choice:
        lines.append("\n<b>🎭 Выбор архетипа!</b>")
        lines.append("Вам предстоит выбрать свой путь развития")
    
    # Заклинания
    if gains.new_cantrips > 0:
        lines.append(f"\n<b>✨ Новые заговоры:</b> +{gains.new_cantrips}")
    
    if gains.new_spells_known > 0:
        lines.append(f"<b>📖 Новые заклинания:</b> +{gains.new_spells_known}")
    
    if gains.new_spell_slots:
        slots_str = ", ".join([f"{lvl}ур: +{cnt}" for lvl, cnt in sorted(gains.new_spell_slots.items())])
        lines.append(f"<b>🔮 Новые ячейки:</b> {slots_str}")
    
    if gains.max_spell_level > 0:
        lines.append(f"<b>Макс. уровень заклинаний:</b> {gains.max_spell_level}")
    
    # Экспертиза
    if gains.expertise_choice:
        lines.append(f"\n<b>⭐ Экспертиза:</b> Выберите {gains.expertise_count} навыка для удвоения бонуса")
    
    return "\n".join(lines)


# ========== ПРИМЕНЕНИЕ ПОВЫШЕНИЯ УРОВНЯ ==========

def apply_level_up(session: LevelUpSession) -> Character:
    """Применить повышение уровня к персонажу"""
    character = session.character
    gains = session.gains
    
    # Повышаем уровень
    character.level = gains.new_level
    character.proficiency_bonus = get_proficiency_bonus(character.level)
    
    # Добавляем хиты
    if session.hp_choice == "average":
        hp_gain = gains.hp_roll_options[0] + character.con_mod
    else:  # roll
        dice = gains.hp_roll_options[1]
        hp_gain = random.randint(1, dice) + character.con_mod
    
    hp_gain = max(1, hp_gain)  # минимум 1 HP
    character.max_hp += hp_gain
    character.current_hp = character.max_hp
    character.hit_dice_remaining = character.level
    
    # Добавляем новые способности
    for feature in gains.new_features:
        character.features.append({
            "level": gains.new_level,
            "name": feature.get("name", ""),
            "description": feature.get("description", "")
        })
    
    # Применяем повышение характеристик
    if gains.ability_score_improvement and session.selected_abilities:
        for ability, increase in session.selected_abilities.items():
            current = getattr(character, ability, 10)
            new_value = min(20, current + increase)  # максимум 20
            setattr(character, ability, new_value)
        character.update_modifiers()
    
    # Применяем архетип
    if gains.archetype_choice and session.selected_archetype:
        character.archetype_name = session.selected_archetype
        
        # Добавляем начальные способности архетипа
        archetypes = get_archetypes_for_class(character.class_name)
        archetype_data = archetypes.get(session.selected_archetype, {})
        
        if archetype_data:
            # Добавляем описание архетипа
            arch_desc = archetype_data.get("description", "")
            if arch_desc:
                character.features.append({
                    "level": gains.new_level,
                    "name": f"Архетип: {session.selected_archetype}",
                    "description": arch_desc
                })
            
            # Добавляем способности архетипа для текущего уровня
            arch_skills = archetype_data.get("skills", {})
            level_skills = arch_skills.get(str(gains.new_level), [])
            for skill in level_skills:
                skill_text = skill if isinstance(skill, str) else str(skill)
                # Извлекаем имя способности из начала текста (до первой точки или 50 символов)
                skill_name = skill_text.split('.')[0][:50] if '.' in skill_text else skill_text[:50]
                character.features.append({
                    "level": gains.new_level,
                    "name": f"[{session.selected_archetype}] {skill_name}",
                    "description": skill_text
                })
            
            # Добавляем заклинания архетипа как особые способности
            arch_spells = archetype_data.get("spells", {})
            level_spells = arch_spells.get(str(gains.new_level), [])
            if level_spells:
                spells_list = ", ".join(level_spells) if isinstance(level_spells, list) else str(level_spells)
                character.features.append({
                    "level": gains.new_level,
                    "name": f"[{session.selected_archetype}] Заклинания архетипа",
                    "description": f"Вы получаете доступ к следующим заклинаниям архетипа: {spells_list}. Эти заклинания всегда считаются подготовленными и не учитываются при подсчёте количества подготовленных заклинаний."
                })
    
    # Добавляем заговоры
    if session.selected_cantrips:
        character.spells.cantrips.extend(session.selected_cantrips)
    
    # Добавляем заклинания
    if session.selected_spells:
        character.spells.known_spells.extend(session.selected_spells)
    
    # Обновляем информацию о заклинаниях
    character.update_spell_info()
    
    # Добавляем экспертизу
    if session.selected_expertise:
        # Храним экспертизу в отдельном поле (можно добавить в Character)
        pass
    
    return character


def roll_hp_for_level(hit_dice: str, con_mod: int) -> int:
    """Бросить хиты для нового уровня"""
    dice_value = int(hit_dice.split("d")[1])
    roll = random.randint(1, dice_value)
    return max(1, roll + con_mod)


def get_average_hp_for_level(hit_dice: str, con_mod: int) -> int:
    """Получить среднее значение хитов для нового уровня"""
    dice_value = int(hit_dice.split("d")[1])
    average = (dice_value // 2) + 1
    return max(1, average + con_mod)


# ========== ПРОВЕРКА ВОЗМОЖНОСТИ ПОВЫШЕНИЯ ==========

def can_level_up(character: Character) -> bool:
    """Проверить, может ли персонаж повысить уровень"""
    if character.level >= 20:
        return False
    
    required_xp = get_xp_for_level(character.level + 1)
    return character.experience >= required_xp


def xp_to_next_level(character: Character) -> int:
    """Сколько XP нужно до следующего уровня"""
    if character.level >= 20:
        return 0
    
    required_xp = get_xp_for_level(character.level + 1)
    return max(0, required_xp - character.experience)


def add_experience(character: Character, xp: int) -> Tuple[bool, int]:
    """
    Добавить опыт персонажу
    Возвращает (можно_ли_повысить_уровень, сколько_уровней_можно_получить)
    """
    character.experience += xp
    
    levels_gained = 0
    while character.level + levels_gained < 20:
        next_level = character.level + levels_gained + 1
        if character.experience >= get_xp_for_level(next_level):
            levels_gained += 1
        else:
            break
    
    return levels_gained > 0, levels_gained


# ========== ФОРМАТИРОВАНИЕ ==========

def format_archetype_info(archetype_name: str, archetype_data: Dict) -> str:
    """Форматировать информацию об архетипе"""
    lines = []
    lines.append(f"<b>🎭 {archetype_name}</b>\n")
    
    desc = archetype_data.get("description", "")
    if desc:
        lines.append(f"<i>{desc[:400]}...</i>\n")
    
    # Показываем способности 3 уровня (обычно первые)
    skills = archetype_data.get("skills", {})
    first_skills = skills.get("3", skills.get("2", []))
    
    if first_skills:
        lines.append("<b>Начальные способности:</b>")
        for skill in first_skills[:2]:  # Показываем максимум 2
            skill_text = skill[:200] if isinstance(skill, str) else str(skill)[:200]
            lines.append(f"• {skill_text}...")
    
    # Заклинания архетипа
    spells = archetype_data.get("spells", {})
    if spells:
        spell_list = []
        for level, spell_names in spells.items():
            if spell_names:
                spell_list.extend(spell_names[:2])
        if spell_list:
            lines.append(f"\n<b>✨ Заклинания:</b> {', '.join(spell_list[:4])}")
    
    return "\n".join(lines)


def format_ability_increase_options() -> str:
    """Форматировать варианты повышения характеристик"""
    return """<b>📈 Повышение характеристик</b>

Выберите один из вариантов:
• <b>+2 к одной</b> - увеличить одну характеристику на 2
• <b>+1 к двум</b> - увеличить две характеристики на 1

<i>Максимальное значение характеристики: 20</i>

Характеристики:
• СИЛ (Сила) - физическая мощь
• ЛОВ (Ловкость) - проворство, рефлексы  
• ТЕЛ (Телосложение) - выносливость, здоровье
• ИНТ (Интеллект) - память, логика
• МДР (Мудрость) - интуиция, восприятие
• ХАР (Харизма) - обаяние, лидерство"""
