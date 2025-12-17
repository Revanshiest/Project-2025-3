import os
from typing import Final
import json
from pathlib import Path
from typing import Dict, List, Optional
from telegram.ext import MessageHandler, filters, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from .ollama import OllamaClient
from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes

from .texts import (
	START_TEXT, 
	HELP_TEXT, 
	RULES_TEXT, 
	DICE_RULES_TEXT,
	COMBAT_RULES_TEXT_PART1,
	COMBAT_RULES_TEXT_PART2,
	COMBAT_RULES_TEXT_PART3,
	COMBAT_RULES_TEXT_PART4,
	STATS_TEXT_PART1,
	STATS_TEXT_PART2,
	GLOSSARY_TEXT_PART1,
	GLOSSARY_TEXT_PART2,
	RACES_SHORT_DESCRIPTIONS
)

from . import character_creation as cc
from .character_creator import load_user_characters, format_character_summary, delete_character, save_character, get_character_by_id
from . import level_up as lu


ollama_client = OllamaClient()
RACES_DATA = {}
SPELLS_CACHE: Dict[str, Dict] = {}  # Кэш заклинаний по уровням
CLASSES_DATA: Dict[str, Dict] = {}  # Кэш классов
CLASSES_LIST: List[str] = []  # Список названий классов
CLASS_KEY_MAP: Dict[str, str] = {}  # Маппинг коротких ID -> полные ключи классов
CLASS_KEY_REVERSE_MAP: Dict[str, str] = {}  # Обратный маппинг: ключ -> короткий ID

def load_races_data() -> dict:
    """Загрузить данные рас из JSON"""
    global RACES_DATA
    if not RACES_DATA:
        races_path = Path(__file__).parent.parent / "data_pars" / "races_data.json"
        try:
            with open(races_path, 'r', encoding='utf-8') as f:
                RACES_DATA = json.load(f)
        except Exception as e:
            print(f"❌ Ошибка загрузки рас: {e}")
    return RACES_DATA


def load_races_formatted_text() -> tuple[str, list[str]]:
    """
    Загрузить отформатированный текст рас и первые три названия для кнопок.
    Возвращает текст целиком и список первых трёх рас.
    """
    races_file = Path(__file__).parent.parent / "data_pars" / "races_descriptions_formatted.txt"
    try:
        raw_text = races_file.read_text(encoding="utf-8").strip()
    except Exception as e:
        print(f"❌ Ошибка чтения races_descriptions_formatted.txt: {e}")
        return "❌ Не удалось загрузить описания рас.", []

    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    first_three_names: list[str] = []

    for line in lines[:3]:
        # Имя расы — всё до первого дефиса
        name = line.split(" -", 1)[0].lstrip("\ufeff").strip()
        if name:
            first_three_names.append(name)

    return raw_text, first_three_names


def load_races_formatted_lines() -> list[tuple[str, str]]:
    """
    Прочитать отформатированный список рас и вернуть пары (имя, описание-строка).
    Используется для пагинации списка рас.
    """
    races_file = Path(__file__).parent.parent / "data_pars" / "races_descriptions_formatted.txt"
    try:
        raw_text = races_file.read_text(encoding="utf-8").strip()
    except Exception as e:
        print(f"❌ Ошибка чтения races_descriptions_formatted.txt: {e}")
        return []

    lines: list[tuple[str, str]] = []
    for line in raw_text.splitlines():
        if not line.strip():
            continue
        name, _, desc = line.partition(" -")
        name = name.lstrip("\ufeff").strip()
        desc = desc.strip(" -")
        lines.append((name, desc))
    return lines


def resolve_race_key(display_name: str) -> str | None:
    """
    Найти ключ в RACES_DATA, который начинается с указанного названия.
    Ключи в JSON имеют вид «АаракокраAarakocraPOA», поэтому матчим по префиксу.
    """
    if not RACES_DATA:
        load_races_data()

    for key in RACES_DATA.keys():
        if key.startswith(display_name):
            return key
    return None


def build_races_page(page: int, page_size: int = 5) -> tuple[str, InlineKeyboardMarkup]:
    """
    Сформировать текст и инлайн-клавиатуру для страницы списка рас.
    """
    load_races_data()
    races = load_races_formatted_lines()
    total = len(races)
    total_pages = max(1, (total + page_size - 1) // page_size)
    current_page = min(max(1, page), total_pages)

    start = (current_page - 1) * page_size
    end = start + page_size
    slice_races = races[start:end]

    text_parts = [f"🎭 Доступные расы (стр. {current_page}/{total_pages})\n"]
    for name, desc in slice_races:
        text_parts.append(f"• {name} — {desc}")
    text = "\n".join(text_parts)

    keyboard: list[list[InlineKeyboardButton]] = []
    for name, _ in slice_races:
        race_key = resolve_race_key(name)
        if race_key:
            keyboard.append([InlineKeyboardButton(text=name, callback_data=f"race_{race_key}")])
        else:
            keyboard.append([InlineKeyboardButton(text=name, callback_data="race_noop")])

    # Навигация: предыдущая / индикатор / следующая
    prev_page = current_page - 1 if current_page > 1 else current_page
    next_page = current_page + 1 if current_page < total_pages else current_page

    nav_row: list[InlineKeyboardButton] = []
    nav_row.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"race_page_{prev_page}"))
    nav_row.append(InlineKeyboardButton(f"Стр {current_page}/{total_pages}", callback_data="race_page_info"))
    nav_row.append(InlineKeyboardButton("Вперёд ➡️", callback_data=f"race_page_{next_page}"))
    keyboard.append(nav_row)

    return text, InlineKeyboardMarkup(keyboard)


def split_message(text: str, limit: int = 4000) -> list[str]:
    """Разбить длинное сообщение на части, стараясь делить по абзацам."""
    if len(text) <= limit:
        return [text]

    parts: list[str] = []
    current = ""

    for paragraph in text.split("\n"):
        paragraph = paragraph.rstrip()
        # +1 за перевод строки, если не первая строчка
        extra_length = len(paragraph) + (1 if current else 0)

        if len(current) + extra_length <= limit:
            current = f"{current}\n{paragraph}" if current else paragraph
        else:
            if current:
                parts.append(current)
            current = paragraph

    if current:
        parts.append(current)

    return parts


# ========== ФУНКЦИИ ДЛЯ РАБОТЫ С ЗАКЛИНАНИЯМИ ==========

def load_spells_by_level(level: str) -> Dict:
    """
    Загрузить заклинания указанного уровня.
    level: "cantrips" или "1", "2", ..., "9"
    """
    global SPELLS_CACHE
    
    if level in SPELLS_CACHE:
        return SPELLS_CACHE[level]
    
    spells_path = Path(__file__).parent.parent / "data_pars" / "spells_by_level"
    
    if level == "cantrips":
        filename = "spells_cantrips.json"
    else:
        filename = f"spells_level_{level}.json"
    
    file_path = spells_path / filename
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            spells_data = json.load(f)
            SPELLS_CACHE[level] = spells_data
            return spells_data
    except Exception as e:
        print(f"❌ Ошибка загрузки заклинаний уровня {level}: {e}")
        return {}


def get_spell_level_display_name(level: str) -> str:
    """Получить отображаемое название уровня заклинаний"""
    if level == "cantrips":
        return "Кантрипы (Заговоры)"
    return f"{level} уровень"


def build_spells_level_selection() -> tuple[str, InlineKeyboardMarkup]:
    """Сформировать экран выбора уровня заклинаний"""
    text = "✨ <b>Выберите уровень заклинаний:</b>\n\n"
    text += "Заговоры — базовые заклинания, не требующие ячеек\n"
    text += "1-9 уровень — заклинания разной силы"
    
    keyboard: list[list[InlineKeyboardButton]] = []
    
    # Заговоры
    keyboard.append([InlineKeyboardButton("✨ Заговоры", callback_data="spell_level_cantrips")])
    
    # Уровни 1-9 в две колонки
    levels_row: list[InlineKeyboardButton] = []
    for i in range(1, 10):
        levels_row.append(InlineKeyboardButton(f"{i}", callback_data=f"spell_level_{i}"))
        if len(levels_row) == 3:
            keyboard.append(levels_row)
            levels_row = []
    if levels_row:
        keyboard.append(levels_row)
    
    return text, InlineKeyboardMarkup(keyboard)


def build_spells_page(level: str, page: int, page_size: int = 10) -> tuple[str, InlineKeyboardMarkup]:
    """
    Сформировать текст и инлайн-клавиатуру для страницы списка заклинаний уровня.
    """
    spells_data = load_spells_by_level(level)
    spell_names = sorted(list(spells_data.keys()))
    
    total = len(spell_names)
    total_pages = max(1, (total + page_size - 1) // page_size)
    current_page = min(max(1, page), total_pages)
    
    start = (current_page - 1) * page_size
    end = start + page_size
    slice_spells = spell_names[start:end]
    
    level_name = get_spell_level_display_name(level)
    text_parts = [f"✨ <b>{level_name}</b> (стр. {current_page}/{total_pages})\n"]
    text_parts.append(f"Всего заклинаний: {total}\n")
    
    for name in slice_spells:
        text_parts.append(f"• {name}")
    text = "\n".join(text_parts)
    
    keyboard: list[list[InlineKeyboardButton]] = []
    
    # Кнопки заклинаний (по 2 в ряд для компактности)
    # Используем индекс вместо имени для callback_data, чтобы избежать проблем с длиной и символами
    spell_row: list[InlineKeyboardButton] = []
    for idx, name in enumerate(slice_spells):
        # Используем глобальный индекс в отсортированном списке
        global_idx = start + idx
        # Формат: spell_level_index (например: spell_1_5, spell_cantrips_12)
        # Это гарантирует короткий и безопасный callback_data
        callback_data = f"spell_{level}_{global_idx}"
        # Ограничиваем текст кнопки для читаемости
        button_text = name[:25] + "..." if len(name) > 25 else name
        spell_row.append(InlineKeyboardButton(text=button_text, callback_data=callback_data))
        if len(spell_row) == 2:
            keyboard.append(spell_row)
            spell_row = []
    if spell_row:
        keyboard.append(spell_row)
    
    # Навигация: предыдущая / индикатор / следующая
    prev_page = current_page - 1 if current_page > 1 else current_page
    next_page = current_page + 1 if current_page < total_pages else current_page
    
    nav_row: list[InlineKeyboardButton] = []
    nav_row.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"spell_page_{level}_{prev_page}"))
    nav_row.append(InlineKeyboardButton(f"Стр {current_page}/{total_pages}", callback_data="spell_page_info"))
    nav_row.append(InlineKeyboardButton("Вперёд ➡️", callback_data=f"spell_page_{level}_{next_page}"))
    keyboard.append(nav_row)
    
    # Кнопка возврата к выбору уровня
    keyboard.append([InlineKeyboardButton("🔙 К выбору уровня", callback_data="spell_level_select")])
    
    return text, InlineKeyboardMarkup(keyboard)


