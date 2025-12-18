"""
Character Creation Module - Пошаговое создание персонажей в Telegram боте
"""
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
try:
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
except Exception:
    # Тестовый / fallback режим: простые заглушки, чтобы модуль можно было импортировать без зависимости
    class InlineKeyboardButton:
        def __init__(self, text, callback_data=None):
            self.text = text
            self.callback_data = callback_data

    class InlineKeyboardMarkup:
        def __init__(self, keyboard):
            self.inline_keyboard = keyboard

from .character_creator import (
    Character, CreationSession, CreationStep,
    create_session, get_creation_session, delete_session,
    save_character, roll_abilities, get_standard_array,
    apply_racial_bonuses, apply_class_features, apply_background,
    format_character_full, format_abilities_display
)
from .character_data import (
    get_race_by_name, get_race_names,
    get_class_by_id, get_class_names,
    get_background_by_id, get_background_names,
    load_races, load_classes_structured, load_backgrounds,
    is_spellcaster, get_spells_for_class,
    calculate_modifier, get_item_name, get_skill_name
)


# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

def create_character_session(user_id: int) -> CreationSession:
    """Создать новую сессию создания персонажа"""
    """Создать новую сессию создания персонажа"""
    return create_session(user_id)


def get_character_session(user_id: int) -> Optional[CreationSession]:
    """Получить сессию создания персонажа"""
    return get_creation_session(user_id)


def delete_character_session(user_id: int):
    """Удалить сессию создания персонажа"""
    delete_session(user_id)


# ========== НАЧАЛО СОЗДАНИЯ ==========

def start_character_creation(user_id: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Начать процесс создания персонажа"""
    session = create_character_session(user_id)
    session.step = CreationStep.NAME
    
    text = "🎭 <b>Создание нового персонажа</b>\n\n"
    text += "Начнём с имени твоего героя!\n\n"
    text += "Введи имя персонажа (например: Арагорн, Гэндальф, Леголас)"
    
    # Кнопка отмены
    keyboard = [[InlineKeyboardButton("❌ Отменить создание", callback_data="char_create_cancel")]]
    
    return text, InlineKeyboardMarkup(keyboard)


def handle_name_input(user_id: int, name: str) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Обработать ввод имени"""
    session = get_character_session(user_id)
    if not session:
        return "❌ Сессия создания не найдена. Начни заново с /createcharacter", None
    
    # Валидация имени
    if len(name) < 2 or len(name) > 50:
        return "❌ Имя должно быть от 2 до 50 символов. Попробуй снова:", None
    
    session.character.name = name
    session.step = CreationStep.RACE
    
    # Переход к выбору расы
    return build_race_selection_message()


# ========== ВЫБОР РАСЫ ==========

def build_race_selection_message(page: int = 1) -> Tuple[str, InlineKeyboardMarkup]:
    """Построить сообщение выбора расы"""
    race_names = get_race_names()
    
    page_size = 8
    total = len(race_names)
    total_pages = max(1, (total + page_size - 1) // page_size)
    current_page = min(max(1, page), total_pages)
    
    start = (current_page - 1) * page_size
    end = start + page_size
    slice_races = race_names[start:end]
    
    text = "🎭 <b>Выбери расу персонажа</b>\n\n"
    text += f"Страница {current_page}/{total_pages}\n\n"
    text += "Каждая раса даёт уникальные бонусы к характеристикам и особые способности.\n"
    text += "<i>Нажми на расу, чтобы узнать о ней подробнее.</i>"
    
    keyboard = []
    for idx, race_name in enumerate(slice_races):
        global_idx = start + idx
        keyboard.append([InlineKeyboardButton(race_name, callback_data=f"char_race_view_{global_idx}")])
    
    # Навигация
    nav_row = []
    if current_page > 1:
        nav_row.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"char_race_page_{current_page - 1}"))
    nav_row.append(InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="char_page_info"))
    if current_page < total_pages:
        nav_row.append(InlineKeyboardButton("Вперёд ➡️", callback_data=f"char_race_page_{current_page + 1}"))
    keyboard.append(nav_row)
    
    # Кнопка отмены
    keyboard.append([InlineKeyboardButton("❌ Отменить создание", callback_data="char_create_cancel")])
    
    return text, InlineKeyboardMarkup(keyboard)


def build_race_detail_message(race_idx: int) -> Tuple[str, InlineKeyboardMarkup]:
    """Показать детали расы перед выбором"""
    race_names = get_race_names()
    
    if race_idx >= len(race_names):
        return "❌ Раса не найдена.", None
    
    race_name = race_names[race_idx]
    race_data = get_race_by_name(race_name)

    if not race_data:
        return "❌ Данные расы не найдены.", None

    data = race_data["data"]

    # Форматируем текст через вспомогательную функцию (чтобы можно было тестировать отдельно)
    text = format_race_detail_text(race_name, data)

    # Вычисляем страницу для возврата
    page = (race_idx // 8) + 1

    keyboard = [
        [InlineKeyboardButton(f"✅ Выбрать {race_name}", callback_data=f"char_race_select_{race_idx}")],
        [InlineKeyboardButton("🔙 К списку рас", callback_data=f"char_race_page_{page}")]
    ]

    return text, InlineKeyboardMarkup(keyboard)


def format_race_detail_text(race_name: str, data: dict) -> str:
    """Сформировать текст описания расы без зависимостей от telegram (для тестирования)."""
    text = f"🎭 <b>{race_name}</b>\n\n"

    # Базовая информация
    age = data.get("age") or data.get("Возраст")
    size = data.get("size") or data.get("Размер")
    speed = data.get("speed") or data.get("Скорость")
    languages = data.get("languages") or data.get("Языки") or data.get("language")
    asi = data.get("ability_score_increase") or data.get("Увеличение характеристик")

    if asi:
        text += f"📊 <b>Характеристики:</b> {asi}\n"
    if speed:
        if isinstance(speed, dict):
            speed_str = ", ".join(f"{k}: {v}" for k, v in speed.items())
        else:
            speed_str = str(speed)
        text += f"🏃 <b>Скорость:</b> {speed_str}\n"
    if size:
        text += f"📏 <b>Размер:</b> {size}\n"
    if age:
        text += f"⏳ <b>Возраст:</b> {age}\n"
    if languages:
        if isinstance(languages, list):
            lang = ", ".join(languages)
        else:
            lang = str(languages)
        text += f"🗣️ <b>Языки:</b> {lang}\n"

    text += "\n"

    # Описание: используем traits (имя + описание) если есть
    traits = data.get("traits") or data.get("особенности") or data.get("traits_list")
    if traits and isinstance(traits, list):
        text += "<b>📖 Особенности и черты:</b>\n"
        for t in traits[:5]:
            if isinstance(t, dict):
                tname = t.get("name") or t.get("Название")
                tdesc = t.get("description") or t.get("Описание") or ""
                if tname:
                    tdesc_short = tdesc[:300] + "..." if len(tdesc) > 300 else tdesc
                    text += f"  • <b>{tname}:</b> {tdesc_short}\n"
                else:
                    # если элемент — строка
                    text += f"  • {str(t)[:300]}\n"
            else:
                text += f"  • {str(t)[:300]}\n"
        text += "\n"
    else:
        # Если нет traits, попробуем найти другие описания
        for candidate in ["description", "Описание", "summary"]:
            val = data.get(candidate)
            if isinstance(val, str) and val:
                txt = val if len(val) < 800 else val[:800] + "..."
                text += f"<b>📖 Описание:</b>\n{txt}\n\n"
                break

    # Спец. поля: сопротивления, иммунитеты
    resist = data.get("resistances") or data.get("Сопротивление")
    immun = data.get("immunities") or data.get("Иммунитет")
    if resist:
        text += f"🛡️ <b>Сопротивления:</b> {', '.join(resist)}\n"
    if immun:
        text += f"⚠️ <b>Иммунитеты:</b> {', '.join(immun)}\n"

    return text


def handle_race_selection(user_id: int, race_idx: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Обработать выбор расы по индексу"""
    session = get_character_session(user_id)
    if not session:
        return "❌ Сессия создания не найдена.", None
    
    race_names = get_race_names()
    if race_idx >= len(race_names):
        return "❌ Раса не найдена.", None
    
    race_name = race_names[race_idx]
    race_data = get_race_by_name(race_name)
    if not race_data:
        return "❌ Раса не найдена.", None
    
    session.character.race_key = race_data["key"]
    session.character.race_name = race_name
    session.step = CreationStep.CLASS
    
    # Переход к выбору класса
    return build_class_selection_message()


# ========== ВЫБОР КЛАССА ==========

def build_class_selection_message(page: int = 1) -> Tuple[str, InlineKeyboardMarkup]:
    """Построить сообщение выбора класса"""
    class_list = get_class_names()
    
    page_size = 8
    total = len(class_list)
    total_pages = max(1, (total + page_size - 1) // page_size)
    current_page = min(max(1, page), total_pages)
    
    start = (current_page - 1) * page_size
    end = start + page_size
    slice_classes = class_list[start:end]
    
    text = "⚔️ <b>Выбери класс персонажа</b>\n\n"
    text += f"Страница {current_page}/{total_pages}\n\n"
    text += "Класс определяет способности, владения и стиль игры."
    
    keyboard = []
    for class_id, class_name in slice_classes:
        keyboard.append([InlineKeyboardButton(class_name, callback_data=f"char_class_{class_id}")])
    
    # Навигация
    nav_row = []
    if current_page > 1:
        nav_row.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"char_class_page_{current_page - 1}"))
    nav_row.append(InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="char_page_info"))
    if current_page < total_pages:
        nav_row.append(InlineKeyboardButton("Вперёд ➡️", callback_data=f"char_class_page_{current_page + 1}"))
    keyboard.append(nav_row)
    
    # Кнопка отмены
    keyboard.append([InlineKeyboardButton("❌ Отменить создание", callback_data="char_create_cancel")])
    
    return text, InlineKeyboardMarkup(keyboard)


def handle_class_selection(user_id: int, class_id: str) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Обработать выбор класса"""
    session = get_character_session(user_id)
    if not session:
        return "❌ Сессия создания не найдена.", None
    
    class_data = get_class_by_id(class_id)
    if not class_data:
        return "❌ Класс не найден.", None
    
    session.character.class_id = class_id
    session.character.class_name = class_data.get("name", class_id)
    session.step = CreationStep.BACKGROUND
    
    # Переход к выбору предыстории
    return build_background_selection_message()


# ========== ВЫБОР ПРЕДЫСТОРИИ ==========

def build_background_selection_message(page: int = 1) -> Tuple[str, InlineKeyboardMarkup]:
    """Построить сообщение выбора предыстории"""
    background_list = get_background_names()
    
    page_size = 8
    total = len(background_list)
    total_pages = max(1, (total + page_size - 1) // page_size)
    current_page = min(max(1, page), total_pages)
    
    start = (current_page - 1) * page_size
    end = start + page_size
    slice_backgrounds = background_list[start:end]
    
    text = "📖 <b>Выбери предыстория персонажа</b>\n\n"
    text += f"Страница {current_page}/{total_pages}\n\n"
    text += "Предыстория даёт дополнительные навыки, языки и снаряжение."
    
    keyboard = []
    for bg_id, bg_name in slice_backgrounds:
        keyboard.append([InlineKeyboardButton(bg_name, callback_data=f"char_bg_{bg_id}")])
    
    # Навигация
    nav_row = []
    if current_page > 1:
        nav_row.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"char_bg_page_{current_page - 1}"))
    nav_row.append(InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="char_page_info"))
    if current_page < total_pages:
        nav_row.append(InlineKeyboardButton("Вперёд ➡️", callback_data=f"char_bg_page_{current_page + 1}"))
    keyboard.append(nav_row)
    
    # Кнопка отмены
    keyboard.append([InlineKeyboardButton("❌ Отменить создание", callback_data="char_create_cancel")])
    
    return text, InlineKeyboardMarkup(keyboard)


