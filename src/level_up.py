"""
Level Up Module - Система повышения уровня персонажей D&D
"""
import random
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

from .character_creator import (
    Character, CharacterSpells, save_character,
    apply_class_features
)
from .character_creation import InlineKeyboardButton, InlineKeyboardMarkup
from .character_data import (
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
    # Выборы, требуемые архетипом (список словарей с {id,name,type,count,options})
    archetype_feature_choices: List[Dict] = field(default_factory=list)


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
    # Выбранные опции архетипных способностей: feature_id -> list of chosen options
    selected_archetype_choices: Dict[str, List[str]] = field(default_factory=dict)
    
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
                ,
                "usage": feature.get("usage"),
                "grants": feature.get("grants")
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
    
    # Проверяем архетипные способности (если архетип уже выбран)
    if character.archetype_name:
        add_archetype_features_to_gains(gains, character.class_name, character.archetype_name)
    
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


def build_levelup_cantrips_message(session: LevelUpSession, page: int = 1):
    """Построить сообщение выбора заговоров при повышении уровня"""
    character = session.character
    # ensure selected_cantrips exists
    if not isinstance(session.selected_cantrips, list):
        session.selected_cantrips = []

    # Ensure spell info up to date
    character.update_spell_info()
    # При повышении уровня количество выбираемых кантрипов задаётся в gains
    max_cantrips = getattr(session.gains, "new_cantrips", 0)

    if max_cantrips == 0:
        return None, None

    # Получаем доступные заговоры
    class_spells = get_spells_for_class(character.class_id, max_level=1)
    available_cantrips = class_spells.get("cantrips", class_spells.get("0", []))
    session.available_cantrips = available_cantrips

    remaining = max_cantrips - len(session.selected_cantrips)

    # Пагинация
    page_size = 10
    total = len(available_cantrips)
    total_pages = max(1, (total + page_size - 1) // page_size)
    current_page = min(max(1, page), total_pages)
    start = (current_page - 1) * page_size
    end = start + page_size
    slice_cantrips = available_cantrips[start:end]

    text = f"✨ <b>Выбери заговоры</b>\n\n"
    text += f"Класс: {character.class_name}\n"
    text += f"Осталось выбрать: {remaining} из {max_cantrips}\n"
    text += f"Страница {current_page}/{total_pages}\n\n"

    if session.selected_cantrips:
        text += "<b>Выбрано:</b>\n"
        for s in session.selected_cantrips[:5]:
            text += f"• {s}\n"
        if len(session.selected_cantrips) > 5:
            text += f"  ...и ещё {len(session.selected_cantrips) - 5}\n"
        text += "\n"

    keyboard = []
    for idx, cantrip in enumerate(slice_cantrips):
        global_idx = start + idx
        prefix = "✅ " if cantrip in session.selected_cantrips else ""
        display_name = cantrip if len(cantrip) <= 30 else cantrip[:27] + "..."
        keyboard.append([InlineKeyboardButton(f"{prefix}{display_name}", callback_data=f"char_lu_cantrip_{global_idx}")])

    nav_row = []
    if current_page > 1:
        nav_row.append(InlineKeyboardButton("⬅️", callback_data=f"char_lu_cantrip_page_{current_page - 1}"))
    nav_row.append(InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="char_page_info"))
    if current_page < total_pages:
        nav_row.append(InlineKeyboardButton("➡️", callback_data=f"char_lu_cantrip_page_{current_page + 1}"))
    keyboard.append(nav_row)

    if len(session.selected_cantrips) == max_cantrips:
        keyboard.append([InlineKeyboardButton("✅ Подтвердить", callback_data="char_lu_cantrips_confirm")])
    elif len(session.selected_cantrips) > 0:
        keyboard.append([InlineKeyboardButton(f"Выбрано {len(session.selected_cantrips)}/{max_cantrips}", callback_data="char_page_info")])

    keyboard.append([InlineKeyboardButton("❌ Отменить", callback_data=f"char_view_{character.id}")])

    return text, InlineKeyboardMarkup(keyboard)


def handle_levelup_cantrip_toggle(session: LevelUpSession, cantrip_idx: int):
    """Переключить выбор заговора в сессии повышения уровня"""
    if not hasattr(session, 'available_cantrips') or cantrip_idx >= len(session.available_cantrips):
        return None, None
    cantrip = session.available_cantrips[cantrip_idx]
    max_cantrips = session.character.spells.max_cantrips
    if cantrip in session.selected_cantrips:
        session.selected_cantrips.remove(cantrip)
    else:
        if len(session.selected_cantrips) < max_cantrips:
            session.selected_cantrips.append(cantrip)
    return build_levelup_cantrips_message(session, page= (cantrip_idx // 10) + 1)


def build_levelup_spells_message(session: LevelUpSession, page: int = 1):
    """Построить сообщение выбора новых заклинаний (1 уровень) при повышении"""
    character = session.character
    if not isinstance(session.selected_spells, list):
        session.selected_spells = []

    max_spells = session.gains.new_spells_known
    if max_spells == 0 and not character.spells.spellbook:
        return None, None

    class_spells = get_spells_for_class(character.class_id, max_level=1)
    available_spells = class_spells.get("1", [])
    session.available_spells = {"1": available_spells}

    page_size = 10
    total = len(available_spells)
    total_pages = max(1, (total + page_size - 1) // page_size)
    current_page = min(max(1, page), total_pages)
    start = (current_page - 1) * page_size
    end = start + page_size
    slice_spells = available_spells[start:end]

    text = f"📜 <b>Выбери заклинания {character.class_name} (1 ур.)</b>\n\n"
    text += f"Осталось выбрать: {max_spells - len(session.selected_spells)} из {max_spells}\n"
    text += f"Страница {current_page}/{total_pages}\n\n"

    if session.selected_spells:
        text += "<b>Выбрано:</b>\n"
        for s in session.selected_spells[:5]:
            text += f"• {s}\n"
        if len(session.selected_spells) > 5:
            text += f"  ...и ещё {len(session.selected_spells) - 5}\n"
        text += "\n"

    keyboard = []
    for idx, sp in enumerate(slice_spells):
        global_idx = start + idx
        prefix = "✅ " if sp in session.selected_spells else ""
        display_name = sp if len(sp) <= 30 else sp[:27] + "..."
        keyboard.append([InlineKeyboardButton(f"{prefix}{display_name}", callback_data=f"char_lu_spell_{global_idx}")])

    nav_row = []
    if current_page > 1:
        nav_row.append(InlineKeyboardButton("⬅️", callback_data=f"char_lu_spell_page_{current_page - 1}"))
    nav_row.append(InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="char_page_info"))
    if current_page < total_pages:
        nav_row.append(InlineKeyboardButton("➡️", callback_data=f"char_lu_spell_page_{current_page + 1}"))
    keyboard.append(nav_row)

    if len(session.selected_spells) == max_spells:
        keyboard.append([InlineKeyboardButton("✅ Подтвердить", callback_data="char_lu_spells_confirm")])
    elif len(session.selected_spells) > 0:
        keyboard.append([InlineKeyboardButton(f"Выбрано {len(session.selected_spells)}/{max_spells}", callback_data="char_page_info")])

    keyboard.append([InlineKeyboardButton("❌ Отменить", callback_data=f"char_view_{character.id}")])
    return text, InlineKeyboardMarkup(keyboard)


def handle_levelup_spell_toggle(session: LevelUpSession, spell_idx: int):
    if not hasattr(session, 'available_spells') or spell_idx >= len(session.available_spells.get("1", [])):
        return None, None
    spell = session.available_spells.get("1")[spell_idx]
    max_spells = session.gains.new_spells_known
    if spell in session.selected_spells:
        session.selected_spells.remove(spell)
    else:
        if len(session.selected_spells) < max_spells:
            session.selected_spells.append(spell)
    return build_levelup_spells_message(session, page=(spell_idx // 10) + 1)


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


def add_archetype_features_to_gains(gains: LevelUpGains, class_name: str, archetype_name: str):
    """Добавить в gains особенности выбранного архетипа для уровня gains.new_level.

    Эта функция безопасна для повторного вызова (проверяет на дубликаты по имени).
    """
    from .character_data import get_archetypes_for_class

    archetypes = get_archetypes_for_class(class_name)
    archetype_data = archetypes.get(archetype_name, {})
    if not archetype_data:
        return

    level = str(gains.new_level)
    features = archetype_data.get("features", {})
    level_feats = features.get(level, [])

    # Добавить каждую способность, избегая дубликатов
    existing_names = {f.get("name") for f in gains.new_features}
    for feat in level_feats:
        if isinstance(feat, dict):
            fname = feat.get("name") or feat.get("id") or "Архетипная способность"
            fdesc = feat.get("description", "")
            display_name = f"[{archetype_name}] {fname}"
            if display_name not in existing_names:
                gains.new_features.append({"name": display_name, "description": fdesc})
                existing_names.add(display_name)

            grants = feat.get("grants", {}) or {}
            if "spells" in grants:
                spells_list = grants["spells"]
                spells_str = ", ".join(spells_list) if isinstance(spells_list, list) else str(spells_list)
                note_name = f"[{archetype_name}] Заклинания архетипа"
                if note_name not in existing_names:
                    gains.new_features.append({
                        "name": note_name,
                        "description": f"Вы получаете доступ к заклинаниям архетипа: {spells_str}. Эти заклинания считаются подготовленными."
                    })
                    existing_names.add(note_name)
            other_grants = {k: v for k, v in grants.items() if k != "spells"}
            if other_grants:
                note_name = f"[{archetype_name}] Доп. гранты"
                if note_name not in existing_names:
                    gains.new_features.append({"name": note_name, "description": str(other_grants)})
                    existing_names.add(note_name)
        # Если у способности есть выборы для игрока — добавляем описания для UI
        choices = feat.get("choices")
        if choices:
            choice_entry = {
                "feature_id": feat.get("id") or feat.get("name") or "",
                "feature_name": feat.get("name") or feat.get("id") or "",
                "type": choices.get("type"),
                "count": choices.get("count", 1),
                "options": []
            }
            # Опции могут быть указаны прямо в 'from' или ссылаться на grants
            opts = choices.get("from")
            if isinstance(opts, list):
                choice_entry["options"] = opts
            elif isinstance(opts, str):
                # Ссылка на поле grants (например, 'environment_choice')
                ref = opts
                if isinstance(grants.get(ref), list):
                    choice_entry["options"] = grants.get(ref)
                else:
                    # Попробуем взять из grants[ref] если это словарь
                    val = grants.get(ref)
                    if isinstance(val, dict):
                        choice_entry["options"] = list(val.keys())
                    else:
                        choice_entry["options"] = []

            # Добавляем в gains
            gains.archetype_feature_choices.append(choice_entry)
            gains.feature_choice = True



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
        # Если способность имеет использование (usage) — зарегистрировать грант
        usage = feature.get("usage")
        grants = feature.get("grants")
        if usage or (grants and any(isinstance(v, dict) or isinstance(v, (int, str)) for v in grants.values())):
            add_grant_from_feature(character, feature, source="class", level=gains.new_level)
    
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
            
            # Добавляем способности архетипа (структура 'features')
            arch_features = archetype_data.get("features", {})
            level_feats = arch_features.get(str(gains.new_level), [])
            for feat in level_feats:
                if isinstance(feat, dict):
                    fname = feat.get("name") or feat.get("id") or "Архетипная способность"
                    fdesc = feat.get("description", "")
                    character.features.append({
                        "level": gains.new_level,
                        "name": f"[{session.selected_archetype}] {fname}",
                        "description": fdesc
                    })

                    # Если грант содержит заклинания — добавляем их в prepared_spells
                    grants = feat.get("grants", {}) or {}
                    if "spells" in grants:
                        spells = grants["spells"]
                        if isinstance(spells, list):
                            character.spells.prepared_spells.extend(spells)
                        else:
                            character.spells.prepared_spells.append(str(spells))
                        # Также добавим в features заметку о новых заклинаниях
                        spells_list = ", ".join(spells) if isinstance(spells, list) else str(spells)
                        character.features.append({
                            "level": gains.new_level,
                            "name": f"[{session.selected_archetype}] Заклинания архетипа",
                            "description": f"Вы получаете доступ к заклинаниям архетипа: {spells_list}. Эти заклинания считаются подготовленными."
                        })
                    # Другие гранты можно зафиксировать как описание
                    other_grants = {k: v for k, v in grants.items() if k != "spells"}
                    if other_grants:
                        character.features.append({
                            "level": gains.new_level,
                            "name": f"[{session.selected_archetype}] Доп. гранты",
                            "description": str(other_grants)
                        })
                    # Регистрируем использования / гранты
                    add_grant_from_feature(character, feat, source=f"archetype:{session.selected_archetype}", level=gains.new_level)
                    # Если пользователь выбирал опции для этой способности — применяем их
                    fid = feat.get("id") or feat.get("name")
                    user_choices = session.selected_archetype_choices.get(fid, [])
                    for uc in user_choices:
                        character.features.append({
                            "level": gains.new_level,
                            "name": f"[{session.selected_archetype}] Выбор: {fid}",
                            "description": f"Выбран вариант: {uc}"
                        })
                        # Если grants содержит маппинг для этого выбора — применим соответствующий грант
                        # Ищем в grants словарь где ключи совпадают с опцией
                        for gk, gv in grants.items():
                            if isinstance(gv, dict) and uc in gv:
                                character.features.append({
                                    "level": gains.new_level,
                                    "name": f"[{session.selected_archetype}] Грант {gk} для {uc}",
                                    "description": str(gv.get(uc))
                                })
                            # Если grants[gk] — список или простое значение, и не зависит от опции, его уже добавили выше
    
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


def add_grant_from_feature(character: Character, feat: Dict, source: str = "", level: int = 0):
    """Добавить в character.granted_abilities запись о гранте/использовании из feat.

    feat может содержать поля 'usage' (dict) и 'grants' (dict)."""
    fid = feat.get("id") or feat.get("name")
    if not fid:
        return

    # Нормализуем id как строку
    fid = str(fid)
    name = feat.get("name") or fid
    usage = feat.get("usage") or {}
    grants = feat.get("grants") or {}

    entry = character.granted_abilities.get(fid, {})
    # If entry exists, don't overwrite uses_remaining unless it's empty
    if not entry:
        entry = {
            "name": name,
            "source": source,
            "level_acquired": level,
            "description": feat.get("description", ""),
            "uses_total": None,
            "uses_remaining": None,
            "recharge": None,
            "action_type": None,
            "meta": {}
        }

    # usage: type/uses/recharge/action_type
    if usage:
        # Тип может быть 'long_rest', 'short_rest', '24_hours' etc.
        entry["recharge"] = usage.get("recharge") or usage.get("type")
        entry["action_type"] = usage.get("action_type") or usage.get("type")
        if usage.get("uses") is not None:
            entry["uses_total"] = int(usage.get("uses"))
            # установим remaining только если ещё не установлено
            if entry.get("uses_remaining") is None:
                entry["uses_remaining"] = int(usage.get("uses"))

    # grants may contain keys like extra_attacks, immunity, spells, temp_hp_on_rage
    # сохраняем их в meta для справки
    if grants:
        entry.setdefault("meta", {}).update(grants)

    character.granted_abilities[fid] = entry


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