def format_spell_detail_by_name(level: str, spell_name: str) -> str:
    """Форматировать детальную информацию о заклинании по имени"""
    spells_data = load_spells_by_level(level)
    
    if spell_name not in spells_data:
        return f"❌ Заклинание не найдено"
    
    spell_data = spells_data[spell_name]
    
    level_name = get_spell_level_display_name(level)
    text_parts = [f"✨ <b>{spell_name}</b>\n"]
    text_parts.append(f"<i>{level_name}</i>\n")
    
    # Определяем ключ для уровня и школы
    level_school_key = None
    for key in ["Уровень и школа", "информация"]:
        if key in spell_data:
            level_school_key = key
            break
    
    if level_school_key:
        text_parts.append(f"<b>{level_school_key}:</b> {spell_data[level_school_key]}\n")
    
    # Остальные поля
    for key, value in spell_data.items():
        if key in ["Уровень и школа", "информация", "описание"]:
            continue
        if isinstance(value, str) and value:
            text_parts.append(f"<b>{key}:</b> {value}\n")
        elif isinstance(value, list) and value:
            text_parts.append(f"<b>{key}:</b> {', '.join(str(v) for v in value)}\n")
    
    # Описание в конце
    if "описание" in spell_data:
        text_parts.append(f"\n<b>Описание:</b>\n{spell_data['описание']}")
    
    return "\n".join(text_parts)

# ========== ФУНКЦИИ ДЛЯ РАБОТЫ С КЛАССАМИ ==========

def load_classes_list() -> List[str]:
    """Загрузить список всех классов из JSON файлов"""
    global CLASSES_LIST
    if CLASSES_LIST:
        return CLASSES_LIST
    
    classes_dir = Path(__file__).parent.parent / "data_pars" / "classes"
    if not classes_dir.exists():
        return []
    
    classes = []
    class_names_map = {}  # Для маппинга ключей к названиям
    
    for json_file in classes_dir.glob("*.json"):
        if json_file.name == "classes_list.json" or json_file.name == "Классы.json":
            continue
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Извлекаем название класса из ключа
                for key in data.keys():
                    # Формат: "Воин—КлассыFighter" -> "Воин"
                    # Или из name_ru в данных
                    class_data = data[key]
                    if isinstance(class_data, dict) and 'name_ru' in class_data:
                        class_name = class_data['name_ru']
                        # Убираем "—Классы" если есть
                        if "—" in class_name:
                            class_name = class_name.split("—")[0]
                    else:
                        # Парсим из ключа
                        class_name = key.split("—")[0]
                        # Убираем английские названия
                        english_names = ["Fighter", "Barbarian", "Bard", "Cleric", "Druid", "Monk", 
                                       "Paladin", "Ranger", "Rogue", "Sorcerer", "Warlock", "Wizard", "Inventor"]
                        for en_name in english_names:
                            if en_name in class_name:
                                class_name = class_name.replace(en_name, "")
                    
                    if class_name and class_name.strip():
                        class_name = class_name.strip()
                        if class_name not in classes:
                            classes.append(class_name)
                            class_names_map[key] = class_name
        except Exception as e:
            print(f"❌ Ошибка загрузки {json_file.name}: {e}")
    
    CLASSES_LIST = sorted(classes)
    return CLASSES_LIST


def load_class_data(class_name: str) -> Optional[Dict]:
    """Загрузить данные конкретного класса"""
    global CLASSES_DATA
    
    # Проверяем кэш
    if class_name in CLASSES_DATA:
        return CLASSES_DATA[class_name]
    
    classes_dir = Path(__file__).parent.parent / "data_pars" / "classes"
    
    # Ищем файл с этим классом
    for json_file in classes_dir.glob("*.json"):
        if json_file.name == "classes_list.json" or json_file.name == "Классы.json":
            continue
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Ищем класс в данных
                for key, value in data.items():
                    # Проверяем, содержит ли ключ название класса
                    if class_name in key or (isinstance(value, dict) and value.get('name_ru', '').startswith(class_name)):
                        CLASSES_DATA[class_name] = value
                        return value
        except Exception as e:
            print(f"❌ Ошибка загрузки {json_file.name}: {e}")
    
    return None


def _register_class_key(class_key: str) -> str:
    """Зарегистрировать ключ класса и вернуть короткий ID"""
    global CLASS_KEY_MAP, CLASS_KEY_REVERSE_MAP
    
    if class_key in CLASS_KEY_REVERSE_MAP:
        return CLASS_KEY_REVERSE_MAP[class_key]
    
    # Генерируем короткий ID на основе хеша
    import hashlib
    short_id = hashlib.md5(class_key.encode('utf-8')).hexdigest()[:8]
    
    # Убеждаемся, что ID уникален
    counter = 0
    while short_id in CLASS_KEY_MAP:
        short_id = hashlib.md5(f"{class_key}{counter}".encode('utf-8')).hexdigest()[:8]
        counter += 1
    
    CLASS_KEY_MAP[short_id] = class_key
    CLASS_KEY_REVERSE_MAP[class_key] = short_id
    return short_id


def _get_class_key_from_id(short_id: str) -> Optional[str]:
    """Получить полный ключ класса по короткому ID"""
    global CLASS_KEY_MAP
    return CLASS_KEY_MAP.get(short_id)


def resolve_class_key(display_name: str) -> Optional[str]:
    """Найти ключ класса в данных"""
    classes_dir = Path(__file__).parent.parent / "data_pars" / "classes"
    
    for json_file in classes_dir.glob("*.json"):
        if json_file.name == "classes_list.json" or json_file.name == "Классы.json":
            continue
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for key, value in data.items():
                    # Проверяем по ключу - точное совпадение начала
                    if key.startswith(display_name) or display_name in key:
                        _register_class_key(key)
                        return key
                    # Проверяем по name_ru в данных
                    if isinstance(value, dict):
                        name_ru = value.get('name_ru', '')
                        if name_ru:
                            # Убираем "—Классы" для сравнения
                            clean_name = name_ru.split("—")[0] if "—" in name_ru else name_ru
                            if display_name == clean_name or display_name in name_ru:
                                _register_class_key(key)
                                return key
        except Exception as e:
            print(f"⚠️ Ошибка при поиске класса '{display_name}': {e}")
            continue
    
    return None


def build_classes_page(page: int, page_size: int = 8) -> tuple[str, InlineKeyboardMarkup]:
    """Сформировать текст и инлайн-клавиатуру для страницы списка классов"""
    classes = load_classes_list()
    total = len(classes)
    total_pages = max(1, (total + page_size - 1) // page_size)
    current_page = min(max(1, page), total_pages)
    
    start = (current_page - 1) * page_size
    end = start + page_size
    slice_classes = classes[start:end]
    
    text_parts = [f"⚔️ <b>Доступные классы</b> (стр. {current_page}/{total_pages})\n"]
    text_parts.append(f"Всего классов: {total}\n")
    
    for name in slice_classes:
        text_parts.append(f"• {name}")
    text = "\n".join(text_parts)
    
    keyboard: list[list[InlineKeyboardButton]] = []
    
    # Кнопки классов (по 2 в ряд для компактности)
    class_row: list[InlineKeyboardButton] = []
    for name in slice_classes:
        class_key = resolve_class_key(name)
        if class_key:
            # Используем короткий ID вместо полного ключа
            short_id = _register_class_key(class_key)
            callback_data = f"class_{short_id}"
            button_text = name[:20] + "..." if len(name) > 20 else name
            class_row.append(InlineKeyboardButton(text=button_text, callback_data=callback_data))
            if len(class_row) == 2:
                keyboard.append(class_row)
                class_row = []
    if class_row:
        keyboard.append(class_row)
    
    # Навигация
    prev_page = current_page - 1 if current_page > 1 else current_page
    next_page = current_page + 1 if current_page < total_pages else current_page
    
    nav_row: list[InlineKeyboardButton] = []
    nav_row.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"class_page_{prev_page}"))
    nav_row.append(InlineKeyboardButton(f"Стр {current_page}/{total_pages}", callback_data="class_page_info"))
    nav_row.append(InlineKeyboardButton("Вперёд ➡️", callback_data=f"class_page_{next_page}"))
    keyboard.append(nav_row)
    
    return text, InlineKeyboardMarkup(keyboard)