def handle_background_selection(user_id: int, bg_id: str) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Обработать выбор предыстории"""
    session = get_character_session(user_id)
    if not session:
        return "❌ Сессия создания не найдена.", None
    
    bg_data = get_background_by_id(bg_id)
    if not bg_data:
        return "❌ Предыстория не найдена.", None
    
    session.character.background_id = bg_id
    session.character.background_name = bg_data.get("name", bg_id)
    session.step = CreationStep.ABILITIES_METHOD
    
    # Переход к выбору метода генерации характеристик
    return build_abilities_method_message()


# ========== ВЫБОР МЕТОДА ГЕНЕРАЦИИ ХАРАКТЕРИСТИК ==========

def build_abilities_method_message() -> Tuple[str, InlineKeyboardMarkup]:
    """Построить сообщение выбора метода генерации характеристик"""
    text = "📊 <b>Выбери метод определения характеристик</b>\n\n"
    text += "<b>Стандартный набор:</b> 15, 14, 13, 12, 10, 8\n"
    text += "Быстро и сбалансировано.\n\n"
    text += "<b>Случайная генерация:</b> 4d6 (отбросить низший)\n"
    text += "Может дать как сильные, так и слабые результаты.\n\n"
    text += "<b>Покупка очков:</b> 27 очков для распределения\n"
    text += "Максимальная кастомизация (8-15)."
    
    keyboard = [
        [InlineKeyboardButton("📋 Стандартный набор", callback_data="char_abilities_standard")],
        [InlineKeyboardButton("🎲 Случайная генерация", callback_data="char_abilities_roll")],
        [InlineKeyboardButton("💰 Покупка очков", callback_data="char_abilities_pointbuy")],
        [InlineKeyboardButton("❌ Отменить создание", callback_data="char_create_cancel")]
    ]
    
    return text, InlineKeyboardMarkup(keyboard)


def handle_abilities_method(user_id: int, method: str) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Обработать выбор метода генерации характеристик"""
    session = get_character_session(user_id)
    if not session:
        return "❌ Сессия создания не найдена.", None
    
    if method == "standard":
        session.ability_scores = get_standard_array()
        session.step = CreationStep.ABILITIES_ASSIGN
        return build_abilities_assign_message(user_id)
    
    elif method == "roll":
        session.ability_scores = roll_abilities()
        session.step = CreationStep.ABILITIES_ASSIGN
        
        text = f"🎲 <b>Результаты броска:</b>\n\n"
        text += ", ".join(str(s) for s in session.ability_scores)
        text += "\n\nТеперь распределим эти значения по характеристикам."
        
        # Показываем результат и переходим к распределению
        return build_abilities_assign_message(user_id)
    
    elif method == "pointbuy":
        session.step = CreationStep.ABILITIES_POINT_BUY
        # Инициализируем базовые значения
        session.ability_assignments = {
            "strength": 8, "dexterity": 8, "constitution": 8,
            "intelligence": 8, "wisdom": 8, "charisma": 8
        }
        session.point_buy_points = 27
        return build_pointbuy_message(user_id)
    
    return "❌ Неизвестный метод.", None


# ========== РАСПРЕДЕЛЕНИЕ ХАРАКТЕРИСТИК (СТАНДАРТ/БРОСОК) ==========

def build_abilities_assign_message(user_id: int) -> Tuple[str, InlineKeyboardMarkup]:
    """Построить сообщение распределения характеристик"""
    session = get_character_session(user_id)
    if not session:
        return "❌ Сессия не найдена.", None
    
    available_scores = [s for s in session.ability_scores]
    assigned = session.ability_assignments
    
    # Удаляем уже назначенные
    for ability, score in assigned.items():
        if score in available_scores:
            available_scores.remove(score)
    
    abilities_ru = {
        "strength": "Сила", "dexterity": "Ловкость", "constitution": "Телосложение",
        "intelligence": "Интеллект", "wisdom": "Мудрость", "charisma": "Харизма"
    }
    
    text = "📊 <b>Распредели значения по характеристикам</b>\n\n"
    text += f"<b>Доступные значения:</b> {', '.join(str(s) for s in sorted(available_scores, reverse=True))}\n\n"
    
    text += "<b>Текущее распределение:</b>\n"
    for ability_en, ability_ru in abilities_ru.items():
        value = assigned.get(ability_en, "—")
        mod = calculate_modifier(value) if isinstance(value, int) else 0
        text += f"{ability_ru}: {value} ({mod:+d})\n"
    
    # Кнопки для назначения
    keyboard = []
    for ability_en, ability_ru in abilities_ru.items():
        if ability_en not in assigned:
            keyboard.append([InlineKeyboardButton(
                f"Назначить {ability_ru}", 
                callback_data=f"char_assign_{ability_en}"
            )])
    
    # Если все назначены, кнопка продолжения
    if len(assigned) == 6:
        keyboard.append([InlineKeyboardButton("✅ Подтвердить", callback_data="char_abilities_confirm")])
    
    keyboard.append([InlineKeyboardButton("🔄 Сбросить", callback_data="char_abilities_reset")])
    keyboard.append([InlineKeyboardButton("❌ Отменить", callback_data="char_create_cancel")])
    
    return text, InlineKeyboardMarkup(keyboard)


def handle_ability_assign(user_id: int, ability: str) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Обработать начало назначения характеристики"""
    session = get_character_session(user_id)
    if not session:
        return "❌ Сессия не найдена.", None
    
    available_scores = [s for s in session.ability_scores]
    assigned = session.ability_assignments
    
    # Удаляем уже назначенные
    for _, score in assigned.items():
        if score in available_scores:
            available_scores.remove(score)
    
    if not available_scores:
        return "❌ Нет доступных значений.", None
    
    abilities_ru = {
        "strength": "Сила", "dexterity": "Ловкость", "constitution": "Телосложение",
        "intelligence": "Интеллект", "wisdom": "Мудрость", "charisma": "Харизма"
    }
    
    text = f"Выбери значение для <b>{abilities_ru.get(ability, ability)}</b>:"
    
    keyboard = []
    for score in sorted(available_scores, reverse=True):
        mod = calculate_modifier(score)
        keyboard.append([InlineKeyboardButton(
            f"{score} ({mod:+d})",
            callback_data=f"char_assign_{ability}_{score}"
        )])
    
    keyboard.append([InlineKeyboardButton("◀ Назад", callback_data="char_abilities_assign_back")])
    
    return text, InlineKeyboardMarkup(keyboard)


def handle_ability_assign_value(user_id: int, ability: str, score: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Обработать назначение значения характеристике"""
    session = get_character_session(user_id)
    if not session:
        return "❌ Сессия не найдена.", None
    
    session.ability_assignments[ability] = score
    
    # Возвращаемся к экрану распределения
    return build_abilities_assign_message(user_id)