def format_class_detail(class_key: str, section: str = "main", page: int = 1) -> tuple[str, InlineKeyboardMarkup]:
    """Форматировать детальную информацию о классе с пагинацией"""
    # Пробуем загрузить напрямую из файла по ключу
    class_data = None
    classes_dir = Path(__file__).parent.parent / "data_pars" / "classes"
    
    for json_file in classes_dir.glob("*.json"):
        if json_file.name == "classes_list.json" or json_file.name == "Классы.json":
            continue
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if class_key in data:
                    class_data = data[class_key]
                    break
        except Exception:
            continue
    
    # Если не нашли по ключу, пробуем по названию
    if not class_data:
        class_name = class_key.split("—")[0] if "—" in class_key else class_key
        class_data = load_class_data(class_name)
    
    if not class_data:
        return "❌ Класс не найден", InlineKeyboardMarkup([])
    
    # Извлекаем название
    class_name = class_data.get('name_ru', class_key.split("—")[0] if "—" in class_key else class_key)
    if "—" in class_name:
        class_name = class_name.split("—")[0]
    
    # Используем короткий ID для callback_data
    short_id = _register_class_key(class_key)
    
    text_parts = []
    keyboard: list[list[InlineKeyboardButton]] = []
    
    # Определяем доступные секции
    available_sections = []
    if "Классовые умения" in class_data:
        available_sections.append("abilities")
    if "Архетипы" in class_data:
        available_sections.append("archetypes")
    if "БЫСТРОЕ СОЗДАНИЕ" in class_data:
        available_sections.append("quick_start")
    
    # Собираем все дополнительные секции
    for key in class_data.keys():
        if key not in ["name_ru", "name_en", "Описание класса", "Ключевые характеристики", 
                      "Владение", "Архетипы", "level_progression", "БЫСТРОЕ СОЗДАНИЕ", "Классовые умения"]:
            if key not in available_sections:
                available_sections.append(key)
    
    # Основная страница
    if section == "main":
        text_parts.append(f"⚔️ <b>{class_name}</b>\n")
        
        # Английское название
        if class_data.get('name_en'):
            text_parts.append(f"<i>{class_data['name_en']}</i>\n")
        
        # Описание класса
        if "Описание класса" in class_data:
            desc = class_data["Описание класса"]
            if isinstance(desc, list):
                desc_text = "\n".join([d for d in desc if d and d.strip()])
                if desc_text:
                    text_parts.append(f"<b>📖 Описание:</b>\n{desc_text}\n")
            elif isinstance(desc, str) and desc.strip():
                text_parts.append(f"<b>📖 Описание:</b>\n{desc}\n")
        
        # Ключевые характеристики
        if "Ключевые характеристики" in class_data:
            key_features = class_data["Ключевые характеристики"]
            if isinstance(key_features, dict) and key_features:
                text_parts.append("<b>📊 Ключевые характеристики:</b>")
                for key, value in key_features.items():
                    if value and str(value).strip() and str(value) != "-":
                        text_parts.append(f"• <b>{key}:</b> {value}")
                text_parts.append("")
        
        # Владение
        if "Владение" in class_data:
            prof = class_data["Владение"]
            if isinstance(prof, list):
                prof_items = [p for p in prof if p and str(p).strip() and str(p) != "-"]
                if prof_items:
                    text_parts.append("<b>🛡️ Владение:</b>")
                    for item in prof_items:
                        if ":" in item:
                            parts = item.split(":", 1)
                            if len(parts) == 2:
                                text_parts.append(f"• <b>{parts[0]}:</b> {parts[1]}")
                            else:
                                text_parts.append(f"• {item}")
                        else:
                            text_parts.append(f"• {item}")
                    text_parts.append("")
            elif isinstance(prof, str) and prof.strip():
                text_parts.append(f"<b>🛡️ Владение:</b>\n{prof}\n")
        
        # Кнопки для перехода к секциям
        if "Классовые умения" in class_data:
            keyboard.append([InlineKeyboardButton("📚 Классовые умения", callback_data=f"cls_{short_id}_a_1")])
        if "Архетипы" in class_data:
            keyboard.append([InlineKeyboardButton("🎭 Архетипы", callback_data=f"cls_{short_id}_r_1")])
        if "БЫСТРОЕ СОЗДАНИЕ" in class_data:
            keyboard.append([InlineKeyboardButton("⚡ Быстрое создание", callback_data=f"cls_{short_id}_q_1")])
    
    # Секция "Классовые умения"
    elif section == "abilities":
        text_parts.append(f"⚔️ <b>{class_name}</b> - Классовые умения\n")
        abilities = class_data.get("Классовые умения", [])
        
        if isinstance(abilities, list):
            items = [a for a in abilities if a and str(a).strip() and str(a) != "-"]
            page_size = 10
            total_pages = max(1, (len(items) + page_size - 1) // page_size)
            current_page = min(max(1, page), total_pages)
            
            start = (current_page - 1) * page_size
            end = start + page_size
            page_items = items[start:end]
            
            for item in page_items:
                text_parts.append(f"• {item}")
            
            text_parts.append(f"\n<i>Страница {current_page}/{total_pages}</i>")
            
            # Навигация
            nav_row = []
            if current_page > 1:
                nav_row.append(InlineKeyboardButton("⬅️", callback_data=f"cls_{short_id}_a_{current_page - 1}"))
            nav_row.append(InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="cls_info"))
            if current_page < total_pages:
                nav_row.append(InlineKeyboardButton("➡️", callback_data=f"cls_{short_id}_a_{current_page + 1}"))
            if nav_row:
                keyboard.append(nav_row)
        
        elif isinstance(abilities, str):
            # Разбиваем длинный текст на части
            parts = split_message(abilities, limit=3500)
            total_pages = len(parts)
            current_page = min(max(1, page), total_pages)
            
            text_parts.append(parts[current_page - 1])
            text_parts.append(f"\n<i>Страница {current_page}/{total_pages}</i>")
            
            # Навигация
            nav_row = []
            if current_page > 1:
                nav_row.append(InlineKeyboardButton("⬅️", callback_data=f"cls_{short_id}_a_{current_page - 1}"))
            nav_row.append(InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="cls_info"))
            if current_page < total_pages:
                nav_row.append(InlineKeyboardButton("➡️", callback_data=f"cls_{short_id}_a_{current_page + 1}"))
            if nav_row:
                keyboard.append(nav_row)
    
    # Секция "Быстрое создание"
    elif section == "quick_start":
        text_parts.append(f"⚔️ <b>{class_name}</b> - Быстрое создание\n")
        quick_start = class_data.get("БЫСТРОЕ СОЗДАНИЕ", "")
        if quick_start:
            text_parts.append(quick_start)
    
    # Секция "Архетипы"
    elif section == "archetypes":
        text_parts.append(f"⚔️ <b>{class_name}</b> - Архетипы\n")
        archetypes = class_data.get("Архетипы", {})
        
        if isinstance(archetypes, dict):
            archetype_list = [(name, data) for name, data in archetypes.items() 
                            if name and not name.startswith("Воинские") and name != "ВОИНСКИЙ"]
            
            page_size = 2  # По 2 архетипа на страницу
            total_pages = max(1, (len(archetype_list) + page_size - 1) // page_size)
            current_page = min(max(1, page), total_pages)
            
            start = (current_page - 1) * page_size
            end = start + page_size
            page_archetypes = archetype_list[start:end]
            
            for arch_name, arch_data in page_archetypes:
                text_parts.append(f"<b>🎭 {arch_name}</b>\n")
                if isinstance(arch_data, dict):
                    if "Описание" in arch_data:
                        desc = arch_data["Описание"]
                        if isinstance(desc, list):
                            desc_text = "\n".join([d for d in desc if d and d.strip()][:3])
                            if desc_text:
                                text_parts.append(f"{desc_text}\n")
                        elif isinstance(desc, str):
                            text_parts.append(f"{desc[:500]}...\n" if len(desc) > 500 else f"{desc}\n")
                text_parts.append("")
            
            text_parts.append(f"<i>Страница {current_page}/{total_pages}</i>")
            
            # Навигация
            nav_row = []
            if current_page > 1:
                nav_row.append(InlineKeyboardButton("⬅️", callback_data=f"cls_{short_id}_r_{current_page - 1}"))
            nav_row.append(InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="cls_info"))
            if current_page < total_pages:
                nav_row.append(InlineKeyboardButton("➡️", callback_data=f"cls_{short_id}_r_{current_page + 1}"))
            if nav_row:
                keyboard.append(nav_row)
    
    # Дополнительные секции
    elif section in class_data:
        text_parts.append(f"⚔️ <b>{class_name}</b> - {section}\n")
        value = class_data[section]
        
        if isinstance(value, list):
            items = [v for v in value if v and str(v).strip() and str(v) != "-"]
            page_size = 10
            total_pages = max(1, (len(items) + page_size - 1) // page_size)
            current_page = min(max(1, page), total_pages)
            
            start = (current_page - 1) * page_size
            end = start + page_size
            page_items = items[start:end]
            
            for item in page_items:
                text_parts.append(f"• {item}")
            
            text_parts.append(f"\n<i>Страница {current_page}/{total_pages}</i>")
            
            # Навигация - используем короткое имя секции (первые 3 символа)
            section_short = section[:3].lower() if len(section) >= 3 else section.lower()
            nav_row = []
            if current_page > 1:
                nav_row.append(InlineKeyboardButton("⬅️", callback_data=f"cls_{short_id}_{section_short}_{current_page - 1}"))
            nav_row.append(InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="cls_info"))
            if current_page < total_pages:
                nav_row.append(InlineKeyboardButton("➡️", callback_data=f"cls_{short_id}_{section_short}_{current_page + 1}"))
            if nav_row:
                keyboard.append(nav_row)
        
        elif isinstance(value, str):
            parts = split_message(value, limit=3500)
            total_pages = len(parts)
            current_page = min(max(1, page), total_pages)
            
            text_parts.append(parts[current_page - 1])
            text_parts.append(f"\n<i>Страница {current_page}/{total_pages}</i>")
            
            # Навигация - используем короткое имя секции (первые 3 символа)
            section_short = section[:3].lower() if len(section) >= 3 else section.lower()
            nav_row = []
            if current_page > 1:
                nav_row.append(InlineKeyboardButton("⬅️", callback_data=f"cls_{short_id}_{section_short}_{current_page - 1}"))
            nav_row.append(InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="cls_info"))
            if current_page < total_pages:
                nav_row.append(InlineKeyboardButton("➡️", callback_data=f"cls_{short_id}_{section_short}_{current_page + 1}"))
            if nav_row:
                keyboard.append(nav_row)
    
    # Кнопка возврата
    keyboard.append([InlineKeyboardButton("◀ Назад к классу", callback_data=f"cls_{short_id}_m_1")])
    keyboard.append([InlineKeyboardButton("🔙 К списку классов", callback_data="class_page_1")])
    
    return "\n".join(text_parts), InlineKeyboardMarkup(keyboard)

def load_env() -> None:
	load_dotenv()


def get_bot_token() -> str:
	load_env()
	bot_token: Final[str | None] = os.getenv("TELEGRAM_BOT_TOKEN")
	if not bot_token:
		raise RuntimeError(
			"TELEGRAM_BOT_TOKEN is not set. Create a .env file or set the environment variable."
		)
	return bot_token

user_sessions: Dict[int, Dict[str, str]] = {}

class UserSession:
    """Управляет состоянием сессии пользователя"""
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.current_section = "rules"  # по умолчанию раздел "Основные правила"
        self.section_content = RULES_TEXT
    
    @staticmethod
    def get_or_create(user_id: int) -> "UserSession":
        """Получить или создать сессию пользователя"""
        if user_id not in user_sessions:
            user_sessions[user_id] = {
                "section": "rules",
                "content": RULES_TEXT
            }
        return user_sessions.get(user_id)
    
    def set_section(self, section: str, content: str) -> None:
        """Установить текущий раздел"""
        user_sessions[self.user_id] = {
            "section": section,
            "content": content
        }
    
    def get_current_section(self) -> tuple[str, str]:
        """Получить название и содержимое текущего раздела"""
        session = user_sessions.get(self.user_id, {
            "section": "rules",
            "content": RULES_TEXT
        })
        return session.get("section", "rules"), session.get("content", RULES_TEXT)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	"""Обработчик обычных текстовых сообщений через Ollama"""
	if not update.message or not update.message.text:
		return

	user_id = update.effective_user.id
	
	# Проверяем, находится ли пользователь в процессе создания персонажа
	session = cc.get_character_session(user_id)
	if session and session.step == cc.CreationStep.NAME:
		# Обрабатываем ввод имени персонажа
		text, markup = cc.handle_name_input(user_id, update.message.text)
		if markup:
			await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
		else:
			await update.message.reply_text(text, parse_mode=ParseMode.HTML)
		return
	
	# Получаем текущий раздел пользователя
	user_message = update.message.text

	section_name, section_content = UserSession(user_id).get_current_section()

	# Определяем использовать ли RAG
	use_rag = section_name in ["races", "spells", "classes"]
	rag_section_type = section_name if use_rag else ""

	await update.message.chat.send_action("typing")

	response = ollama_client.generate_response(
		user_message=user_message,
		section_name=section_name,
		section_content=section_content,
		use_rag=use_rag,
		rag_section_type=rag_section_type
	)

	if response:
		try:
			await update.message.reply_text(response, parse_mode=ParseMode.HTML)
		except Exception as e:
			print(f"❌ Ошибка при отправке сообщения: {e}")
			# Пробуем отправить без форматирования или укороченное сообщение
			try:
				short_response = response[:4000] if len(response) > 4000 else response
				await update.message.reply_text(short_response)
			except Exception as e2:
				await update.message.reply_text(
					"❌ Произошла ошибка при отправке ответа. Попробуйте позже."
				)
	else:
		await update.message.reply_text(
			"❌ Не удалось получить ответ. Проверь подключение к Ollama."
		)

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	if update.message:
		await update.message.reply_text(START_TEXT)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	if update.message:
		await update.message.reply_text(HELP_TEXT, parse_mode=ParseMode.HTML)