def handle_abilities_reset(user_id: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Сбросить распределение характеристик"""
    session = get_character_session(user_id)
    if not session:
        return "❌ Сессия не найдена.", None
    
    session.ability_assignments = {}
    return build_abilities_assign_message(user_id)


# ========== ПОКУПКА ОЧКОВ ==========

def build_pointbuy_message(user_id: int) -> Tuple[str, InlineKeyboardMarkup]:
    """Построить сообщение покупки очков"""
    session = get_character_session(user_id)
    if not session:
        return "❌ Сессия не найдена.", None
    
    costs = {8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9}
    abilities = session.ability_assignments
    
    # Подсчёт использованных очков
    used_points = sum(costs.get(v, 0) for v in abilities.values())
    remaining = 27 - used_points
    
    abilities_ru = {
        "strength": "СИЛ", "dexterity": "ЛОВ", "constitution": "ТЕЛ",
        "intelligence": "ИНТ", "wisdom": "МДР", "charisma": "ХАР"
    }
    
    text = "💰 <b>Покупка очков</b>\n\n"
    text += f"<b>Осталось очков:</b> {remaining} / 27\n\n"
    text += "<b>Текущие значения:</b>\n"
    
    for ability_en, ability_ru in abilities_ru.items():
        value = abilities.get(ability_en, 8)
        mod = calculate_modifier(value)
        cost = costs.get(value, 0)
        text += f"{ability_ru}: {value} ({mod:+d}) [стоимость: {cost}]\n"
    
    # Кнопки для изменения
    keyboard = []
    for ability_en, ability_ru in abilities_ru.items():
        row = [
            InlineKeyboardButton("➖", callback_data=f"char_pb_{ability_en}_dec"),
            InlineKeyboardButton(ability_ru, callback_data="char_page_info"),
            InlineKeyboardButton("➕", callback_data=f"char_pb_{ability_en}_inc")
        ]
        keyboard.append(row)
    
    # Кнопки управления
    keyboard.append([InlineKeyboardButton("🔄 Сбросить", callback_data="char_pb_reset")])
    
    if remaining >= 0:
        keyboard.append([InlineKeyboardButton("✅ Подтвердить", callback_data="char_abilities_confirm")])
    
    keyboard.append([InlineKeyboardButton("❌ Отменить", callback_data="char_create_cancel")])
    
    return text, InlineKeyboardMarkup(keyboard)


def handle_pointbuy_change(user_id: int, ability: str, change: str) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Обработать изменение очков"""
    session = get_character_session(user_id)
    if not session:
        return "❌ Сессия не найдена.", None
    
    costs = {8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9}
    current_value = session.ability_assignments.get(ability, 8)
    
    if change == "inc":
        new_value = min(15, current_value + 1)
    else:  # dec
        new_value = max(8, current_value - 1)
    
    # Проверяем, хватит ли очков
    temp_abilities = session.ability_assignments.copy()
    temp_abilities[ability] = new_value
    used_points = sum(costs.get(v, 0) for v in temp_abilities.values())
    
    if used_points <= 27:
        session.ability_assignments[ability] = new_value
    
    return build_pointbuy_message(user_id)


def handle_pointbuy_reset(user_id: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Сбросить покупку очков"""
    session = get_character_session(user_id)
    if not session:
        return "❌ Сессия не найдена.", None
    
    session.ability_assignments = {
        "strength": 8, "dexterity": 8, "constitution": 8,
        "intelligence": 8, "wisdom": 8, "charisma": 8
    }
    
    return build_pointbuy_message(user_id)


# ========== ПОДТВЕРЖДЕНИЕ ХАРАКТЕРИСТИК ==========

def handle_abilities_confirm(user_id: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Подтвердить характеристики и перейти к выбору снаряжения"""
    session = get_character_session(user_id)
    if not session:
        return "❌ Сессия не найдена.", None
    
    # Применяем характеристики к персонажу
    for ability, value in session.ability_assignments.items():
        setattr(session.character, ability, value)
    
    # Применяем расовые бонусы
    races = load_races()
    race_data = races.get(session.character.race_key, {})
    apply_racial_bonuses(session.character, race_data)
    
    # Применяем способности класса
    classes = load_classes_structured()
    class_data = classes.get(session.character.class_id, {})
    apply_class_features(session.character, class_data, level=1)
    
    # Применяем предысторию (без золота от снаряжения - только от предыстории)
    bg_data = get_background_by_id(session.character.background_id)
    if bg_data:
        apply_background(session.character, bg_data)
    
    # Обновляем модификаторы
    session.character.update_modifiers()
    session.character.calculate_hp()
    
    # Определяем доступные навыки для выбора
    class_data = get_class_by_id(session.character.class_id)
    if class_data:
        skill_choices = class_data.get("skill_choices", {})
        session.available_skills = skill_choices.get("from", skill_choices.get("choose_from", []))
        session.skills_to_choose = skill_choices.get("count", skill_choices.get("choose", 2))
    
    # Переходим к выбору снаряжения
    session.step = CreationStep.EQUIPMENT
    return build_equipment_selection_message(user_id)


# ========== ВЫБОР СНАРЯЖЕНИЯ ==========

def get_starting_gold_for_class(class_id: str) -> int:
    """Получить стартовое золото для класса (среднее от броска)"""
    gold_by_class = {
        "fighter": 125,    # 5d4x10
        "wizard": 100,     # 4d4x10
        "cleric": 125,     # 5d4x10
        "rogue": 100,      # 4d4x10
        "barbarian": 50,   # 2d4x10
        "bard": 125,       # 5d4x10
        "druid": 50,       # 2d4x10
        "monk": 25,        # 5d4
        "paladin": 125,    # 5d4x10
        "ranger": 125,     # 5d4x10
        "sorcerer": 75,    # 3d4x10
        "warlock": 100,    # 4d4x10
        "artificer": 125   # 5d4x10
    }
    return gold_by_class.get(class_id, 100)


def format_equipment_option(items: List[str]) -> str:
    """Форматировать вариант снаряжения для отображения"""
    from collections import Counter
    item_names = [get_item_name(item_id) for item_id in items]
    counts = Counter(item_names)
    
    formatted = []
    for item, count in counts.items():
        if count > 1:
            formatted.append(f"{item} x{count}")
        else:
            formatted.append(item)
    
    return ", ".join(formatted)


def build_equipment_selection_message(user_id: int) -> Tuple[str, InlineKeyboardMarkup]:
    """Построить сообщение выбора снаряжения"""
    session = get_character_session(user_id)
    if not session:
        return "❌ Сессия не найдена.", None
    
    from .character_data import load_starting_equipment
    starting_eq = load_starting_equipment()
    class_id = session.character.class_id
    
    # Загружаем данные снаряжения класса
    if class_id not in starting_eq:
        # Если нет данных - пропускаем этап
        return proceed_after_equipment(user_id)
    
    class_equipment = starting_eq[class_id]
    choices = class_equipment.get("choices", [])
    fixed = class_equipment.get("fixed", [])
    
    # Инициализируем выбор если нужно
    if not session.equipment_choices:
        session.equipment_choices = choices
        session.selected_equipment = [None] * len(choices)
        session.current_equipment_choice = 0
    
    # Если игрок выбрал золото
    if session.take_gold_instead:
        gold_amount = get_starting_gold_for_class(class_id)
        text = f"💰 <b>Ты выбрал золото вместо снаряжения</b>\n\n"
        text += f"Ты получишь: <b>{gold_amount} зм</b>\n\n"
        text += "Это альтернатива стартовому набору снаряжения."
        
        keyboard = [
            [InlineKeyboardButton("✅ Подтвердить", callback_data="char_eq_gold_confirm")],
            [InlineKeyboardButton("🔙 Вернуться к снаряжению", callback_data="char_eq_back_to_items")],
            [InlineKeyboardButton("❌ Отменить создание", callback_data="char_create_cancel")]
        ]
        return text, InlineKeyboardMarkup(keyboard)
    
    # Если все выборы сделаны - показываем итог
    if session.current_equipment_choice >= len(choices):
        return build_equipment_review_message(user_id, class_equipment)
    
    # Показываем текущий выбор
    current_choice = choices[session.current_equipment_choice]
    options = current_choice.get("options", [])
    
    text = f"🎒 <b>Выбор снаряжения ({session.current_equipment_choice + 1}/{len(choices)})</b>\n\n"
    text += f"Класс: {session.character.class_name}\n\n"
    
    # Показываем фиксированное снаряжение
    if fixed and session.current_equipment_choice == 0:
        text += "<b>Гарантированное снаряжение:</b>\n"
        fixed_formatted = format_equipment_option(fixed)
        text += f"• {fixed_formatted}\n\n"
    
    text += "<b>Выбери один вариант:</b>\n\n"
    
    keyboard = []
    for i, option in enumerate(options):
        option_text = format_equipment_option(option)
        # Сокращаем если слишком длинный
        if len(option_text) > 40:
            option_text = option_text[:37] + "..."
        keyboard.append([InlineKeyboardButton(
            f"{'✅ ' if session.selected_equipment[session.current_equipment_choice] == i else ''}{option_text}",
            callback_data=f"char_eq_opt_{i}"
        )])
    
    # Показываем опцию "взять золото вместо снаряжения" только на первом выборе
    if session.current_equipment_choice == 0:
        gold_amount = get_starting_gold_for_class(class_id)
        keyboard.append([InlineKeyboardButton(
            f"💰 Взять {gold_amount} зм вместо снаряжения",
            callback_data="char_eq_take_gold"
        )])
    
    keyboard.append([InlineKeyboardButton("❌ Отменить", callback_data="char_create_cancel")])
    
    return text, InlineKeyboardMarkup(keyboard)


def build_equipment_review_message(user_id: int, class_equipment: Dict) -> Tuple[str, InlineKeyboardMarkup]:
    """Показать итог выбора снаряжения"""
    session = get_character_session(user_id)
    if not session:
        return "❌ Сессия не найдена.", None
    
    choices = class_equipment.get("choices", [])
    fixed = class_equipment.get("fixed", [])
    
    text = "🎒 <b>Твоё снаряжение</b>\n\n"
    
    # Фиксированное снаряжение
    if fixed:
        text += "<b>Базовое снаряжение:</b>\n"
        text += f"• {format_equipment_option(fixed)}\n\n"
    
    # Выбранное снаряжение
    text += "<b>Выбранное снаряжение:</b>\n"
    for i, choice_idx in enumerate(session.selected_equipment):
        if choice_idx is not None and i < len(choices):
            options = choices[i].get("options", [])
            if choice_idx < len(options):
                selected_items = options[choice_idx]
                text += f"• {format_equipment_option(selected_items)}\n"
    
    text += "\n✅ Всё выбрано! Подтверди снаряжение."
    
    keyboard = [
        [InlineKeyboardButton("✅ Подтвердить снаряжение", callback_data="char_eq_confirm")],
        [InlineKeyboardButton("🔄 Выбрать заново", callback_data="char_eq_reset")],
        [InlineKeyboardButton("❌ Отменить", callback_data="char_create_cancel")]
    ]
    
    return text, InlineKeyboardMarkup(keyboard)


def handle_equipment_option(user_id: int, option_idx: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Обработать выбор варианта снаряжения"""
    session = get_character_session(user_id)
    if not session:
        return "❌ Сессия не найдена.", None
    
    # Сохраняем выбор
    session.selected_equipment[session.current_equipment_choice] = option_idx
    
    # Переходим к следующему выбору
    session.current_equipment_choice += 1
    
    return build_equipment_selection_message(user_id)


def handle_equipment_take_gold(user_id: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Выбрать золото вместо снаряжения"""
    session = get_character_session(user_id)
    if not session:
        return "❌ Сессия не найдена.", None
    
    session.take_gold_instead = True
    return build_equipment_selection_message(user_id)


def handle_equipment_back_to_items(user_id: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Вернуться к выбору снаряжения"""
    session = get_character_session(user_id)
    if not session:
        return "❌ Сессия не найдена.", None
    
    session.take_gold_instead = False
    session.current_equipment_choice = 0
    session.selected_equipment = [None] * len(session.equipment_choices)
    return build_equipment_selection_message(user_id)


def handle_equipment_reset(user_id: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Сбросить выбор снаряжения"""
    session = get_character_session(user_id)
    if not session:
        return "❌ Сессия не найдена.", None
    
    session.current_equipment_choice = 0
    session.selected_equipment = [None] * len(session.equipment_choices)
    return build_equipment_selection_message(user_id)


def handle_equipment_gold_confirm(user_id: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Подтвердить выбор золота вместо снаряжения"""
    session = get_character_session(user_id)
    if not session:
        return "❌ Сессия не найдена.", None
    
    # Даём золото
    gold_amount = get_starting_gold_for_class(session.character.class_id)
    session.character.gold += gold_amount
    
    # Переходим дальше
    return proceed_after_equipment(user_id)


def handle_equipment_confirm(user_id: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Подтвердить выбранное снаряжение"""
    session = get_character_session(user_id)
    if not session:
        return "❌ Сессия не найдена.", None
    
    from .character_data import load_starting_equipment
    starting_eq = load_starting_equipment()
    class_id = session.character.class_id
    
    if class_id not in starting_eq:
        return proceed_after_equipment(user_id)
    
    class_equipment = starting_eq[class_id]
    choices = class_equipment.get("choices", [])
    fixed = class_equipment.get("fixed", [])
    
    # Добавляем фиксированное снаряжение
    for item_id in fixed:
        item_name = get_item_name(item_id)
        session.character.equipment.append(item_name)
    
    # Добавляем выбранное снаряжение
    for i, choice_idx in enumerate(session.selected_equipment):
        if choice_idx is not None and i < len(choices):
            options = choices[i].get("options", [])
            if choice_idx < len(options):
                for item_id in options[choice_idx]:
                    item_name = get_item_name(item_id)
                    session.character.equipment.append(item_name)
    
    # Переходим дальше
    return proceed_after_equipment(user_id)


def proceed_after_equipment(user_id: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Перейти к следующему этапу после снаряжения"""
    session = get_character_session(user_id)
    if not session:
        return "❌ Сессия не найдена.", None
    
    # Если класс - заклинатель, переходим к выбору заклинаний
    if is_spellcaster(session.character.class_id):
        session.step = CreationStep.SPELLS_CANTRIPS
        return build_cantrips_selection_message(user_id)
    else:
        # Иначе переходим к выбору навыков
        if session.skills_to_choose > 0:
            session.step = CreationStep.SKILLS
            return build_skills_selection_message(user_id)
        else:
            # Если нет навыков для выбора, переходим к просмотру
            session.step = CreationStep.REVIEW
            return build_review_message(user_id)


# ========== ВЫБОР НАВЫКОВ ==========

def build_skills_selection_message(user_id: int) -> Tuple[str, InlineKeyboardMarkup]:
    """Построить сообщение выбора навыков"""
    session = get_character_session(user_id)
    if not session:
        return "❌ Сессия не найдена.", None
    
    from .character_data import load_skills
    skills_data = load_skills()
    
    remaining = session.skills_to_choose - len(session.selected_skills)
    
    text = f"📚 <b>Выбери навыки класса</b>\n\n"
    text += f"Осталось выбрать: {remaining}\n\n"
    
    if session.selected_skills:
        text += "<b>Выбрано:</b>\n"
        for skill_id in session.selected_skills:
            skill_name = skills_data.get(skill_id, {}).get("name", skill_id)
            text += f"• {skill_name}\n"
        text += "\n"
    
    text += "<b>Доступные навыки:</b>"
    
    keyboard = []
    for skill_id in session.available_skills:
        if skill_id not in session.selected_skills:
            skill_name = skills_data.get(skill_id, {}).get("name", skill_id)
            keyboard.append([InlineKeyboardButton(skill_name, callback_data=f"char_skill_{skill_id}")])
    
    # Показываем кнопку подтверждения если выбрано достаточно навыков
    if len(session.selected_skills) == session.skills_to_choose:
        keyboard.append([InlineKeyboardButton("✅ Подтвердить", callback_data="char_skills_confirm")])
    elif len(session.selected_skills) > 0:
        # Показываем сколько ещё нужно выбрать
        keyboard.append([InlineKeyboardButton(f"Выбрано {len(session.selected_skills)}/{session.skills_to_choose}", callback_data="char_page_info")])
    
    keyboard.append([InlineKeyboardButton("❌ Отменить", callback_data="char_create_cancel")])
    
    return text, InlineKeyboardMarkup(keyboard)


def handle_skill_selection(user_id: int, skill: str) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Обработать выбор навыка"""
    session = get_character_session(user_id)
    if not session:
        return "❌ Сессия не найдена.", None
    
    if skill in session.selected_skills:
        session.selected_skills.remove(skill)
    else:
        if len(session.selected_skills) < session.skills_to_choose:
            session.selected_skills.append(skill)
    
    return build_skills_selection_message(user_id)


def handle_skills_confirm(user_id: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Подтвердить выбор навыков"""
    session = get_character_session(user_id)
    if not session:
        return "❌ Сессия не найдена.", None
    
    session.character.skills.extend(session.selected_skills)
    session.step = CreationStep.REVIEW
    
    return build_review_message(user_id)


# ========== ВЫБОР ЗАКЛИНАНИЙ ==========

def build_cantrips_selection_message(user_id: int, page: int = 1) -> Tuple[str, InlineKeyboardMarkup]:
    """Построить сообщение выбора заговоров"""
    session = get_character_session(user_id)
    if not session:
        return "❌ Сессия не найдена.", None
    
    # Инициализируем списки если их нет
    if not hasattr(session, 'selected_cantrips'):
        session.selected_cantrips = []
    
    # Получаем информацию о заклинаниях класса
    session.character.update_spell_info()
    max_cantrips = session.character.spells.max_cantrips
    
    if max_cantrips == 0:
        # Класс не использует заговоры, переходим к заклинаниям
        session.step = CreationStep.SPELLS_KNOWN
        return build_spells_selection_message(user_id)
    
    # Получаем доступные заговоры
    class_spells = get_spells_for_class(session.character.class_id, max_level=1)
    # Пробуем оба варианта ключей для заговоров
    available_cantrips = class_spells.get("cantrips", class_spells.get("0", []))
    
    # Сохраняем список для использования по индексу
    session.available_cantrips = available_cantrips
    
    # Если нет заговоров, переходим к заклинаниям
    if not available_cantrips:
        session.step = CreationStep.SPELLS_KNOWN
        return build_spells_selection_message(user_id)
    
    selected = session.selected_cantrips
    remaining = max_cantrips - len(selected)
    
    # Пагинация
    page_size = 10
    total = len(available_cantrips)
    total_pages = max(1, (total + page_size - 1) // page_size)
    current_page = min(max(1, page), total_pages)
    
    start = (current_page - 1) * page_size
    end = start + page_size
    slice_cantrips = available_cantrips[start:end]
    
    text = f"✨ <b>Выбери заговоры</b>\n\n"
    text += f"Класс: {session.character.class_name}\n"
    text += f"Осталось выбрать: {remaining} из {max_cantrips}\n"
    text += f"Страница {current_page}/{total_pages}\n\n"
    
    if selected:
        text += "<b>Выбрано:</b>\n"
        for s in selected[:5]:
            text += f"• {s}\n"
        if len(selected) > 5:
            text += f"  ...и ещё {len(selected) - 5}\n"
        text += "\n"
    
    keyboard = []
    # Используем глобальный индекс для callback_data
    for idx, cantrip in enumerate(slice_cantrips):
        global_idx = start + idx
        prefix = "✅ " if cantrip in selected else ""
        # Обрезаем название если слишком длинное
        display_name = cantrip if len(cantrip) <= 30 else cantrip[:27] + "..."
        keyboard.append([InlineKeyboardButton(
            f"{prefix}{display_name}",
            callback_data=f"char_cantrip_{global_idx}"
        )])
    
    # Навигация
    nav_row = []
    if current_page > 1:
        nav_row.append(InlineKeyboardButton("⬅️", callback_data=f"char_cantrip_page_{current_page - 1}"))
    nav_row.append(InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="char_page_info"))
    if current_page < total_pages:
        nav_row.append(InlineKeyboardButton("➡️", callback_data=f"char_cantrip_page_{current_page + 1}"))
    keyboard.append(nav_row)
    
    # Показываем кнопку подтверждения если выбрано достаточно заговоров
    if len(selected) == max_cantrips:
        keyboard.append([InlineKeyboardButton("✅ Подтвердить", callback_data="char_cantrips_confirm")])
    elif len(selected) > 0:
        keyboard.append([InlineKeyboardButton(f"Выбрано {len(selected)}/{max_cantrips}", callback_data="char_page_info")])
    
    keyboard.append([InlineKeyboardButton("❌ Отменить", callback_data="char_create_cancel")])
    
    return text, InlineKeyboardMarkup(keyboard)


def handle_cantrip_selection(user_id: int, cantrip_idx: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Обработать выбор заговора по индексу - теперь это просто редирект"""
    return build_cantrip_detail_message(user_id, cantrip_idx)


def build_cantrip_detail_message(user_id: int, cantrip_idx: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Показать детали заговора с возможностью выбора"""
    session = get_character_session(user_id)
    if not session:
        return "❌ Сессия не найдена.", None
    
    # Получаем название заговора по индексу
    if not hasattr(session, 'available_cantrips') or cantrip_idx >= len(session.available_cantrips):
        return build_cantrips_selection_message(user_id)
    
    cantrip_name = session.available_cantrips[cantrip_idx]
    
    # Загружаем данные заговора
    from .character_data import load_spells_by_level
    spells_data = load_spells_by_level("cantrips")
    spell_data = spells_data.get(cantrip_name, {})
    
    # Формируем текст с деталями
    text = f"✨ <b>{cantrip_name}</b>\n\n"
    
    # Уровень и школа
    level_school = spell_data.get("информация", spell_data.get("Уровень и школа", ""))
    if level_school:
        text += f"<i>{level_school}</i>\n\n"
    
    # Основные параметры
    if "Время накладывания" in spell_data:
        text += f"⏱ <b>Время:</b> {spell_data['Время накладывания']}\n"
    if "Дистанция" in spell_data:
        text += f"📏 <b>Дистанция:</b> {spell_data['Дистанция']}\n"
    if "Компоненты" in spell_data:
        text += f"🔮 <b>Компоненты:</b> {spell_data['Компоненты']}\n"
    if "Длительность" in spell_data:
        text += f"⌛ <b>Длительность:</b> {spell_data['Длительность']}\n"
    
    text += "\n"
    
    # Описание
    description = spell_data.get("описание", "Описание недоступно.")
    # Обрезаем если слишком длинное
    if len(description) > 800:
        description = description[:800] + "..."
    text += f"{description}\n\n"
    
    # Статус выбора
    is_selected = cantrip_name in session.selected_cantrips
    max_cantrips = session.character.spells.max_cantrips
    current_count = len(session.selected_cantrips)
    
    if is_selected:
        text += f"✅ <b>Этот заговор выбран</b>\n"
    else:
        text += f"Выбрано: {current_count}/{max_cantrips}\n"
    
    # Кнопки
    keyboard = []
    
    if is_selected:
        keyboard.append([InlineKeyboardButton(
            "❌ Убрать из выбранных",
            callback_data=f"char_cantrip_select_{cantrip_idx}"
        )])
    else:
        if current_count < max_cantrips:
            keyboard.append([InlineKeyboardButton(
                "✅ Выбрать этот заговор",
                callback_data=f"char_cantrip_select_{cantrip_idx}"
            )])
        else:
            keyboard.append([InlineKeyboardButton(
                "⚠️ Лимит заговоров достигнут",
                callback_data="char_page_info"
            )])
    
    keyboard.append([InlineKeyboardButton("🔙 К списку заговоров", callback_data="char_cantrip_back")])
    keyboard.append([InlineKeyboardButton("❌ Отменить создание", callback_data="char_create_cancel")])
    
    return text, InlineKeyboardMarkup(keyboard)


def handle_cantrip_toggle(user_id: int, cantrip_idx: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Переключить выбор заговора и вернуться к деталям"""
    session = get_character_session(user_id)
    if not session:
        return "❌ Сессия не найдена.", None
    
    if not hasattr(session, 'available_cantrips') or cantrip_idx >= len(session.available_cantrips):
        return build_cantrips_selection_message(user_id)
    
    cantrip = session.available_cantrips[cantrip_idx]
    max_cantrips = session.character.spells.max_cantrips
    
    if cantrip in session.selected_cantrips:
        session.selected_cantrips.remove(cantrip)
    else:
        if len(session.selected_cantrips) < max_cantrips:
            session.selected_cantrips.append(cantrip)
    
    # Возвращаемся к деталям этого заговора
    return build_cantrip_detail_message(user_id, cantrip_idx)


def handle_cantrips_confirm(user_id: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Подтвердить выбор заговоров"""
    session = get_character_session(user_id)
    if not session:
        return "❌ Сессия не найдена.", None
    
    session.character.spells.cantrips = session.selected_cantrips.copy()
    
    # Переходим к выбору заклинаний 1 уровня
    if session.character.spells.max_known > 0 or session.character.spells.spellbook:
        session.step = CreationStep.SPELLS_KNOWN
        return build_spells_selection_message(user_id)
    else:
        # Если нет известных заклинаний, переходим к навыкам
        if session.skills_to_choose > 0:
            session.step = CreationStep.SKILLS
            return build_skills_selection_message(user_id)
        else:
            session.step = CreationStep.REVIEW
            return build_review_message(user_id)


def build_spells_selection_message(user_id: int, page: int = 1) -> Tuple[str, InlineKeyboardMarkup]:
    """Построить сообщение выбора заклинаний 1 уровня"""
    session = get_character_session(user_id)
    if not session:
        return "❌ Сессия не найдена.", None
    
    # Инициализируем список если его нет
    if not hasattr(session, 'selected_spells'):
        session.selected_spells = []
    
    max_spells = session.character.spells.max_known
    if max_spells == 0 and not session.character.spells.spellbook:
        # Нет известных заклинаний, переходим дальше
        if session.skills_to_choose > 0:
            session.step = CreationStep.SKILLS
            return build_skills_selection_message(user_id)
        else:
            session.step = CreationStep.REVIEW
            return build_review_message(user_id)
    
    # Получаем доступные заклинания 1 уровня
    class_spells = get_spells_for_class(session.character.class_id, max_level=1)
    available_spells = class_spells.get("1", [])
    
    # Сохраняем список для использования по индексу
    session.available_spells = {"1": available_spells}
    
    selected = session.selected_spells
    
    # Для волшебника - 6 заклинаний в книгу
    if session.character.spells.spellbook:
        max_spells = 6
    
    remaining = max_spells - len(selected)
    
    # Пагинация
    page_size = 10
    total = len(available_spells)
    total_pages = max(1, (total + page_size - 1) // page_size)
    current_page = min(max(1, page), total_pages)
    
    start = (current_page - 1) * page_size
    end = start + page_size
    slice_spells = available_spells[start:end]
    
    text = f"✨ <b>Выбери заклинания 1 уровня</b>\n\n"
    text += f"Класс: {session.character.class_name}\n"
    text += f"Осталось выбрать: {remaining} из {max_spells}\n"
    text += f"Страница {current_page}/{total_pages}\n\n"
    
    if selected:
        text += "<b>Выбрано:</b>\n"
        for s in selected[:5]:
            text += f"• {s}\n"
        if len(selected) > 5:
            text += f"  ...и ещё {len(selected) - 5}\n"
        text += "\n"
    
    keyboard = []
    # Используем глобальный индекс для callback_data
    for idx, spell in enumerate(slice_spells):
        global_idx = start + idx
        prefix = "✅ " if spell in selected else ""
        # Обрезаем название если слишком длинное
        display_name = spell if len(spell) <= 30 else spell[:27] + "..."
        keyboard.append([InlineKeyboardButton(
            f"{prefix}{display_name}",
            callback_data=f"char_spell_{global_idx}"
        )])
    
    # Навигация
    nav_row = []
    if current_page > 1:
        nav_row.append(InlineKeyboardButton("⬅️", callback_data=f"char_spell_page_{current_page - 1}"))
    nav_row.append(InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="char_page_info"))
    if current_page < total_pages:
        nav_row.append(InlineKeyboardButton("➡️", callback_data=f"char_spell_page_{current_page + 1}"))
    keyboard.append(nav_row)
    
    # Показываем кнопку подтверждения если выбрано достаточно заклинаний
    if len(selected) == max_spells:
        keyboard.append([InlineKeyboardButton("✅ Подтвердить", callback_data="char_spells_confirm")])
    elif len(selected) > 0:
        keyboard.append([InlineKeyboardButton(f"Выбрано {len(selected)}/{max_spells}", callback_data="char_page_info")])
    
    keyboard.append([InlineKeyboardButton("❌ Отменить", callback_data="char_create_cancel")])
    
    return text, InlineKeyboardMarkup(keyboard)


def handle_spell_selection(user_id: int, spell_idx: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Обработать выбор заклинания по индексу - теперь это просто редирект"""
    return build_spell_detail_message(user_id, spell_idx)


def build_spell_detail_message(user_id: int, spell_idx: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Показать детали заклинания с возможностью выбора"""
    session = get_character_session(user_id)
    if not session:
        return "❌ Сессия не найдена.", None
    
    # Получаем название заклинания по индексу
    available = session.available_spells.get("1", []) if hasattr(session, 'available_spells') else []
    if spell_idx >= len(available):
        return build_spells_selection_message(user_id)
    
    spell_name = available[spell_idx]
    
    # Загружаем данные заклинания
    from .character_data import load_spells_by_level
    spells_data = load_spells_by_level("1")
    spell_data = spells_data.get(spell_name, {})
    
    # Формируем текст с деталями
    text = f"✨ <b>{spell_name}</b>\n\n"
    
    # Уровень и школа
    level_school = spell_data.get("информация", spell_data.get("Уровень и школа", ""))
    if level_school:
        text += f"<i>{level_school}</i>\n\n"
    
    # Основные параметры
    if "Время накладывания" in spell_data:
        text += f"⏱ <b>Время:</b> {spell_data['Время накладывания']}\n"
    if "Дистанция" in spell_data:
        text += f"📏 <b>Дистанция:</b> {spell_data['Дистанция']}\n"
    if "Компоненты" in spell_data:
        text += f"🔮 <b>Компоненты:</b> {spell_data['Компоненты']}\n"
    if "Длительность" in spell_data:
        text += f"⌛ <b>Длительность:</b> {spell_data['Длительность']}\n"
    
    text += "\n"
    
    # Описание
    description = spell_data.get("описание", "Описание недоступно.")
    # Обрезаем если слишком длинное
    if len(description) > 800:
        description = description[:800] + "..."
    text += f"{description}\n\n"
    
    # Статус выбора
    is_selected = spell_name in session.selected_spells
    max_spells = session.character.spells.max_known
    if session.character.spells.spellbook:
        max_spells = 6
    current_count = len(session.selected_spells)
    
    if is_selected:
        text += f"✅ <b>Это заклинание выбрано</b>\n"
    else:
        text += f"Выбрано: {current_count}/{max_spells}\n"
    
    # Кнопки
    keyboard = []
    
    if is_selected:
        keyboard.append([InlineKeyboardButton(
            "❌ Убрать из выбранных",
            callback_data=f"char_spell_select_{spell_idx}"
        )])
    else:
        if current_count < max_spells:
            keyboard.append([InlineKeyboardButton(
                "✅ Выбрать это заклинание",
                callback_data=f"char_spell_select_{spell_idx}"
            )])
        else:
            keyboard.append([InlineKeyboardButton(
                "⚠️ Лимит заклинаний достигнут",
                callback_data="char_page_info"
            )])
    
    keyboard.append([InlineKeyboardButton("🔙 К списку заклинаний", callback_data="char_spell_back")])
    keyboard.append([InlineKeyboardButton("❌ Отменить создание", callback_data="char_create_cancel")])
    
    return text, InlineKeyboardMarkup(keyboard)


def handle_spell_toggle(user_id: int, spell_idx: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Переключить выбор заклинания и вернуться к деталям"""
    session = get_character_session(user_id)
    if not session:
        return "❌ Сессия не найдена.", None
    
    available = session.available_spells.get("1", []) if hasattr(session, 'available_spells') else []
    if spell_idx >= len(available):
        return build_spells_selection_message(user_id)
    
    spell = available[spell_idx]
    
    max_spells = session.character.spells.max_known
    if session.character.spells.spellbook:
        max_spells = 6
    
    if spell in session.selected_spells:
        session.selected_spells.remove(spell)
    else:
        if len(session.selected_spells) < max_spells:
            session.selected_spells.append(spell)
    
    # Возвращаемся к деталям этого заклинания
    return build_spell_detail_message(user_id, spell_idx)


def handle_spells_confirm(user_id: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Подтвердить выбор заклинаний"""
    session = get_character_session(user_id)
    if not session:
        return "❌ Сессия не найдена.", None
    
    if session.character.spells.spellbook:
        session.character.spells.spellbook = session.selected_spells.copy()
    else:
        session.character.spells.known_spells = session.selected_spells.copy()
    
    # Переходим к навыкам или обзору
    if session.skills_to_choose > 0 and not session.selected_skills:
        session.step = CreationStep.SKILLS
        return build_skills_selection_message(user_id)
    else:
        session.step = CreationStep.REVIEW
        return build_review_message(user_id)


# ========== ПРОСМОТР И ПОДТВЕРЖДЕНИЕ ==========

def build_review_message(user_id: int, tab: str = "stats") -> Tuple[str, InlineKeyboardMarkup]:
    """Построить сообщение просмотра персонажа с вкладками"""
    session = get_character_session(user_id)
    if not session:
        return "❌ Сессия не найдена.", None
    
    # Финализируем персонажа
    session.character.update_modifiers()
    session.character.calculate_hp()
    session.character.update_spell_info()
    
    char = session.character
    
    if tab == "stats":
        text = build_stats_tab(char)
    elif tab == "abilities":
        text = build_abilities_tab(char)
    elif tab == "spells":
        text = build_spells_tab(char)
    else:
        text = build_stats_tab(char)
    
    # Навигация по вкладкам
    keyboard = []
    
    # Вкладки
    tabs_row = []
    tabs_row.append(InlineKeyboardButton(
        "📊 Характеристики" if tab != "stats" else "📊 ▸Характеристики◂",
        callback_data="char_review_stats"
    ))
    tabs_row.append(InlineKeyboardButton(
        "⚡ Способности" if tab != "abilities" else "⚡ ▸Способности◂",
        callback_data="char_review_abilities"
    ))
    
    # Показываем вкладку заклинаний только для заклинателей
    if is_spellcaster(char.class_id):
        tabs_row.append(InlineKeyboardButton(
            "✨ Заклинания" if tab != "spells" else "✨ ▸Заклинания◂",
            callback_data="char_review_spells"
        ))
    
    keyboard.append(tabs_row)
    
    # Если на вкладке способностей - добавляем кнопки для просмотра
    if tab == "abilities" and char.features:
        keyboard.append([InlineKeyboardButton(
            "📖 Подробнее о способностях",
            callback_data="char_review_ability_list"
        )])
    
    # Если на вкладке заклинаний - добавляем кнопку списка
    if tab == "spells" and is_spellcaster(char.class_id):
        keyboard.append([InlineKeyboardButton(
            "📖 Подробнее о заклинаниях",
            callback_data="char_review_spell_list"
        )])
    
    keyboard.append([InlineKeyboardButton("✅ Сохранить персонажа", callback_data="char_save")])
    keyboard.append([InlineKeyboardButton("❌ Отменить создание", callback_data="char_create_cancel")])
    
    return text, InlineKeyboardMarkup(keyboard)


def build_stats_tab(char: Character) -> str:
    """Вкладка характеристик и навыков"""
    lines = []
    lines.append(f"🎉 <b>Персонаж создан!</b>\n")
    lines.append(f"<b>📜 {char.name}</b>")
    lines.append(f"<i>{char.race_name} • {char.class_name} {char.level}</i>")
    
    if char.background_name:
        lines.append(f"📖 Предыстория: {char.background_name}")
    
    lines.append("")
    lines.append(f"<b>⚔️ ХАРАКТЕРИСТИКИ</b>")
    lines.append(f"┌─────────────────────────┐")
    lines.append(f"│ СИЛ: {char.strength:2d} ({char.str_mod:+d})  │  ИНТ: {char.intelligence:2d} ({char.int_mod:+d}) │")
    lines.append(f"│ ЛОВ: {char.dexterity:2d} ({char.dex_mod:+d})  │  МДР: {char.wisdom:2d} ({char.wis_mod:+d}) │")
    lines.append(f"│ ТЕЛ: {char.constitution:2d} ({char.con_mod:+d})  │  ХАР: {char.charisma:2d} ({char.cha_mod:+d}) │")
    lines.append(f"└─────────────────────────┘")
    
    lines.append("")
    lines.append(f"<b>❤️ Хиты:</b> {char.current_hp}/{char.max_hp}")
    lines.append(f"<b>🛡️ КД:</b> {char.armor_class}  |  <b>🏃 Скорость:</b> {char.speed} фт")
    lines.append(f"<b>⭐ Бонус мастерства:</b> +{char.proficiency_bonus}")
    
    # Спасброски
    if char.saving_throws:
        save_names = {"str": "Сила", "dex": "Ловкость", "con": "Телосложение",
                      "int": "Интеллект", "wis": "Мудрость", "cha": "Харизма"}
        saves = [save_names.get(s, s) for s in char.saving_throws]
        lines.append(f"<b>🎯 Спасброски:</b> {', '.join(saves)}")
    
    # Навыки
    if char.skills:
        lines.append("")
        lines.append(f"<b>📚 ВЛАДЕНИЕ НАВЫКАМИ</b>")
        # Убираем дубликаты
        unique_skills = list(dict.fromkeys(char.skills))
        skill_names = [get_skill_name(s) for s in unique_skills]
        for skill in skill_names:
            lines.append(f"  • {skill}")
    
    # Владения
    lines.append("")
    lines.append(f"<b>🔧 ВЛАДЕНИЯ</b>")
    if char.armor_proficiencies:
        armor_names = {"light": "Лёгкие", "medium": "Средние", "heavy": "Тяжёлые", "shields": "Щиты"}
        armors = [armor_names.get(a, a) for a in char.armor_proficiencies]
        lines.append(f"  Доспехи: {', '.join(armors)}")
    if char.weapon_proficiencies:
        weapon_names = {"simple": "Простое", "martial": "Воинское"}
        weapons = [weapon_names.get(w, w) for w in char.weapon_proficiencies]
        lines.append(f"  Оружие: {', '.join(weapons)}")
    if char.languages:
        lines.append(f"  Языки: {', '.join(char.languages)}")
    
    # Снаряжение
    if char.equipment:
        lines.append("")
        lines.append(f"<b>🎒 СНАРЯЖЕНИЕ</b>")
        from collections import Counter
        eq_counts = Counter(char.equipment)
        for item, count in list(eq_counts.items())[:6]:
            if count > 1:
                lines.append(f"  • {item} x{count}")
            else:
                lines.append(f"  • {item}")
        if len(eq_counts) > 6:
            lines.append(f"  <i>...и ещё {len(eq_counts) - 6}</i>")
    
    lines.append(f"\n<b>💰 Золото:</b> {char.gold} зм")
    
    return "\n".join(lines)


def build_abilities_tab(char: Character) -> str:
    """Вкладка способностей класса"""
    lines = []
    lines.append(f"⚡ <b>СПОСОБНОСТИ ПЕРСОНАЖА</b>")
    lines.append(f"<i>{char.name} • {char.class_name} {char.level}</i>\n")
    
    if not char.features:
        lines.append("У персонажа пока нет способностей класса.")
        return "\n".join(lines)
    
    # Группируем по уровням
    features_by_level = {}
    for feature in char.features:
        level = feature.get("level", 1)
        if level not in features_by_level:
            features_by_level[level] = []
        features_by_level[level].append(feature)
    
    for level in sorted(features_by_level.keys()):
        lines.append(f"<b>📍 {level} уровень:</b>")
        for feature in features_by_level[level]:
            name = feature.get("name", "Способность")
            desc = feature.get("description", "")
            # Показываем краткое описание (первые 150 символов)
            if desc:
                short_desc = desc[:150] + "..." if len(desc) > 150 else desc
                lines.append(f"  • <b>{name}</b>")
                lines.append(f"    <i>{short_desc}</i>")
            else:
                lines.append(f"  • {name}")
        lines.append("")
    # Отображаем активные гранты/использования
    if char.granted_abilities:
        lines.append(f"<b>🔔 Активные способности и использования:</b>")
        for gid, g in char.granted_abilities.items():
            name = g.get("name", gid)
            uses_total = g.get("uses_total")
            uses_remaining = g.get("uses_remaining")
            recharge = g.get("recharge")
            action_type = g.get("action_type")
            if uses_total is not None:
                lines.append(f"  • {name}: {uses_remaining}/{uses_total} (перезарядка: {recharge or '—'})")
            else:
                # show meta grants if no limited uses
                meta = g.get("meta")
                meta_str = ", ".join([f"{k}: {v}" for k, v in (meta or {}).items()])
                lines.append(f"  • {name}: {meta_str if meta_str else 'есть'}")
        lines.append("")
    
    # Расовые черты
    if char.racial_traits:
        lines.append(f"<b>🧬 Расовые черты:</b>")
        for trait in char.racial_traits[:5]:
            # Берём только название (до первого :)
            trait_name = trait.split(":")[0] if ":" in trait else trait[:30]
            lines.append(f"  • {trait_name}")
        if len(char.racial_traits) > 5:
            lines.append(f"  <i>...и ещё {len(char.racial_traits) - 5}</i>")
    
    lines.append("\n<i>Нажми 'Подробнее' для полных описаний</i>")
    
    return "\n".join(lines)


def build_spells_tab(char: Character) -> str:
    """Вкладка заклинаний"""
    lines = []
    lines.append(f"✨ <b>ЗАКЛИНАНИЯ ПЕРСОНАЖА</b>")
    lines.append(f"<i>{char.name} • {char.class_name} {char.level}</i>\n")
    
    if not is_spellcaster(char.class_id):
        lines.append("Этот класс не использует заклинания.")
        return "\n".join(lines)
    
    # Характеристика заклинаний
    ability_names = {"int": "Интеллект", "wis": "Мудрость", "cha": "Харизма"}
    spell_ability = ability_names.get(char.spells.spellcasting_ability, char.spells.spellcasting_ability)
    
    lines.append(f"<b>📊 Магические показатели:</b>")
    lines.append(f"  Базовая характеристика: {spell_ability}")
    lines.append(f"  Сложность спасброска: {char.spells.spell_save_dc}")
    lines.append(f"  Бонус атаки: +{char.spells.spell_attack_bonus}")
    
    # Ячейки заклинаний
    if char.spells.spell_slots:
        slots = []
        for lvl in sorted(char.spells.spell_slots.keys()):
            slots.append(f"{lvl}ур: {char.spells.spell_slots[lvl]}")
        lines.append(f"  Ячейки: {', '.join(slots)}")
    
    lines.append("")
    
    # Заговоры
    if char.spells.cantrips:
        lines.append(f"<b>🔮 Заговоры ({len(char.spells.cantrips)}):</b>")
        for cantrip in char.spells.cantrips:
            lines.append(f"  • {cantrip}")
        lines.append("")
    
    # Известные заклинания или книга
    if char.spells.known_spells:
        lines.append(f"<b>📜 Известные заклинания ({len(char.spells.known_spells)}):</b>")
        for spell in char.spells.known_spells:
            lines.append(f"  • {spell}")
    elif char.spells.spellbook:
        lines.append(f"<b>📖 Книга заклинаний ({len(char.spells.spellbook)}):</b>")
        for spell in char.spells.spellbook:
            lines.append(f"  • {spell}")
    
    lines.append("\n<i>Нажми 'Подробнее' чтобы прочитать описания</i>")
    
    return "\n".join(lines)


def build_ability_list_message(user_id: int, page: int = 1) -> Tuple[str, InlineKeyboardMarkup]:
    """Список способностей с возможностью просмотра"""
    session = get_character_session(user_id)
    if not session:
        return "❌ Сессия не найдена.", None
    
    char = session.character
    features = char.features + [{"name": t.split(":")[0] if ":" in t else t[:40], "description": t, "is_racial": True} 
                                 for t in char.racial_traits]
    
    if not features:
        return "У персонажа нет способностей.", None
    
    # Пагинация
    page_size = 8
    total = len(features)
    total_pages = max(1, (total + page_size - 1) // page_size)
    current_page = min(max(1, page), total_pages)
    
    start = (current_page - 1) * page_size
    end = start + page_size
    slice_features = features[start:end]
    
    text = f"⚡ <b>Способности</b> (стр. {current_page}/{total_pages})\n\n"
    text += "Выбери способность для просмотра:\n"
    
    keyboard = []
    for idx, feature in enumerate(slice_features):
        global_idx = start + idx
        name = feature.get("name", "Способность")
        prefix = "🧬 " if feature.get("is_racial") else "⚡ "
        display_name = name if len(name) <= 28 else name[:25] + "..."
        keyboard.append([InlineKeyboardButton(
            f"{prefix}{display_name}",
            callback_data=f"char_review_ability_{global_idx}"
        )])
    
    # Навигация
    nav_row = []
    if current_page > 1:
        nav_row.append(InlineKeyboardButton("⬅️", callback_data=f"char_review_ability_page_{current_page - 1}"))
    nav_row.append(InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="char_page_info"))
    if current_page < total_pages:
        nav_row.append(InlineKeyboardButton("➡️", callback_data=f"char_review_ability_page_{current_page + 1}"))
    if nav_row:
        keyboard.append(nav_row)
    
    keyboard.append([InlineKeyboardButton("🔙 Назад к обзору", callback_data="char_review_abilities")])
    
    return text, InlineKeyboardMarkup(keyboard)


def build_ability_detail_message(user_id: int, ability_idx: int) -> Tuple[str, InlineKeyboardMarkup]:
    """Детали способности"""
    session = get_character_session(user_id)
    if not session:
        return "❌ Сессия не найдена.", None
    
    char = session.character
    features = char.features + [{"name": t.split(":")[0] if ":" in t else t[:40], "description": t, "is_racial": True} 
                                 for t in char.racial_traits]
    
    if ability_idx >= len(features):
        return build_ability_list_message(user_id)
    
    feature = features[ability_idx]
    name = feature.get("name", "Способность")
    description = feature.get("description", "Описание недоступно.")
    level = feature.get("level", "")
    is_racial = feature.get("is_racial", False)
    
    text = f"{'🧬' if is_racial else '⚡'} <b>{name}</b>\n"
    if level:
        text += f"<i>Получено на {level} уровне</i>\n"
    if is_racial:
        text += f"<i>Расовая черта</i>\n"
    text += "\n"
    
    # Увеличенный лимит для полного отображения
    if len(description) > 3800:
        description = description[:3800] + "..."
    text += description
    
    # Если у этой способности есть зарегистрированные использования — показываем их и кнопку использования
    # Находим grant по имени
    grant_entry = None
    for gid, g in char.granted_abilities.items():
        if g.get("name") == name:
            grant_entry = (gid, g)
            break
    if grant_entry:
        gid, g = grant_entry
        uses_total = g.get("uses_total")
        uses_remaining = g.get("uses_remaining")
        recharge = g.get("recharge")
        text += "\n\n"
        if uses_total is not None:
            text += f"<b>🔔 Использований:</b> {uses_remaining}/{uses_total} (перезарядка: {recharge or '—'})\n"
        else:
            text += f"<b>🔔 Особенность:</b> {', '.join([f'{k}: {v}' for k,v in (g.get('meta') or {}).items()])}\n"
    
    keyboard = [
        [InlineKeyboardButton("🔙 К списку способностей", callback_data="char_review_ability_list")],
        [InlineKeyboardButton("🔙 К обзору персонажа", callback_data="char_review_abilities")]
    ]
    
    return text, InlineKeyboardMarkup(keyboard)


def build_spell_list_message(user_id: int, spell_type: str = "cantrips") -> Tuple[str, InlineKeyboardMarkup]:
    """Список заклинаний с возможностью просмотра"""
    session = get_character_session(user_id)
    if not session:
        return "❌ Сессия не найдена.", None
    
    char = session.character
    
    # Собираем все заклинания
    all_spells = {
        "cantrips": char.spells.cantrips,
        "1": char.spells.known_spells or char.spells.spellbook
    }
    
    # Определяем какой список показывать
    spells = all_spells.get(spell_type, [])
    
    if spell_type == "cantrips":
        title = "🔮 Заговоры"
    else:
        title = f"📜 Заклинания {spell_type} уровня"
    
    text = f"<b>{title}</b>\n\n"
    
    if not spells:
        text += "Нет заклинаний этого уровня."
    else:
        text += "Выбери заклинание для просмотра:\n"
    
    keyboard = []
    
    for idx, spell in enumerate(spells):
        display_name = spell if len(spell) <= 30 else spell[:27] + "..."
        keyboard.append([InlineKeyboardButton(
            f"✨ {display_name}",
            callback_data=f"char_review_spell_{spell_type}_{idx}"
        )])
    
    # Переключение между заговорами и заклинаниями
    switch_row = []
    if char.spells.cantrips:
        btn_text = "▸Заговоры◂" if spell_type == "cantrips" else "Заговоры"
        switch_row.append(InlineKeyboardButton(btn_text, callback_data="char_review_spell_list_cantrips"))
    if char.spells.known_spells or char.spells.spellbook:
        btn_text = "▸1 уровень◂" if spell_type == "1" else "1 уровень"
        switch_row.append(InlineKeyboardButton(btn_text, callback_data="char_review_spell_list_1"))
    
    if switch_row:
        keyboard.append(switch_row)
    
    keyboard.append([InlineKeyboardButton("🔙 К обзору персонажа", callback_data="char_review_spells")])
    
    return text, InlineKeyboardMarkup(keyboard)


def build_review_spell_detail_message(user_id: int, spell_type: str, spell_idx: int) -> Tuple[str, InlineKeyboardMarkup]:
    """Детали заклинания в обзоре персонажа"""
    session = get_character_session(user_id)
    if not session:
        return "❌ Сессия не найдена.", None
    
    char = session.character
    
    # Получаем список заклинаний
    if spell_type == "cantrips":
        spells = char.spells.cantrips
        level_key = "cantrips"
    else:
        spells = char.spells.known_spells or char.spells.spellbook
        level_key = "1"
    
    if spell_idx >= len(spells):
        return build_spell_list_message(user_id, spell_type)
    
    spell_name = spells[spell_idx]
    
    # Загружаем данные заклинания
    from .character_data import load_spells_by_level
    spells_data = load_spells_by_level(level_key)
    spell_data = spells_data.get(spell_name, {})
    
    # Формируем текст
    text = f"✨ <b>{spell_name}</b>\n\n"
    
    level_school = spell_data.get("информация", spell_data.get("Уровень и школа", ""))
    if level_school:
        text += f"<i>{level_school}</i>\n\n"
    
    if "Время накладывания" in spell_data:
        text += f"⏱ <b>Время:</b> {spell_data['Время накладывания']}\n"
    if "Дистанция" in spell_data:
        text += f"📏 <b>Дистанция:</b> {spell_data['Дистанция']}\n"
    if "Компоненты" in spell_data:
        text += f"🔮 <b>Компоненты:</b> {spell_data['Компоненты']}\n"
    if "Длительность" in spell_data:
        text += f"⌛ <b>Длительность:</b> {spell_data['Длительность']}\n"
    
    text += "\n"
    
    description = spell_data.get("описание", "Описание недоступно.")
    if len(description) > 1200:
        description = description[:1200] + "..."
    text += description
    
    keyboard = [
        [InlineKeyboardButton("🔙 К списку заклинаний", callback_data=f"char_review_spell_list_{spell_type}")],
        [InlineKeyboardButton("🔙 К обзору персонажа", callback_data="char_review_spells")]
    ]
    
    return text, InlineKeyboardMarkup(keyboard)


def handle_character_save(user_id: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """Сохранить персонажа"""
    session = get_character_session(user_id)
    if not session:
        return "❌ Сессия не найдена.", None
    
    # Сохраняем персонажа
    if save_character(session.character):
        delete_character_session(user_id)
        
        text = f"✅ <b>Персонаж {session.character.name} сохранён!</b>\n\n"
        text += "Используй команду /mycharacters для просмотра своих персонажей."
        
        return text, None
    else:
        return "❌ Ошибка при сохранении персонажа. Попробуй ещё раз.", None


def handle_creation_cancel(user_id: int) -> str:
    """Отменить создание персонажа"""
    delete_character_session(user_id)
    return "❌ Создание персонажа отменено."


# ========== ПРОСМОТР СОХРАНЁННЫХ ПЕРСОНАЖЕЙ ==========

def build_saved_character_view(character: Character, tab: str = "stats") -> Tuple[str, InlineKeyboardMarkup]:
    """Построить сообщение просмотра сохранённого персонажа с вкладками"""
    character.update_modifiers()
    character.calculate_hp()
    character.update_spell_info()
    
    if tab == "stats":
        text = build_stats_tab(character)
    elif tab == "abilities":
        text = build_abilities_tab(character)
    elif tab == "spells":
        text = build_spells_tab(character)
    else:
        text = build_stats_tab(character)
    
    # Убираем "Персонаж создан!" для сохранённых персонажей
    text = text.replace("🎉 <b>Персонаж создан!</b>\n\n", "")
    
    char_id = character.id
    
    # Навигация по вкладкам
    keyboard = []
    
    tabs_row = []
    tabs_row.append(InlineKeyboardButton(
        "📊 Характеристики" if tab != "stats" else "📊 ▸Характеристики◂",
        callback_data=f"char_saved_stats_{char_id}"
    ))
    tabs_row.append(InlineKeyboardButton(
        "⚡ Способности" if tab != "abilities" else "⚡ ▸Способности◂",
        callback_data=f"char_saved_abilities_{char_id}"
    ))
    
    if is_spellcaster(character.class_id):
        tabs_row.append(InlineKeyboardButton(
            "✨ Заклинания" if tab != "spells" else "✨ ▸Заклинания◂",
            callback_data=f"char_saved_spells_{char_id}"
        ))
    
    keyboard.append(tabs_row)
    
    # Кнопки подробностей
    if tab == "abilities" and character.features:
        keyboard.append([InlineKeyboardButton(
            "📖 Подробнее о способностях",
            callback_data=f"char_saved_ability_list_{char_id}"
        )])
    
    if tab == "spells" and is_spellcaster(character.class_id):
        keyboard.append([InlineKeyboardButton(
            "📖 Подробнее о заклинаниях",
            callback_data=f"char_saved_spell_list_{char_id}"
        )])
    
    # Кнопка повышения уровня (если уровень < 20)
    if character.level < 20:
        keyboard.append([InlineKeyboardButton("⬆️ Повысить уровень", callback_data=f"char_levelup_{char_id}")])
    
    keyboard.append([InlineKeyboardButton("🗑️ Удалить", callback_data=f"char_delete_{char_id}")])
    keyboard.append([InlineKeyboardButton("◀ Назад к списку", callback_data="char_list")])
    
    return text, InlineKeyboardMarkup(keyboard)


def build_saved_ability_list(character: Character, page: int = 1) -> Tuple[str, InlineKeyboardMarkup]:
    """Список способностей сохранённого персонажа"""
    char_id = character.id
    
    features = character.features + [{"name": t.split(":")[0] if ":" in t else t[:40], "description": t, "is_racial": True} 
                                      for t in character.racial_traits]
    
    if not features:
        text = "У персонажа нет способностей."
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data=f"char_saved_abilities_{char_id}")]]
        return text, InlineKeyboardMarkup(keyboard)
    
    page_size = 8
    total = len(features)
    total_pages = max(1, (total + page_size - 1) // page_size)
    current_page = min(max(1, page), total_pages)
    
    start = (current_page - 1) * page_size
    end = start + page_size
    slice_features = features[start:end]
    
    text = f"⚡ <b>Способности {character.name}</b> (стр. {current_page}/{total_pages})\n\n"
    text += "Выбери способность для просмотра:\n"
    
    keyboard = []
    for idx, feature in enumerate(slice_features):
        global_idx = start + idx
        name = feature.get("name", "Способность")
        prefix = "🧬 " if feature.get("is_racial") else "⚡ "
        display_name = name if len(name) <= 28 else name[:25] + "..."
        keyboard.append([InlineKeyboardButton(
            f"{prefix}{display_name}",
            callback_data=f"char_saved_ability_{char_id}_{global_idx}"
        )])
    
    nav_row = []
    if current_page > 1:
        nav_row.append(InlineKeyboardButton("⬅️", callback_data=f"char_saved_ability_page_{char_id}_{current_page - 1}"))
    nav_row.append(InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="char_page_info"))
    if current_page < total_pages:
        nav_row.append(InlineKeyboardButton("➡️", callback_data=f"char_saved_ability_page_{char_id}_{current_page + 1}"))
    if nav_row:
        keyboard.append(nav_row)
    
    keyboard.append([InlineKeyboardButton("🔙 Назад к обзору", callback_data=f"char_saved_abilities_{char_id}")])
    
    return text, InlineKeyboardMarkup(keyboard)


def build_saved_ability_detail(character: Character, ability_idx: int) -> Tuple[str, InlineKeyboardMarkup]:
    """Детали способности сохранённого персонажа"""
    char_id = character.id
    
    features = character.features + [{"name": t.split(":")[0] if ":" in t else t[:40], "description": t, "is_racial": True} 
                                      for t in character.racial_traits]
    
    if ability_idx >= len(features):
        return build_saved_ability_list(character)
    
    feature = features[ability_idx]
    name = feature.get("name", "Способность")
    description = feature.get("description", "Описание недоступно.")
    level = feature.get("level", "")
    is_racial = feature.get("is_racial", False)
    
    text = f"{'🧬' if is_racial else '⚡'} <b>{name}</b>\n"
    if level:
        text += f"<i>Получено на {level} уровне</i>\n"
    if is_racial:
        text += f"<i>Расовая черта</i>\n"
    text += "\n"
    
    # Увеличенный лимит для полного отображения
    if len(description) > 3800:
        description = description[:3800] + "..."
    text += description
    
    keyboard = [
        [InlineKeyboardButton("🔙 К списку способностей", callback_data=f"char_saved_ability_list_{char_id}")],
        [InlineKeyboardButton("🔙 К обзору персонажа", callback_data=f"char_saved_abilities_{char_id}")]
    ]
    
    return text, InlineKeyboardMarkup(keyboard)


def build_saved_spell_list(character: Character, spell_type: str = "cantrips") -> Tuple[str, InlineKeyboardMarkup]:
    """Список заклинаний сохранённого персонажа"""
    char_id = character.id
    
    all_spells = {
        "cantrips": character.spells.cantrips,
        "1": character.spells.known_spells or character.spells.spellbook
    }
    
    spells = all_spells.get(spell_type, [])
    
    if spell_type == "cantrips":
        title = "🔮 Заговоры"
    else:
        title = f"📜 Заклинания {spell_type} уровня"
    
    text = f"<b>{title}</b> - {character.name}\n\n"
    
    if not spells:
        text += "Нет заклинаний этого уровня."
    else:
        text += "Выбери заклинание для просмотра:\n"
    
    keyboard = []
    
    for idx, spell in enumerate(spells):
        display_name = spell if len(spell) <= 30 else spell[:27] + "..."
        keyboard.append([InlineKeyboardButton(
            f"✨ {display_name}",
            callback_data=f"char_saved_spell_{char_id}_{spell_type}_{idx}"
        )])
    
    switch_row = []
    if character.spells.cantrips:
        btn_text = "▸Заговоры◂" if spell_type == "cantrips" else "Заговоры"
        switch_row.append(InlineKeyboardButton(btn_text, callback_data=f"char_saved_spell_list_{char_id}_cantrips"))
    if character.spells.known_spells or character.spells.spellbook:
        btn_text = "▸1 уровень◂" if spell_type == "1" else "1 уровень"
        switch_row.append(InlineKeyboardButton(btn_text, callback_data=f"char_saved_spell_list_{char_id}_1"))
    
    if switch_row:
        keyboard.append(switch_row)
    
    keyboard.append([InlineKeyboardButton("🔙 К обзору персонажа", callback_data=f"char_saved_spells_{char_id}")])
    
    return text, InlineKeyboardMarkup(keyboard)


def build_saved_spell_detail(character: Character, spell_type: str, spell_idx: int) -> Tuple[str, InlineKeyboardMarkup]:
    """Детали заклинания сохранённого персонажа"""
    char_id = character.id
    
    if spell_type == "cantrips":
        spells = character.spells.cantrips
        level_key = "cantrips"
    else:
        spells = character.spells.known_spells or character.spells.spellbook
        level_key = "1"
    
    if spell_idx >= len(spells):
        return build_saved_spell_list(character, spell_type)
    
    spell_name = spells[spell_idx]
    
    from .character_data import load_spells_by_level
    spells_data = load_spells_by_level(level_key)
    spell_data = spells_data.get(spell_name, {})
    
    text = f"✨ <b>{spell_name}</b>\n\n"
    
    level_school = spell_data.get("информация", spell_data.get("Уровень и школа", ""))
    if level_school:
        text += f"<i>{level_school}</i>\n\n"
    
    if "Время накладывания" in spell_data:
        text += f"⏱ <b>Время:</b> {spell_data['Время накладывания']}\n"
    if "Дистанция" in spell_data:
        text += f"📏 <b>Дистанция:</b> {spell_data['Дистанция']}\n"
    if "Компоненты" in spell_data:
        text += f"🔮 <b>Компоненты:</b> {spell_data['Компоненты']}\n"
    if "Длительность" in spell_data:
        text += f"⌛ <b>Длительность:</b> {spell_data['Длительность']}\n"
    
    text += "\n"
    
    description = spell_data.get("описание", "Описание недоступно.")
    if len(description) > 1200:
        description = description[:1200] + "..."
    text += description
    
    keyboard = [
        [InlineKeyboardButton("🔙 К списку заклинаний", callback_data=f"char_saved_spell_list_{char_id}_{spell_type}")],
        [InlineKeyboardButton("🔙 К обзору персонажа", callback_data=f"char_saved_spells_{char_id}")]
    ]
    
    return text, InlineKeyboardMarkup(keyboard)