async def cmd_rules(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	if update.message and update.effective_user:
		user_id = update.effective_user.id
		# Сохраняем текущий раздел пользователя
		session = UserSession(user_id)
		session.set_section("rules", RULES_TEXT)
		await update.message.reply_text(RULES_TEXT, parse_mode=ParseMode.HTML)

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	if update.message:
		await update.message.reply_text(START_TEXT)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	if update.message:
		await update.message.reply_text(HELP_TEXT, parse_mode=ParseMode.HTML)


async def cmd_rules(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	if update.message and update.effective_user:
		user_id = update.effective_user.id
		# Сохраняем текущий раздел пользователя
		session = UserSession(user_id)
		session.set_section("rules", RULES_TEXT)
		await update.message.reply_text(RULES_TEXT, parse_mode=ParseMode.HTML)


async def cmd_dice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	if update.message and update.effective_user:
		user_id = update.effective_user.id
		# Сохраняем текущий раздел пользователя
		session = UserSession(user_id)
		session.set_section("dice", DICE_RULES_TEXT)
		await update.message.reply_text(DICE_RULES_TEXT, parse_mode=ParseMode.HTML)


async def cmd_combat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	if update.message and update.effective_user:
		user_id = update.effective_user.id
		# Сохраняем текущий раздел пользователя
		session = UserSession(user_id)
		session.set_section("combat", COMBAT_RULES_TEXT_PART1 + COMBAT_RULES_TEXT_PART2 + COMBAT_RULES_TEXT_PART3 + COMBAT_RULES_TEXT_PART4)
		# Split large text into multiple messages
		combat_parts = [
			COMBAT_RULES_TEXT_PART1,
			COMBAT_RULES_TEXT_PART2,
			COMBAT_RULES_TEXT_PART3,
			COMBAT_RULES_TEXT_PART4
		]
		
		for part in combat_parts:
			await update.message.reply_text(part, parse_mode=ParseMode.HTML)


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	if update.message and update.effective_user:
		user_id = update.effective_user.id
		# Сохраняем текущий раздел пользователя
		session = UserSession(user_id)
		session.set_section("stats", STATS_TEXT_PART1 + STATS_TEXT_PART2)
		# Split large text into multiple messages
		combat_parts = [
			STATS_TEXT_PART1,
			STATS_TEXT_PART2,
		]
		
		for part in combat_parts:
			await update.message.reply_text(part, parse_mode=ParseMode.HTML)

async def cmd_glossary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	if update.message and update.effective_user:
		user_id = update.effective_user.id
		# Сохраняем текущий раздел пользователя
		session = UserSession(user_id)
		session.set_section("glossary", GLOSSARY_TEXT_PART1 + GLOSSARY_TEXT_PART2)
		# Split large text into multiple messages
		glossary_parts = [
			GLOSSARY_TEXT_PART1,
			GLOSSARY_TEXT_PART2,
		]
		
		for part in glossary_parts:
			await update.message.reply_text(part, parse_mode=ParseMode.HTML)

async def cmd_races(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /races - список рас с кликабельными названиями"""
    if not update.message or not update.effective_user:
        return
    
    user_id = update.effective_user.id
    session = UserSession(user_id)
    session.set_section("races", "")

    text, markup = build_races_page(page=1)
    await update.message.reply_text(text, parse_mode=None, reply_markup=markup)


async def cmd_spells(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /spells - выбор уровня заклинаний"""
    if not update.message or not update.effective_user:
        return
    
    user_id = update.effective_user.id
    session = UserSession(user_id)
    session.set_section("spells", "")
    
    text, markup = build_spells_level_selection()
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)


async def cmd_classes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /classes - список классов"""
    if not update.message or not update.effective_user:
        return
    
    user_id = update.effective_user.id
    session = UserSession(user_id)
    session.set_section("classes", "")
    
    text, markup = build_classes_page(page=1)
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)


# ========== ФУНКЦИИ ДЛЯ ПОВЫШЕНИЯ УРОВНЯ ==========

def build_levelup_confirm_message(session) -> tuple[str, InlineKeyboardMarkup]:
    """Построить сообщение подтверждения повышения уровня"""
    character = session.character
    gains = session.gains
    char_id = character.id
    
    text = f"📈 <b>Подтверждение повышения уровня</b>\n\n"
    text += f"<b>{character.name}</b> ({character.race_name} {character.class_name})\n"
    text += f"Уровень: {character.level} → {gains.new_level}\n\n"
    
    # Хиты
    if session.hp_choice == "average":
        hp_gain = gains.hp_roll_options[0] + character.con_mod
        text += f"❤️ <b>Хиты:</b> +{hp_gain} (среднее)\n"
    else:
        dice = gains.hp_roll_options[1]
        text += f"❤️ <b>Хиты:</b> бросок 1d{dice}+{character.con_mod}\n"
    
    # Архетип
    if session.selected_archetype:
        text += f"🎭 <b>Архетип:</b> {session.selected_archetype}\n"
    
    # Новые способности
    if gains.new_features:
        text += "\n<b>Новые способности:</b>\n"
        for feature in gains.new_features[:5]:  # показываем максимум 5
            name = feature.get("name", "Способность")
            text += f"• {name}\n"
        if len(gains.new_features) > 5:
            text += f"... и ещё {len(gains.new_features) - 5}\n"
    
    text += "\n<b>Подтвердить повышение уровня?</b>"
    
    keyboard = [
        [InlineKeyboardButton("✅ Подтвердить", callback_data=f"char_levelup_confirm_{char_id}")],
        [InlineKeyboardButton("❌ Отмена", callback_data=f"char_view_{char_id}")]
    ]
    
    return text, InlineKeyboardMarkup(keyboard)


def build_archetype_list_message(session) -> tuple[str, InlineKeyboardMarkup]:
    """Построить список архетипов для выбора"""
    from .character_data import get_archetypes_for_class
    
    character = session.character
    char_id = character.id
    archetypes = get_archetypes_for_class(character.class_name)
    
    text = f"🎭 <b>Выберите архетип для {character.class_name}</b>\n\n"
    text += f"На {session.gains.new_level} уровне вы выбираете путь развития вашего персонажа.\n"
    text += "Нажмите на архетип, чтобы узнать подробности:\n\n"
    
    keyboard = []
    for idx, (arch_name, arch_data) in enumerate(archetypes.items()):
        desc = arch_data.get("description", "")
        # Показываем первые 80 символов описания
        short_desc = desc[:80] + "..." if len(desc) > 80 else desc
        text += f"<b>• {arch_name}</b>\n<i>{short_desc}</i>\n\n"
        
        # Кнопка для просмотра деталей
        keyboard.append([InlineKeyboardButton(
            f"📖 {arch_name}",
            callback_data=f"char_lu_arv_{char_id}_{idx}"
        )])
    
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data=f"char_view_{char_id}")])
    
    return text, InlineKeyboardMarkup(keyboard)


def build_archetype_detail_message(session, arch_idx: int) -> tuple[str, InlineKeyboardMarkup]:
    """Построить детальное описание архетипа"""
    from .character_data import get_archetypes_for_class
    
    character = session.character
    char_id = character.id
    new_level = session.gains.new_level
    archetypes = get_archetypes_for_class(character.class_name)
    arch_names = list(archetypes.keys())
    
    if arch_idx >= len(arch_names):
        return build_archetype_list_message(session)
    
    arch_name = arch_names[arch_idx]
    arch_data = archetypes[arch_name]
    
    text = f"🎭 <b>{arch_name}</b>\n"
    text += f"<i>Архетип для {character.class_name}</i>\n\n"
    
    # Описание архетипа (до 600 символов для первого экрана)
    description = arch_data.get("description", "")
    if len(description) > 600:
        text += f"{description[:600]}...\n\n"
    else:
        text += f"{description}\n\n"
    
    # Способности которые получит персонаж на текущем уровне
    skills = arch_data.get("skills", {})
    level_skills = skills.get(str(new_level), [])
    
    if level_skills:
        text += f"<b>⚡ Способности {new_level} уровня:</b>\n"
        for skill in level_skills:
            # Показываем первые 200 символов каждой способности
            if len(skill) > 200:
                text += f"• {skill[:200]}...\n\n"
            else:
                text += f"• {skill}\n\n"
    
    # Заклинания архетипа на текущем уровне
    spells = arch_data.get("spells", {})
    level_spells = spells.get(str(new_level), [])
    
    if level_spells:
        text += f"<b>✨ Особые заклинания {new_level} уровня:</b>\n"
        for spell in level_spells:
            text += f"• {spell}\n"
        text += "\n"
    
    # Краткий обзор что будет на следующих уровнях
    future_levels = [lvl for lvl in sorted(skills.keys(), key=lambda x: int(x)) if int(lvl) > new_level]
    if future_levels:
        text += "<b>📈 На следующих уровнях:</b>\n"
        for lvl in future_levels[:3]:  # Показываем до 3 следующих уровней
            text += f"• {lvl} ур.: новые способности\n"
    
    keyboard = [
        [InlineKeyboardButton(f"✅ Выбрать {arch_name}", callback_data=f"char_lu_ar_{char_id}_{arch_idx}")],
        [InlineKeyboardButton("◀ К списку архетипов", callback_data=f"char_lu_arlist_{char_id}")],
        [InlineKeyboardButton("❌ Отмена", callback_data=f"char_view_{char_id}")]
    ]
    
    return text, InlineKeyboardMarkup(keyboard)


async def cmd_createcharacter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /createcharacter - начать создание персонажа"""
    if not update.message or not update.effective_user:
        return
    
    user_id = update.effective_user.id
    
    # Проверяем, есть ли незавершённая сессия
    existing_session = cc.get_character_session(user_id)
    if existing_session:
        keyboard = [
            [InlineKeyboardButton("✅ Продолжить", callback_data="char_continue")],
            [InlineKeyboardButton("🔄 Начать заново", callback_data="char_restart")],
            [InlineKeyboardButton("❌ Отменить", callback_data="char_create_cancel")]
        ]
        await update.message.reply_text(
            "⚠️ У тебя уже есть незавершённое создание персонажа.\n\nЧто делать?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # Начинаем новое создание
    text, markup = cc.start_character_creation(user_id)
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)


async def cmd_mycharacters(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /mycharacters - список персонажей пользователя"""
    if not update.message or not update.effective_user:
        return
    
    user_id = update.effective_user.id
    characters = load_user_characters(user_id)
    
    if not characters:
        await update.message.reply_text(
            "📜 У тебя пока нет персонажей.\n\n"
            "Создай своего первого героя командой /createcharacter"
        )
        return
    
    text = "📜 <b>Твои персонажи:</b>\n\n"
    
    keyboard = []
    for char in characters:
        char_summary = f"{char.name} ({char.race_name} {char.class_name} {char.level})\n"
        text += f"• {char_summary}"
        
        keyboard.append([
            InlineKeyboardButton(
                f"👤 {char.name}",
                callback_data=f"char_view_{char.id}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("➕ Создать нового", callback_data="char_create_new")])
    
    await update.message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def cmd_levelup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /levelup - повысить уровень персонажа"""
    if not update.message or not update.effective_user:
        return
    
    user_id = update.effective_user.id
    characters = load_user_characters(user_id)
    
    if not characters:
        await update.message.reply_text(
            "📜 У тебя пока нет персонажей.\n\n"
            "Создай своего первого героя командой /createcharacter"
        )
        return
    
    # Фильтруем персонажей, которые могут повысить уровень (< 20)
    upgradable = [c for c in characters if c.level < 20]
    
    if not upgradable:
        await update.message.reply_text(
            "🏆 Все твои персонажи достигли максимального уровня (20)!"
        )
        return
    
    text = "⬆️ <b>Повышение уровня</b>\n\n"
    text += "Выбери персонажа для повышения уровня:\n\n"
    
    keyboard = []
    for char in upgradable:
        char_info = f"{char.name} (ур. {char.level} → {char.level + 1})"
        text += f"• {char_info}\n"
        
        keyboard.append([
            InlineKeyboardButton(
                f"⬆️ {char.name}",
                callback_data=f"char_levelup_{char.id}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="char_list")])
    
    await update.message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def race_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик клика на названию расы"""
    query = update.callback_query
    await query.answer()
    
    race_name = query.data.replace("race_", "")
    
    load_races_data()
    
    if race_name not in RACES_DATA:
        await query.edit_message_text("❌ Раса не найдена")
        return
    
    # Формируем полную информацию о расе
    race_content = RACES_DATA[race_name]
    full_text = f"<b>🎭 {race_name}</b>\n\n"
    
    for section_title, section_content in race_content.items():
        if isinstance(section_content, list) and section_content:
            full_text += f"<b>{section_title}:</b>\n"
            for item in section_content:
                full_text += f"{item}\n\n"
        elif isinstance(section_content, str) and section_content:
            full_text += f"<b>{section_title}:</b> {section_content}\n\n"
    
    # Разбиваем если больше 4096 символов
    max_length = 4096
    if len(full_text) > max_length:
        parts = []
        current_part = ""
        
        for paragraph in full_text.split("\n\n"):
            if len(current_part) + len(paragraph) + 2 < max_length:
                current_part += paragraph + "\n\n"
            else:
                if current_part:
                    parts.append(current_part)
                current_part = paragraph + "\n\n"
        
        if current_part:
            parts.append(current_part)
        
        await query.edit_message_text(parts[0], parse_mode=ParseMode.HTML)
        
        for part in parts[1:]:
            await query.message.reply_text(part, parse_mode=ParseMode.HTML)
    else:
        await query.edit_message_text(full_text, parse_mode=ParseMode.HTML)


async def race_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Пагинация списка рас"""
    query = update.callback_query
    data = query.data.replace("race_page_", "")
    try:
        page = int(data)
    except ValueError:
        page = 1

    text, markup = build_races_page(page=page)
    await query.answer()
    await query.edit_message_text(text, reply_markup=markup, parse_mode=None)


# ========== ОБРАБОТЧИКИ ДЛЯ ЗАКЛИНАНИЙ ==========

async def spell_level_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик возврата к выбору уровня заклинаний"""
    query = update.callback_query
    await query.answer()
    
    text, markup = build_spells_level_selection()
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)


async def spell_level_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик выбора уровня заклинаний"""
    query = update.callback_query
    await query.answer()
    
    level = query.data.replace("spell_level_", "")
    
    # Если это просто выбор уровня, показываем первую страницу списка
    if level != "select":
        text, markup = build_spells_page(level=level, page=1)
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
    else:
        # Возврат к выбору уровня
        text, markup = build_spells_level_selection()
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)


async def spell_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Пагинация списка заклинаний"""
    query = update.callback_query
    data = query.data.replace("spell_page_", "")
    
    if data == "info":
        await query.answer("Информация о текущей странице")
        return
    
    # Формат: level_page или level_1, level_2, etc.
    parts = data.split("_", 1)
    if len(parts) != 2:
        await query.answer("❌ Ошибка навигации")
        return
    
    level = parts[0]
    try:
        page = int(parts[1])
    except ValueError:
        page = 1
    
    text, markup = build_spells_page(level=level, page=page)
    await query.answer()
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)


async def spell_detail_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик клика на заклинание - показ деталей"""
    query = update.callback_query
    await query.answer()
    
    # Формат: spell_level_index (например: spell_1_5)
    data = query.data.replace("spell_", "")
    parts = data.split("_", 1)
    
    if len(parts) != 2:
        await query.edit_message_text("❌ Ошибка: заклинание не найдено")
        return
    
    level = parts[0]
    try:
        spell_index = int(parts[1])
    except ValueError:
        await query.edit_message_text("❌ Ошибка: неверный индекс заклинания")
        return
    
    # Получаем список заклинаний и находим по индексу
    spells_data = load_spells_by_level(level)
    spell_names = sorted(list(spells_data.keys()))
    
    if spell_index < 0 or spell_index >= len(spell_names):
        await query.edit_message_text("❌ Ошибка: заклинание не найдено")
        return
    
    spell_name = spell_names[spell_index]
    detail_text = format_spell_detail_by_name(level=level, spell_name=spell_name)
    
    # Кнопки навигации
    keyboard: list[list[InlineKeyboardButton]] = []
    keyboard.append([InlineKeyboardButton("◀ Назад к списку", callback_data=f"spell_page_{level}_1")])
    keyboard.append([InlineKeyboardButton("🔙 К выбору уровня", callback_data="spell_level_select")])
    
    markup = InlineKeyboardMarkup(keyboard)
    
    # Разбиваем если слишком длинное
    if len(detail_text) > 4096:
        parts = split_message(detail_text, limit=4096)
        await query.edit_message_text(parts[0], parse_mode=ParseMode.HTML, reply_markup=markup)
        for part in parts[1:]:
            await query.message.reply_text(part, parse_mode=ParseMode.HTML)
    else:
        await query.edit_message_text(detail_text, parse_mode=ParseMode.HTML, reply_markup=markup)


# ========== ОБРАБОТЧИКИ ДЛЯ КЛАССОВ ==========

async def class_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Пагинация списка классов"""
    query = update.callback_query
    data = query.data.replace("class_page_", "")
    
    if data == "info":
        await query.answer("Информация о текущей странице")
        return
    
    try:
        page = int(data)
    except ValueError:
        page = 1
    
    text, markup = build_classes_page(page=page)
    await query.answer()
    try:
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
    except Exception:
        pass  # Сообщение не изменилось


# ========== ОБРАБОТЧИКИ ДЛЯ СОЗДАНИЯ ПЕРСОНАЖЕЙ ==========

async def char_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Главный обработчик для создания персонажей"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = query.data
    
    # Отмена создания
    if data == "char_create_cancel":
        text = cc.handle_creation_cancel(user_id)
        await query.edit_message_text(text)
        return
    
    # Создание нового персонажа
    if data == "char_create_new":
        text, markup = cc.start_character_creation(user_id)
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return
    
    # Продолжить незавершённое создание
    if data == "char_continue":
        session = cc.get_character_session(user_id)
        if not session:
            await query.edit_message_text("❌ Сессия не найдена.")
            return
        
        # Определяем текущий шаг и показываем соответствующий экран
        if session.step == cc.CreationStep.NAME:
            text, markup = cc.start_character_creation(user_id)
        elif session.step == cc.CreationStep.RACE:
            text, markup = cc.build_race_selection_message()
        elif session.step == cc.CreationStep.CLASS:
            text, markup = cc.build_class_selection_message()
        elif session.step == cc.CreationStep.BACKGROUND:
            text, markup = cc.build_background_selection_message()
        elif session.step == cc.CreationStep.ABILITIES_METHOD:
            text, markup = cc.build_abilities_method_message()
        elif session.step == cc.CreationStep.ABILITIES_ASSIGN:
            text, markup = cc.build_abilities_assign_message(user_id)
        elif session.step == cc.CreationStep.ABILITIES_POINT_BUY:
            text, markup = cc.build_pointbuy_message(user_id)
        elif session.step == cc.CreationStep.EQUIPMENT:
            text, markup = cc.build_equipment_selection_message(user_id)
        elif session.step == cc.CreationStep.SKILLS:
            text, markup = cc.build_skills_selection_message(user_id)
        elif session.step == cc.CreationStep.SPELLS_CANTRIPS:
            text, markup = cc.build_cantrips_selection_message(user_id)
        elif session.step == cc.CreationStep.SPELLS_KNOWN:
            text, markup = cc.build_spells_selection_message(user_id)
        elif session.step == cc.CreationStep.REVIEW:
            text, markup = cc.build_review_message(user_id)
        else:
            text = "❌ Неизвестный этап создания."
            markup = None
        
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return
    
    # Перезапуск создания
    if data == "char_restart":
        cc.delete_character_session(user_id)
        text, markup = cc.start_character_creation(user_id)
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return
    
    # Выбор расы
    if data.startswith("char_race_"):
        if "page" in data:
            page = int(data.split("_")[-1])
            text, markup = cc.build_race_selection_message(page)
            await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        elif "view" in data:
            # Просмотр расы: char_race_view_{idx}
            race_idx = int(data.split("_")[-1])
            text, markup = cc.build_race_detail_message(race_idx)
            await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        elif "select" in data:
            # Выбор расы: char_race_select_{idx}
            race_idx = int(data.split("_")[-1])
            text, markup = cc.handle_race_selection(user_id, race_idx)
            await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return
    
    # Выбор класса
    if data.startswith("char_class_"):
        if "page" in data:
            page = int(data.split("_")[-1])
            text, markup = cc.build_class_selection_message(page)
            await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        else:
            class_id = data.replace("char_class_", "")
            text, markup = cc.handle_class_selection(user_id, class_id)
            await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return
    
    # Выбор предыстории
    if data.startswith("char_bg_"):
        if "page" in data:
            page = int(data.split("_")[-1])
            text, markup = cc.build_background_selection_message(page)
            await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        else:
            bg_id = data.replace("char_bg_", "")
            text, markup = cc.handle_background_selection(user_id, bg_id)
            await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return
    
    # Выбор метода генерации характеристик
    if data.startswith("char_abilities_"):
        if data == "char_abilities_standard":
            text, markup = cc.handle_abilities_method(user_id, "standard")
            await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        elif data == "char_abilities_roll":
            text, markup = cc.handle_abilities_method(user_id, "roll")
            await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        elif data == "char_abilities_pointbuy":
            text, markup = cc.handle_abilities_method(user_id, "pointbuy")
            await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        elif data == "char_abilities_confirm":
            text, markup = cc.handle_abilities_confirm(user_id)
            await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        elif data == "char_abilities_reset":
            text, markup = cc.handle_abilities_reset(user_id)
            await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        elif data == "char_abilities_assign_back":
            text, markup = cc.build_abilities_assign_message(user_id)
            await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return
    
    # Назначение характеристик
    if data.startswith("char_assign_"):
        parts = data.replace("char_assign_", "").split("_")
        if len(parts) == 1:
            # Показываем выбор значения
            ability = parts[0]
            text, markup = cc.handle_ability_assign(user_id, ability)
            await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        elif len(parts) == 2:
            # Назначаем значение
            ability, score = parts[0], int(parts[1])
            text, markup = cc.handle_ability_assign_value(user_id, ability, score)
            await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return
    
    # Покупка очков
    if data.startswith("char_pb_"):
        if data == "char_pb_reset":
            text, markup = cc.handle_pointbuy_reset(user_id)
            await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        else:
            parts = data.replace("char_pb_", "").split("_")
            if len(parts) == 2:
                ability, change = parts[0], parts[1]
                text, markup = cc.handle_pointbuy_change(user_id, ability, change)
                await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return
    
    # Выбор навыков
    if data == "char_skills_confirm":
        text, markup = cc.handle_skills_confirm(user_id)
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return
    
    if data.startswith("char_skill_"):
        skill = data.replace("char_skill_", "")
        text, markup = cc.handle_skill_selection(user_id, skill)
        try:
            await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        except Exception as e:
            # Игнорируем ошибку если сообщение не изменилось
            if "not modified" not in str(e).lower():
                raise
        return
    
    # Выбор снаряжения
    if data.startswith("char_eq_"):
        if data == "char_eq_take_gold":
            text, markup = cc.handle_equipment_take_gold(user_id)
            await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        elif data == "char_eq_gold_confirm":
            text, markup = cc.handle_equipment_gold_confirm(user_id)
            await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        elif data == "char_eq_back_to_items":
            text, markup = cc.handle_equipment_back_to_items(user_id)
            await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        elif data == "char_eq_reset":
            text, markup = cc.handle_equipment_reset(user_id)
            await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        elif data == "char_eq_confirm":
            text, markup = cc.handle_equipment_confirm(user_id)
            await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        elif data.startswith("char_eq_opt_"):
            option_idx = int(data.replace("char_eq_opt_", ""))
            text, markup = cc.handle_equipment_option(user_id, option_idx)
            await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return
    
    # Подтверждение заговоров (проверяем ДО char_cantrip_)
    if data == "char_cantrips_confirm":
        text, markup = cc.handle_cantrips_confirm(user_id)
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return
    
    # Подтверждение заклинаний (проверяем ДО char_spell_)
    if data == "char_spells_confirm":
        text, markup = cc.handle_spells_confirm(user_id)
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return
    
    # Выбор/снятие выбора заговора
    if data.startswith("char_cantrip_select_"):
        cantrip_idx = int(data.replace("char_cantrip_select_", ""))
        text, markup = cc.handle_cantrip_toggle(user_id, cantrip_idx)
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return
    
    # Возврат к списку заговоров
    if data.startswith("char_cantrip_back"):
        page = 1
        if "_" in data.replace("char_cantrip_back", ""):
            parts = data.split("_")
            if len(parts) > 3:
                page = int(parts[-1])
        text, markup = cc.build_cantrips_selection_message(user_id, page)
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return
    
    # Выбор заговоров - просмотр деталей
    if data.startswith("char_cantrip_"):
        if "page" in data:
            page = int(data.split("_")[-1])
            text, markup = cc.build_cantrips_selection_message(user_id, page)
            await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        else:
            # Показываем детали заговора
            cantrip_idx = int(data.replace("char_cantrip_", ""))
            text, markup = cc.build_cantrip_detail_message(user_id, cantrip_idx)
            await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return
    
    # Выбор/снятие выбора заклинания
    if data.startswith("char_spell_select_"):
        spell_idx = int(data.replace("char_spell_select_", ""))
        text, markup = cc.handle_spell_toggle(user_id, spell_idx)
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return
    
    # Возврат к списку заклинаний
    if data.startswith("char_spell_back"):
        page = 1
        if "_" in data.replace("char_spell_back", ""):
            parts = data.split("_")
            if len(parts) > 3:
                page = int(parts[-1])
        text, markup = cc.build_spells_selection_message(user_id, page)
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return
    
    # Выбор заклинаний - просмотр деталей
    if data.startswith("char_spell_"):
        if "page" in data:
            page = int(data.split("_")[-1])
            text, markup = cc.build_spells_selection_message(user_id, page)
            await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        else:
            # Показываем детали заклинания
            spell_idx = int(data.replace("char_spell_", ""))
            text, markup = cc.build_spell_detail_message(user_id, spell_idx)
            await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return
    
    # Сохранение персонажа
    if data == "char_save":
        text, markup = cc.handle_character_save(user_id)
        if markup:
            await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        else:
            await query.edit_message_text(text, parse_mode=ParseMode.HTML)
        return
    
    # Вкладки обзора персонажа
    if data == "char_review_stats":
        text, markup = cc.build_review_message(user_id, "stats")
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return
    
    if data == "char_review_abilities":
        text, markup = cc.build_review_message(user_id, "abilities")
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return
    
    if data == "char_review_spells":
        text, markup = cc.build_review_message(user_id, "spells")
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return
    
    # Список способностей для просмотра
    if data == "char_review_ability_list":
        text, markup = cc.build_ability_list_message(user_id)
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return
    
    if data.startswith("char_review_ability_page_"):
        page = int(data.replace("char_review_ability_page_", ""))
        text, markup = cc.build_ability_list_message(user_id, page)
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return
    
    if data.startswith("char_review_ability_"):
        ability_idx = int(data.replace("char_review_ability_", ""))
        text, markup = cc.build_ability_detail_message(user_id, ability_idx)
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return
    
    # Список заклинаний для просмотра
    if data.startswith("char_review_spell_list_"):
        spell_type = data.replace("char_review_spell_list_", "")
        text, markup = cc.build_spell_list_message(user_id, spell_type)
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return
    
    if data == "char_review_spell_list":
        text, markup = cc.build_spell_list_message(user_id)
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return
    
    if data.startswith("char_review_spell_"):
        # char_review_spell_{type}_{idx}
        parts = data.replace("char_review_spell_", "").split("_")
        if len(parts) >= 2:
            spell_type = parts[0]
            spell_idx = int(parts[1])
            text, markup = cc.build_review_spell_detail_message(user_id, spell_type, spell_idx)
            await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return
    
    # Просмотр персонажа (новый формат с вкладками)
    if data.startswith("char_view_"):
        char_id = data.replace("char_view_", "")
        character = get_character_by_id(user_id, char_id)
        if not character:
            await query.edit_message_text("❌ Персонаж не найден.")
            return
        
        text, markup = cc.build_saved_character_view(character, "stats")
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return
    
    # Вкладки сохранённого персонажа
    if data.startswith("char_saved_stats_"):
        char_id = data.replace("char_saved_stats_", "")
        character = get_character_by_id(user_id, char_id)
        if not character:
            await query.edit_message_text("❌ Персонаж не найден.")
            return
        text, markup = cc.build_saved_character_view(character, "stats")
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return
    
    if data.startswith("char_saved_abilities_"):
        char_id = data.replace("char_saved_abilities_", "")
        character = get_character_by_id(user_id, char_id)
        if not character:
            await query.edit_message_text("❌ Персонаж не найден.")
            return
        text, markup = cc.build_saved_character_view(character, "abilities")
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return
    
    if data.startswith("char_saved_spells_"):
        char_id = data.replace("char_saved_spells_", "")
        character = get_character_by_id(user_id, char_id)
        if not character:
            await query.edit_message_text("❌ Персонаж не найден.")
            return
        text, markup = cc.build_saved_character_view(character, "spells")
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return
    
    # Список способностей сохранённого персонажа
    if data.startswith("char_saved_ability_list_"):
        char_id = data.replace("char_saved_ability_list_", "")
        character = get_character_by_id(user_id, char_id)
        if not character:
            await query.edit_message_text("❌ Персонаж не найден.")
            return
        text, markup = cc.build_saved_ability_list(character)
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return
    
    if data.startswith("char_saved_ability_page_"):
        # char_saved_ability_page_{char_id}_{page}
        parts = data.replace("char_saved_ability_page_", "").rsplit("_", 1)
        char_id = parts[0]
        page = int(parts[1])
        character = get_character_by_id(user_id, char_id)
        if not character:
            await query.edit_message_text("❌ Персонаж не найден.")
            return
        text, markup = cc.build_saved_ability_list(character, page)
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return
    
    if data.startswith("char_saved_ability_"):
        # char_saved_ability_{char_id}_{idx}
        parts = data.replace("char_saved_ability_", "").rsplit("_", 1)
        char_id = parts[0]
        ability_idx = int(parts[1])
        character = get_character_by_id(user_id, char_id)
        if not character:
            await query.edit_message_text("❌ Персонаж не найден.")
            return
        text, markup = cc.build_saved_ability_detail(character, ability_idx)
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return
    
    # Список заклинаний сохранённого персонажа
    if data.startswith("char_saved_spell_list_"):
        # char_saved_spell_list_{char_id}_{type}
        parts = data.replace("char_saved_spell_list_", "").rsplit("_", 1)
        char_id = parts[0]
        spell_type = parts[1] if len(parts) > 1 else "cantrips"
        character = get_character_by_id(user_id, char_id)
        if not character:
            await query.edit_message_text("❌ Персонаж не найден.")
            return
        text, markup = cc.build_saved_spell_list(character, spell_type)
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return
    
    if data.startswith("char_saved_spell_"):
        # char_saved_spell_{char_id}_{type}_{idx}
        parts = data.replace("char_saved_spell_", "").rsplit("_", 2)
        char_id = parts[0]
        spell_type = parts[1]
        spell_idx = int(parts[2])
        character = get_character_by_id(user_id, char_id)
        if not character:
            await query.edit_message_text("❌ Персонаж не найден.")
            return
        text, markup = cc.build_saved_spell_detail(character, spell_type, spell_idx)
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return
    
    # ========== ОБРАБОТЧИКИ ПОВЫШЕНИЯ УРОВНЯ ==========
    
    # Начало повышения уровня
    if data.startswith("char_levelup_") and not data.startswith("char_levelup_hp_") and not data.startswith("char_levelup_confirm") and not data.startswith("char_levelup_arch_"):
        char_id = data.replace("char_levelup_", "")
        character = get_character_by_id(user_id, char_id)
        if not character:
            await query.edit_message_text("❌ Персонаж не найден.")
            return
        
        if character.level >= 20:
            await query.edit_message_text("❌ Персонаж уже достиг максимального уровня (20).")
            return
        
        # Создаём сессию повышения уровня
        session = lu.create_levelup_session(user_id, character)
        gains = lu.calculate_level_up_gains(character)
        session.gains = gains
        
        # Показываем что получит персонаж
        text = lu.format_level_up_gains(gains)
        text += "\n\n<b>Выберите способ получения хитов:</b>"
        
        avg, dice = gains.hp_roll_options
        keyboard = [
            [InlineKeyboardButton(f"📊 Среднее (+{avg + character.con_mod})", callback_data=f"char_levelup_hp_avg_{char_id}")],
            [InlineKeyboardButton(f"🎲 Бросок (1d{dice}+{character.con_mod})", callback_data=f"char_levelup_hp_roll_{char_id}")],
            [InlineKeyboardButton("❌ Отмена", callback_data=f"char_view_{char_id}")]
        ]
        
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    # Выбор хитов - среднее
    if data.startswith("char_levelup_hp_avg_"):
        char_id = data.replace("char_levelup_hp_avg_", "")
        session = lu.get_levelup_session(user_id)
        if not session:
            await query.edit_message_text("❌ Сессия повышения уровня не найдена.")
            return
        
        session.hp_choice = "average"
        
        # Проверяем, нужны ли дополнительные выборы
        gains = session.gains
        
        # Если есть выбор архетипа
        if gains.archetype_choice and not session.character.archetype_name:
            text, markup = build_archetype_list_message(session)
            await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
            return
        
        # Переходим к подтверждению
        text, markup = build_levelup_confirm_message(session)
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return
    
    # Выбор хитов - бросок
    if data.startswith("char_levelup_hp_roll_"):
        char_id = data.replace("char_levelup_hp_roll_", "")
        session = lu.get_levelup_session(user_id)
        if not session:
            await query.edit_message_text("❌ Сессия повышения уровня не найдена.")
            return
        
        session.hp_choice = "roll"
        
        # Проверяем, нужны ли дополнительные выборы
        gains = session.gains
        
        # Если есть выбор архетипа
        if gains.archetype_choice and not session.character.archetype_name:
            text, markup = build_archetype_list_message(session)
            await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
            return
        
        # Переходим к подтверждению
        text, markup = build_levelup_confirm_message(session)
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return
    
    # Возврат к списку архетипов
    if data.startswith("char_lu_arlist_"):
        char_id = data.replace("char_lu_arlist_", "")
        
        session = lu.get_levelup_session(user_id)
        if not session:
            await query.edit_message_text("❌ Сессия повышения уровня не найдена.")
            return
        
        text, markup = build_archetype_list_message(session)
        try:
            await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        except Exception:
            await query.answer()  # Сообщение не изменилось
        return
    
    # Просмотр деталей архетипа (перед выбором)
    if data.startswith("char_lu_arv_"):
        # char_lu_arv_{char_id}_{idx} - используем rsplit чтобы правильно отделить idx
        rest = data.replace("char_lu_arv_", "")
        parts = rest.rsplit("_", 1)  # Разбиваем только по последнему _
        char_id = parts[0]
        arch_idx = int(parts[1]) if len(parts) > 1 else 0
        
        session = lu.get_levelup_session(user_id)
        if not session:
            await query.edit_message_text("❌ Сессия повышения уровня не найдена.")
            return
        
        text, markup = build_archetype_detail_message(session, arch_idx)
        try:
            await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        except Exception:
            await query.answer()
        return
    
    # Выбор архетипа (подтверждение)
    if data.startswith("char_lu_ar_"):
        rest = data.replace("char_lu_ar_", "")
        parts = rest.rsplit("_", 1)  # Разбиваем только по последнему _
        char_id = parts[0]
        arch_idx = int(parts[1]) if len(parts) > 1 else 0
        
        session = lu.get_levelup_session(user_id)
        if not session:
            await query.edit_message_text("❌ Сессия повышения уровня не найдена.")
            return
        
        # Находим имя архетипа по индексу
        from .character_data import get_archetypes_for_class
        archetypes = get_archetypes_for_class(session.character.class_name)
        arch_names = list(archetypes.keys())
        
        if arch_idx < len(arch_names):
            session.selected_archetype = arch_names[arch_idx]
        
        # Переходим к подтверждению
        text, markup = build_levelup_confirm_message(session)
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return
    
    # Выбор архетипа (старый формат - для совместимости)
    if data.startswith("char_levelup_arch_"):
        parts = data.replace("char_levelup_arch_", "").split("_", 1)
        char_id = parts[0]
        arch_prefix = parts[1] if len(parts) > 1 else ""
        
        session = lu.get_levelup_session(user_id)
        if not session:
            await query.edit_message_text("❌ Сессия повышения уровня не найдена.")
            return
        
        # Находим полное имя архетипа
        from .character_data import get_archetypes_for_class
        archetypes = get_archetypes_for_class(session.character.class_name)
        
        for arch_name in archetypes.keys():
            if arch_name.startswith(arch_prefix) or arch_prefix in arch_name:
                session.selected_archetype = arch_name
                break
        
        # Переходим к подтверждению
        text, markup = build_levelup_confirm_message(session)
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return
    
    # Подтверждение повышения уровня
    if data.startswith("char_levelup_confirm_"):
        char_id = data.replace("char_levelup_confirm_", "")
        session = lu.get_levelup_session(user_id)
        if not session:
            await query.edit_message_text("❌ Сессия повышения уровня не найдена.")
            return
        
        # Применяем повышение уровня
        import random
        character = session.character
        gains = session.gains
        
        # Повышаем уровень
        character.level = gains.new_level
        from .character_data import get_proficiency_bonus
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
        
        # Применяем архетип
        if session.selected_archetype:
            character.archetype_name = session.selected_archetype
        
        # Обновляем информацию о заклинаниях
        character.update_spell_info()
        
        # Сохраняем персонажа
        save_character(character)
        
        # Удаляем сессию
        lu.delete_levelup_session(user_id)
        
        text = f"🎉 <b>{character.name} повышен до {character.level} уровня!</b>\n\n"
        text += f"❤️ HP: +{hp_gain} (всего: {character.max_hp})\n"
        
        if gains.new_features:
            text += "\n<b>Новые способности:</b>\n"
            for feature in gains.new_features:
                text += f"• {feature.get('name', 'Способность')}\n"
        
        if session.selected_archetype:
            text += f"\n🎭 <b>Архетип:</b> {session.selected_archetype}"
        
        keyboard = [[InlineKeyboardButton("👤 К персонажу", callback_data=f"char_view_{char_id}")]]
        
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    # Подтверждение удаления (проверяем ДО char_delete_)
    if data.startswith("char_delete_confirm_"):
        char_id = data.replace("char_delete_confirm_", "")
        
        if delete_character(user_id, char_id):
            await query.edit_message_text("✅ Персонаж удалён.")
        else:
            await query.edit_message_text("❌ Ошибка при удалении персонажа.")
        return
    
    # Удаление персонажа - запрос подтверждения
    if data.startswith("char_delete_"):
        char_id = data.replace("char_delete_", "")
        
        keyboard = [
            [InlineKeyboardButton("✅ Да, удалить", callback_data=f"char_delete_confirm_{char_id}")],
            [InlineKeyboardButton("❌ Отмена", callback_data=f"char_view_{char_id}")]
        ]
        
        await query.edit_message_text(
            "⚠️ Ты уверен, что хочешь удалить этого персонажа?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # Возврат к списку персонажей
    if data == "char_list":
        characters = load_user_characters(user_id)
        
        if not characters:
            await query.edit_message_text(
                "📜 У тебя пока нет персонажей.\n\n"
                "Создай своего первого героя командой /createcharacter"
            )
            return
        
        text = "📜 <b>Твои персонажи:</b>\n\n"
        
        keyboard = []
        for char in characters:
            char_summary = f"{char.name} ({char.race_name} {char.class_name} {char.level})\n"
            text += f"• {char_summary}"
            
            keyboard.append([
                InlineKeyboardButton(
                    f"👤 {char.name}",
                    callback_data=f"char_view_{char.id}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("➕ Создать нового", callback_data="char_create_new")])
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # Информационные callback
    if data == "char_page_info":
        await query.answer("Информация о текущей странице")
        return


async def class_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик клика на класс - показ деталей"""
    query = update.callback_query
    await query.answer()
    
    # Проверяем формат callback_data
    if query.data.startswith("cls_"):
        # Это запрос на детальную секцию (новый формат: cls_{id}_{section}_{page})
        data_parts = query.data.replace("cls_", "").split("_")
        if len(data_parts) >= 3:
            short_id = data_parts[0]
            section_code = data_parts[1]
            try:
                page = int(data_parts[2])
            except ValueError:
                page = 1
            
            # Расшифровываем код секции
            section_map = {
                "a": "abilities",
                "r": "archetypes", 
                "q": "quick_start",
                "m": "main"
            }
            section = section_map.get(section_code)
            
            # Если это не известная секция, ищем полное имя по коду
            if not section:
                # Получаем данные класса для поиска секции
                class_key_temp = _get_class_key_from_id(short_id)
                if class_key_temp:
                    classes_dir = Path(__file__).parent.parent / "data_pars" / "classes"
                    for json_file in classes_dir.glob("*.json"):
                        try:
                            with open(json_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                if class_key_temp in data:
                                    class_data_temp = data[class_key_temp]
                                    # Ищем секцию, которая начинается с этого кода
                                    for key in class_data_temp.keys():
                                        if key.lower().startswith(section_code.lower()):
                                            section = key
                                            break
                                    break
                        except Exception:
                            continue
                
                # Если не нашли, используем код как есть
                if not section:
                    section = section_code
            
            # Получаем полный ключ класса
            class_key = _get_class_key_from_id(short_id)
            if not class_key:
                await query.edit_message_text("❌ Класс не найден")
                return
        elif len(data_parts) == 1 and data_parts[0] == "info":
            # Информационный callback
            await query.answer("Информация о текущей странице")
            return
        else:
            await query.edit_message_text("❌ Ошибка формата запроса")
            return
    elif query.data.startswith("class_"):
        # Старый формат или запрос из списка
        short_id = query.data.replace("class_", "")
        class_key = _get_class_key_from_id(short_id)
        
        if not class_key:
            await query.edit_message_text("❌ Класс не найден")
            return
        
        section = "main"
        page = 1
    else:
        await query.edit_message_text("❌ Неизвестный формат запроса")
        return
    
    # Форматируем детали с пагинацией
    detail_text, markup = format_class_detail(class_key, section=section, page=page)
    
    # Разбиваем если слишком длинное (на случай если всё равно не влезло)
    try:
        if len(detail_text) > 4096:
            parts = split_message(detail_text, limit=4096)
            await query.edit_message_text(parts[0], parse_mode=ParseMode.HTML, reply_markup=markup)
            for part in parts[1:]:
                await query.message.reply_text(part, parse_mode=ParseMode.HTML)
        else:
            await query.edit_message_text(detail_text, parse_mode=ParseMode.HTML, reply_markup=markup)
    except Exception:
        await query.answer()  # Сообщение не изменилось

def main() -> None:
	token = get_bot_token()
	app = ApplicationBuilder().token(token).build()

	# Register handlers for D&D helper bot
	app.add_handler(CommandHandler("start", cmd_start))
	app.add_handler(CommandHandler("help", cmd_help))
	app.add_handler(CommandHandler("rules", cmd_rules))
	app.add_handler(CommandHandler("dice", cmd_dice))
	app.add_handler(CommandHandler("combat", cmd_combat))
	app.add_handler(CommandHandler("stats", cmd_stats))
	app.add_handler(CommandHandler("glossary", cmd_glossary))
	app.add_handler(CommandHandler("races", cmd_races))
	app.add_handler(CommandHandler("spells", cmd_spells))
	app.add_handler(CommandHandler("classes", cmd_classes))
	
	# Обработчики для создания и управления персонажами
	app.add_handler(CommandHandler("createcharacter", cmd_createcharacter))
	app.add_handler(CommandHandler("mycharacters", cmd_mycharacters))
	app.add_handler(CommandHandler("levelup", cmd_levelup))
	
	# Обработчики для создания персонажей (должны быть перед общими обработчиками)
	app.add_handler(CallbackQueryHandler(char_callback_handler, pattern="^char_"))
	
	# Обработчики для просмотра рас
	app.add_handler(CallbackQueryHandler(race_page_callback, pattern="^race_page_"))
	app.add_handler(CallbackQueryHandler(race_callback, pattern="^race_"))
	
	# Обработчики для заклинаний (порядок важен - более специфичные первыми)
	app.add_handler(CallbackQueryHandler(spell_level_select_callback, pattern="^spell_level_select$"))
	app.add_handler(CallbackQueryHandler(spell_page_callback, pattern="^spell_page_"))
	app.add_handler(CallbackQueryHandler(spell_level_callback, pattern="^spell_level_"))
	# Детали заклинаний - паттерн для формата spell_level_index (например: spell_1_5, spell_cantrips_12)
	app.add_handler(CallbackQueryHandler(spell_detail_callback, pattern="^spell_(cantrips|[1-9])_\\d+$"))
	
	# Обработчики для классов (порядок важен - более специфичные первыми)
	app.add_handler(CallbackQueryHandler(class_callback, pattern="^cls_"))
	app.add_handler(CallbackQueryHandler(class_page_callback, pattern="^class_page_"))
	app.add_handler(CallbackQueryHandler(class_callback, pattern="^class_"))

	app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

	print("🎲 D&D Helper Bot is starting... Press Ctrl+C to stop.")
	app.run_polling()


if __name__ == "__main__":
	main()
