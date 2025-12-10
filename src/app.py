import os
from typing import Final, Dict, List, Optional
import json
from pathlib import Path
from telegram.ext import MessageHandler, filters, CallbackQueryHandler, Application, ApplicationBuilder, CommandHandler, ContextTypes
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, KeyboardButton, ReplyKeyboardMarkup, Update
from .ollama import OllamaClient
from dotenv import load_dotenv
from telegram.constants import ParseMode
from .texts import *

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
    races_file = Path(__file__).parent.parent / "data_pars" / "races_descriptions_formatted.txt"
    
    # Проверяем существование файла
    if not races_file.exists():
        # Попробуем альтернативный путь или создать базовый список
        races_data = load_races_data()
        if races_data:
            # Используем данные из JSON, если файл txt не найден
            lines: list[tuple[str, str]] = []
            for race_key, race_info in races_data.items():
                # Извлекаем русское название из ключа
                race_name = race_key
                for i, char in enumerate(race_key):
                    if 'A' <= char <= 'z':  # Нашли английскую букву
                        race_name = race_key[:i].strip()
                        break
                # Берем первое поле как описание
                description = ""
                if race_info:
                    first_key = next(iter(race_info), "")
                    first_value = race_info.get(first_key, "")
                    if isinstance(first_value, list):
                        description = first_value[0] if first_value else ""
                    else:
                        description = str(first_value)
                
                lines.append((race_name, description[:50] + "..." if len(description) > 50 else description))
            return lines
        return []
    
    try:
        raw_text = races_file.read_text(encoding="utf-8").strip()
        if not raw_text:
            print(f"❌ Файл пустой: {races_file}")
            return []
            
    except Exception as e:
        print(f"❌ Ошибка чтения {races_file}: {e}")
        return []

    lines: list[tuple[str, str]] = []
    for line in raw_text.splitlines():
        if not line.strip():
            continue
        name, _, desc = line.partition(" -")
        name = name.lstrip("\ufeff").strip()
        desc = desc.strip(" -")
        if name:  # Добавляем только если есть имя
            lines.append((name, desc))
    
    print(f"✅ Загружено рас: {len(lines)}")
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


def build_races_page(page: int, page_size: int = 10) -> tuple[str, InlineKeyboardMarkup]:
    """
    Сформировать текст и инлайн-клавиатуру для страницы списка рас.
    """
    load_races_data()
    races = load_races_formatted_lines()
    total = len(races)
    
    if total == 0:
        text = "🧝 <b>Расы D&D 5e</b>\n\n"
        text += "❌ <b>Расы не найдены!</b>\n\n"
        text += "Пожалуйста, проверьте наличие файлов с данными."
        
        keyboard = [[InlineKeyboardButton("🔄 Обновить", callback_data="race_page_1")]]
        return text, InlineKeyboardMarkup(keyboard)
    
    total_pages = max(1, (total + page_size - 1) // page_size)
    current_page = min(max(1, page), total_pages)

    start = (current_page - 1) * page_size
    end = start + page_size
    slice_races = races[start:end]

    # Только заголовок без списка рас
    text = f"🧝 <b>Расы D&D 5e</b>\n"
    text += f"Страница {current_page}/{total_pages} • Всего: {total}\n\n"
    text += "Выберите расу для подробной информации:\n"

    keyboard: list[list[InlineKeyboardButton]] = []
    for name, _ in slice_races:
        race_key = resolve_race_key(name)
        if race_key:
            # Используем короткий callback_data для экономии места
            callback_data = f"race_detail_{race_key[:20]}" if len(race_key) > 20 else f"race_detail_{race_key}"
            keyboard.append([InlineKeyboardButton(text=name, callback_data=callback_data)])
        else:
            # Если не нашли ключ, все равно создаем кнопку
            keyboard.append([InlineKeyboardButton(text=name, callback_data=f"race_detail_{name}")])

    # Навигация (без кнопки с номером страницы)
    nav_row: list[InlineKeyboardButton] = []
    if current_page > 1:
        nav_row.append(InlineKeyboardButton("◀️ Назад", callback_data=f"race_page_{current_page - 1}"))
    
    if current_page < total_pages:
        if nav_row:  # Если уже есть кнопка "Назад", добавляем "Вперед" в тот же ряд
            nav_row.append(InlineKeyboardButton("Вперёд ▶️", callback_data=f"race_page_{current_page + 1}"))
        else:
            nav_row.append(InlineKeyboardButton("Вперёд ▶️", callback_data=f"race_page_{current_page + 1}"))
    
    if nav_row:
        keyboard.append(nav_row)

    return text, InlineKeyboardMarkup(keyboard)


def build_race_detail_page(race_key: str, page: int = 1) -> tuple[str, InlineKeyboardMarkup]:
    """
    Сформировать страницу с детальной информацией о расе с пагинацией.
    Фиксированное количество строк (10-12) на страницу для большего количества страниц.
    """
    load_races_data()
    
    # Ищем расу в данных
    race_data = None
    race_name_display = race_key
    
    # Пытаемся найти расу по ключу
    for key, data in RACES_DATA.items():
        if key.startswith(race_key) or race_key in key:
            race_data = data
            # Извлекаем русское название из ключа
            for i, char in enumerate(key):
                if 'A' <= char <= 'z':  # Нашли английскую букву
                    race_name_display = key[:i].strip()
                    break
            break
    
    # Если не нашли по ключу, ищем по русскому названию
    if not race_data:
        for key, data in RACES_DATA.items():
            # Извлекаем русское название
            race_name = key
            for i, char in enumerate(key):
                if 'A' <= char <= 'z':
                    race_name = key[:i].strip()
                    break
            
            if race_name == race_key:
                race_data = data
                race_name_display = race_name
                break
    
    if not race_data:
        return "❌ Информация о расе не найдена", InlineKeyboardMarkup([])
    
    # Формируем полный текст
    full_text = f"🧝 <b>{race_name_display}</b>\n\n"
    
    if isinstance(race_data, dict):
        for section_title, section_content in race_data.items():
            if isinstance(section_content, list) and section_content:
                full_text += f"<b>{section_title}:</b>\n"
                for item in section_content:
                    full_text += f"• {item}\n"
                full_text += "\n"
            elif isinstance(section_content, str) and section_content.strip():
                full_text += f"<b>{section_title}:</b> {section_content}\n\n"
    else:
        # Если данные не в ожидаемом формате
        full_text += str(race_data)
    
    # Разбиваем текст на строки
    lines = full_text.split('\n')
    total_lines = len(lines)
    
    # ФИКСИРОВАННОЕ количество строк на страницу
    LINES_PER_PAGE = 12
    
    # Вычисляем общее количество страниц
    total_pages = max(1, (total_lines + LINES_PER_PAGE - 1) // LINES_PER_PAGE)
    current_page = min(max(1, page), total_pages)
    
    # Вычисляем диапазон строк для текущей страницы
    start_line = (current_page - 1) * LINES_PER_PAGE
    end_line = min(start_line + LINES_PER_PAGE, total_lines)
    
    # Формируем текст текущей страницы
    page_text = '\n'.join(lines[start_line:end_line])
    
    # Добавляем информацию о странице
    page_text += f"\n\n📄 Страница {current_page}/{total_pages}"
    
    # Проверяем длину
    if len(page_text) > 4096:
        # Если все еще слишком длинный, принудительно укорачиваем
        page_text = page_text[:4000] + "\n\n📝 <i>Текст продолжается на следующей странице...</i>"
    
    # Создаем клавиатуру
    keyboard: list[list[InlineKeyboardButton]] = []
    
    # Кнопки навигации
    nav_row: list[InlineKeyboardButton] = []
    
    if current_page > 1:
        nav_row.append(InlineKeyboardButton("◀️ Назад", 
                     callback_data=f"race_detail_page_{race_key}_{current_page - 1}"))
    
    if current_page < total_pages:
        if nav_row:
            nav_row.append(InlineKeyboardButton("Вперёд ▶️", 
                         callback_data=f"race_detail_page_{race_key}_{current_page + 1}"))
        else:
            nav_row.append(InlineKeyboardButton("Вперёд ▶️", 
                         callback_data=f"race_detail_page_{race_key}_{current_page + 1}"))
    
    if nav_row:
        keyboard.append(nav_row)
    
    # Кнопка возврата к списку рас
    keyboard.append([InlineKeyboardButton("🔙 К списку рас", callback_data="race_page_1")])
    
    return page_text, InlineKeyboardMarkup(keyboard)


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
        return "Заговоры"
    elif level == "1":
        return "1 уровень"
    else:
        return f"{level} уровень"


def build_spells_level_selection() -> tuple[str, InlineKeyboardMarkup]:
    """Сформировать экран выбора уровня заклинаний"""
    text = "✨ <b>Выберите уровень заклинаний:</b>\n\n"
    text += "Заговоры — базовые заклинания, не требующие ячеек\n"
    text += "1-9 уровень — заклинания разной силы"
    
    keyboard: list[list[InlineKeyboardButton]] = []
    
    # Заговоры
    keyboard.append([InlineKeyboardButton("✨ Заговоры", callback_data="spell_level_cantrips")])
    
    # Уровни 1-9 в три колонки
    levels_row: list[InlineKeyboardButton] = []
    for i in range(1, 10):
        levels_row.append(InlineKeyboardButton(f"{i} ур.", callback_data=f"spell_level_{i}"))
        if len(levels_row) == 3:
            keyboard.append(levels_row)
            levels_row = []
    if levels_row:
        keyboard.append(levels_row)
    
    return text, InlineKeyboardMarkup(keyboard)


def build_spells_page(level: str, page: int = 1, page_size: int = 8) -> tuple[str, InlineKeyboardMarkup]:
    """
    Сформировать текст и инлайн-клавиатуру для страницы списка заклинаний уровня.
    """
    spells_data = load_spells_by_level(level)
    spell_names = sorted(list(spells_data.keys()))
    
    total = len(spell_names)
    if total == 0:
        level_name = get_spell_level_display_name(level)
        text = f"✨ <b>{level_name}</b>\n\n"
        text += "❌ Заклинания этого уровня не найдены"
        
        keyboard: list[list[InlineKeyboardButton]] = []
        keyboard.append([InlineKeyboardButton("🔙 К выбору уровня", callback_data="spell_level_select")])
        return text, InlineKeyboardMarkup(keyboard)
    
    total_pages = max(1, (total + page_size - 1) // page_size)
    current_page = min(max(1, page), total_pages)
    
    start = (current_page - 1) * page_size
    end = start + page_size
    slice_spells = spell_names[start:end]
    
    level_name = get_spell_level_display_name(level)
    text = f"✨ <b>{level_name}</b>\n"
    text += f"Страница {current_page}/{total_pages} • Всего: {total}\n\n"
    text += "Выберите заклинание для подробной информации:"
    
    keyboard: list[list[InlineKeyboardButton]] = []
    
    # Кнопки заклинаний (по 2 в ряд для компактности)
    # Сохраняем номер страницы в callback_data для возврата
    spell_row: list[InlineKeyboardButton] = []
    for idx, name in enumerate(slice_spells):
        # Используем глобальный индекс в отсортированном списке
        global_idx = start + idx
        
        # Формат: spell_detail_{level}_{index}_{current_page}
        callback_data = f"spell_detail_{level}_{global_idx}_{current_page}"
        
        # Ограничиваем текст кнопки для читаемости
        button_text = name
        if len(name) > 25:
            # Находим последний пробел до 25 символов
            cutoff = 22
            if ' ' in name[:25]:
                # Находим последний пробел до 25 символов
                cutoff = name[:25].rfind(' ')
                if cutoff < 15:  # Если последний пробел слишком рано
                    cutoff = 22
            button_text = name[:cutoff] + "..."
        
        spell_row.append(InlineKeyboardButton(text=button_text, callback_data=callback_data))
        if len(spell_row) == 2:
            keyboard.append(spell_row)
            spell_row = []
    
    if spell_row:
        keyboard.append(spell_row)
    
    # Навигация (без кнопки с номером страницы)
    nav_row: list[InlineKeyboardButton] = []
    if current_page > 1:
        nav_row.append(InlineKeyboardButton("◀️ Назад", callback_data=f"spell_page_{level}_{current_page - 1}"))
    
    if current_page < total_pages:
        nav_row.append(InlineKeyboardButton("Вперёд ▶️", callback_data=f"spell_page_{level}_{current_page + 1}"))
    
    if nav_row:
        keyboard.append(nav_row)
    
    # Кнопка возврата к выбору уровня
    keyboard.append([InlineKeyboardButton("🔙 К выбору уровня", callback_data="spell_level_select")])
    
    return text, InlineKeyboardMarkup(keyboard)


def format_spell_detail_by_name(level: str, spell_name: str) -> str:
    """Форматировать детальную информацию о заклинании по имени"""
    spells_data = load_spells_by_level(level)
    
    if spell_name not in spells_data:
        return f"❌ Заклинание '{spell_name}' не найдено"
    
    spell_data = spells_data[spell_name]
    
    level_name = get_spell_level_display_name(level)
    text_parts = [f"✨ <b>{spell_name}</b>\n"]
    text_parts.append(f"<i>{level_name}</i>\n\n")
    
    # Определяем ключ для уровня и школы
    level_school_key = None
    possible_keys = ["Уровень и школа", "информация", "Информация", "Уровень"]
    for key in possible_keys:
        if key in spell_data:
            level_school_key = key
            break
    
    if level_school_key and spell_data[level_school_key]:
        text_parts.append(f"<b>{level_school_key}:</b> {spell_data[level_school_key]}\n")
    
    # Остальные поля (кроме описания)
    for key, value in spell_data.items():
        if key in ["Уровень и школа", "информация", "Информация", "Уровень", "описание", "Описание"]:
            continue
        
        if isinstance(value, str) and value.strip():
            text_parts.append(f"<b>{key}:</b> {value}\n")
        elif isinstance(value, list) and value:
            # Фильтруем пустые значения в списке
            filtered_values = [str(v).strip() for v in value if str(v).strip()]
            if filtered_values:
                text_parts.append(f"<b>{key}:</b> {', '.join(filtered_values)}\n")
    
    # Описание в конце
    desc_key = None
    for key in ["описание", "Описание", "description"]:
        if key in spell_data:
            desc_key = key
            break
    
    if desc_key and spell_data[desc_key]:
        text_parts.append(f"\n<b>Описание:</b>\n{spell_data[desc_key]}")
    
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

def build_classes_simple_page() -> tuple[str, InlineKeyboardMarkup]:
    """
    Упрощенная страница со списком классов - все классы на одной странице
    """
    classes = load_classes_list()
    total = len(classes)
    
    # Эмодзи для классов
    class_emojis = {
        "Воин": "⚔️",
        "Варвар": "🪓",
        "Бард": "🎵",
        "Жрец": "🙏",
        "Волшебник": "🔮",
        "Плут": "🗡️",
        "Друид": "🌿",
        "Паладин": "🛡️",
        "Изобретатель": "⚙️",
        "Следопыт": "🏹",
        "Колдун": "👁️",
        "Монах": "🥋",
        "Чародей": "✨"
    }
    
    # Формируем текст
    text = f"<b>⚔️ Классы D&D 5e</b>\n"
    text += f"<i>Всего классов: {total}</i>\n\n"
    text += "Выберите класс для подробной информации:"
    
    # Создаем клавиатуру
    keyboard = []
    
    # Кнопки классов (в 2 столбца)
    row = []
    for i, class_name in enumerate(classes, 1):
        emoji = class_emojis.get(class_name, "🎭")
        button_text = f"{emoji} {class_name}"
        
        # Получаем ключ класса
        class_key = resolve_class_key(class_name)
        if class_key:
            # Используем короткий ID
            short_id = _register_class_key(class_key)
            callback_data = f"cls_{short_id}_m_1"  # Формат для перехода сразу в основную секцию
        else:
            callback_data = f"class_{class_name}"
        
        row.append(InlineKeyboardButton(button_text, callback_data=callback_data))
        
        # Добавляем новую строку после каждого второго элемента
        if i % 2 == 0:
            keyboard.append(row)
            row = []
    
    # Если остались недобавленные кнопки (нечетное количество классов)
    if row:
        keyboard.append(row)
    
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
            
            # Навигация (без кнопки с номером страницы)
            nav_row = []
            if current_page > 1:
                nav_row.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"cls_{short_id}_a_{current_page - 1}"))
            if current_page < total_pages:
                nav_row.append(InlineKeyboardButton("Вперёд ➡️", callback_data=f"cls_{short_id}_a_{current_page + 1}"))
            if nav_row:
                keyboard.append(nav_row)
        
        elif isinstance(abilities, str):
            # Разбиваем длинный текст на части
            parts = split_message(abilities, limit=3500)
            total_pages = len(parts)
            current_page = min(max(1, page), total_pages)
            
            text_parts.append(parts[current_page - 1])
            text_parts.append(f"\n<i>Страница {current_page}/{total_pages}</i>")
            
            # Навигация (без кнопки с номером страницы)
            nav_row = []
            if current_page > 1:
                nav_row.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"cls_{short_id}_a_{current_page - 1}"))
            if current_page < total_pages:
                nav_row.append(InlineKeyboardButton("Вперёд ➡️", callback_data=f"cls_{short_id}_a_{current_page + 1}"))
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
                if isinstance(arch_data, dict):
                    if "Описание" in arch_data:
                        desc = arch_data["Описание"]
                        if isinstance(desc, list):
                            desc_text = "\n".join([d for d in desc if d and d.strip()][:3])
                            if desc_text:
                                text_parts.append(f"{desc_text}\n")
                        elif isinstance(desc, str):
                            text_parts.append(f"{desc[:500]}...\n" if len(desc) > 500 else f"{desc}\n")
            
            text_parts.append(f"<i>Страница {current_page}/{total_pages}</i>")
            
            # Навигация (без кнопки с номером страницы)
            nav_row = []
            if current_page > 1:
                nav_row.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"cls_{short_id}_r_{current_page - 1}"))
            if current_page < total_pages:
                nav_row.append(InlineKeyboardButton("Вперёд ➡️", callback_data=f"cls_{short_id}_r_{current_page + 1}"))
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
            
            # Навигация - используем короткое имя секции (без кнопки с номером страницы)
            section_short = section[:3].lower() if len(section) >= 3 else section.lower()
            nav_row = []
            if current_page > 1:
                nav_row.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"cls_{short_id}_{section_short}_{current_page - 1}"))
            if current_page < total_pages:
                nav_row.append(InlineKeyboardButton("Вперёд ➡️", callback_data=f"cls_{short_id}_{section_short}_{current_page + 1}"))
            if nav_row:
                keyboard.append(nav_row)
        
        elif isinstance(value, str):
            parts = split_message(value, limit=3500)
            total_pages = len(parts)
            current_page = min(max(1, page), total_pages)
            
            text_parts.append(parts[current_page - 1])
            text_parts.append(f"\n<i>Страница {current_page}/{total_pages}</i>")
            
            # Навигация - используем короткое имя секции (без кнопки с номером страницы)
            section_short = section[:3].lower() if len(section) >= 3 else section.lower()
            nav_row = []
            if current_page > 1:
                nav_row.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"cls_{short_id}_{section_short}_{current_page - 1}"))
            if current_page < total_pages:
                nav_row.append(InlineKeyboardButton("Вперёд ➡️", callback_data=f"cls_{short_id}_{section_short}_{current_page + 1}"))
            if nav_row:
                keyboard.append(nav_row)
    
    # Кнопки навигации в зависимости от секции
    if section != "main":
        # В дополнительных секциях добавляем кнопку "Назад к классу"
        keyboard.append([InlineKeyboardButton("◀️ Назад к классу", callback_data=f"cls_{short_id}_m_1")])
    
    # Кнопка возврата к списку классов (добавляется всегда)
    keyboard.append([InlineKeyboardButton("🔙 К списку классов", callback_data="class_page_1")])
    
    return "\n".join(text_parts), InlineKeyboardMarkup(keyboard)

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start с меню кнопок"""
    if update.message:
        # Создаем клавиатуру
        keyboard = [
            [KeyboardButton("👤 Создать персонажа"), KeyboardButton("🎲 Броски костей")],
            [KeyboardButton("⚔️ Боевая система"), KeyboardButton("📊 Характеристики")],
            [KeyboardButton("📚 Глоссарий"), KeyboardButton("❓ Помощь")],
			[KeyboardButton("👀 Классы"), KeyboardButton("👥 Расы")],
			[KeyboardButton("🔮 Заклинания")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            START_TEXT,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )

async def handle_reply_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатий на кнопки Reply-клавиатуры"""
    if not update.message or not update.message.text:
        return
    
    text = update.message.text
    user_id = update.effective_user.id
    
    if text == "👤 Создать персонажа":
        await update.message.reply_text("Функция создания персонажа в разработке...")
        
    elif text == "🎲 Броски костей":
        session = UserSession(user_id)
        session.set_section("dice", DICE_RULES_TEXT_PART1 + DICE_RULES_TEXT_PART2 + DICE_RULES_TEXT_PART3 + DICE_RULES_TEXT_PART4 + DICE_RULES_TEXT_PART5)
        keyboard = [[InlineKeyboardButton("Далее ➡️", callback_data="dice_1")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"🎲 <b>Броски костей (1/5):</b>\n\n{DICE_RULES_TEXT_PART1}",
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
        
    elif text == "⚔️ Боевая система":
        session = UserSession(user_id)
        session.set_section("combat", 
            COMBAT_RULES_TEXT_PART1 + COMBAT_RULES_TEXT_PART2 + 
            COMBAT_RULES_TEXT_PART3 + COMBAT_RULES_TEXT_PART4 +
            COMBAT_RULES_TEXT_PART5 + COMBAT_RULES_TEXT_PART6 +
            COMBAT_RULES_TEXT_PART7
        )
        keyboard = [[InlineKeyboardButton("Далее ➡️", callback_data="combat_1")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"⚔️ <b>Боевая система (1/7):</b>\n\n{COMBAT_RULES_TEXT_PART1}",
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
        
    elif text == "📊 Характеристики":
        session = UserSession(user_id)
        session.set_section("stats", 
            STATS_TEXT_PART1 + STATS_TEXT_PART2 + STATS_TEXT_PART3 +
            STATS_TEXT_PART4 + STATS_TEXT_PART5 + STATS_TEXT_PART6 +
            STATS_TEXT_PART7 + STATS_TEXT_PART8 + STATS_TEXT_PART9 +
            STATS_TEXT_PART10
        )
        keyboard = [[InlineKeyboardButton("Далее ➡️", callback_data="stats_1")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"📊 <b>Характеристики (1/10):</b>\n\n{STATS_TEXT_PART1}",
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
        
    elif text == "📚 Глоссарий":
        session = UserSession(user_id)
        session.set_section("glossary", 
            GLOSSARY_TEXT_PART1 + GLOSSARY_TEXT_PART2 + GLOSSARY_TEXT_PART3 +
            GLOSSARY_TEXT_PART4 + GLOSSARY_TEXT_PART5
        )
        keyboard = [[InlineKeyboardButton("Далее ➡️", callback_data="glossary_1")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"📚 <b>Глоссарий (1/5):</b>\n\n{GLOSSARY_TEXT_PART1}",
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
        
    elif text == "❓ Помощь":
        await update.message.reply_text(HELP_TEXT, parse_mode=ParseMode.HTML)
    
    elif text == "👀 Классы":
        # Вызываем функцию для отображения классов
        await cmd_classes(update, context)
        
    elif text == "👥 Расы":
        # Вызываем функцию для отображения рас
        await cmd_races(update, context)
        
    elif text == "🔮 Заклинания":
        # Вызываем функцию для отображения заклинаний
        await cmd_spells(update, context)

async def handle_inline_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик inline-кнопок для всех разделов"""
    query = update.callback_query
    await query.answer()
    
    # Вспомогательные функции для создания кнопок
    def create_nav_buttons(current: int, total: int, prefix: str):
        """Создает кнопки навигации"""
        buttons = []
        if current > 0:
            buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"{prefix}_{current-1}"))
        if current < total - 1:
            buttons.append(InlineKeyboardButton("Далее ➡️", callback_data=f"{prefix}_{current+1}"))
        return [buttons] if buttons else []
    
    # Обработка для Основных правил
    if query.data.startswith("rules_"):
        part_num = int(query.data.split("_")[1])
        total_parts = 3
        parts = [RULES_TEXT_PART1, RULES_TEXT_PART2, RULES_TEXT_PART3]
        
        reply_markup = InlineKeyboardMarkup(create_nav_buttons(part_num, total_parts, "rules"))
        await query.edit_message_text(
            f"📚 <b>Основные правила ({part_num+1}/{total_parts}):</b>\n\n{parts[part_num]}",
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    # Обработка для Бросков костей 
    elif query.data.startswith("dice_"):
        part_num = int(query.data.split("_")[1])
        total_parts = 5
        parts = [DICE_RULES_TEXT_PART1, DICE_RULES_TEXT_PART2, DICE_RULES_TEXT_PART3, 
                DICE_RULES_TEXT_PART4, DICE_RULES_TEXT_PART5]
        
        reply_markup = InlineKeyboardMarkup(create_nav_buttons(part_num, total_parts, "dice"))
        await query.edit_message_text(
            f"🎲 <b>Броски костей ({part_num+1}/{total_parts}):</b>\n\n{parts[part_num]}",
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    # Обработка для Боевой системы 
    elif query.data.startswith("combat_"):
        part_num = int(query.data.split("_")[1])
        total_parts = 7
        parts = [COMBAT_RULES_TEXT_PART1, COMBAT_RULES_TEXT_PART2, COMBAT_RULES_TEXT_PART3,
                COMBAT_RULES_TEXT_PART4, COMBAT_RULES_TEXT_PART5, COMBAT_RULES_TEXT_PART6,
                COMBAT_RULES_TEXT_PART7]
        
        reply_markup = InlineKeyboardMarkup(create_nav_buttons(part_num, total_parts, "combat"))
        await query.edit_message_text(
            f"⚔️ <b>Боевая система ({part_num+1}/{total_parts}):</b>\n\n{parts[part_num]}",
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    # Обработка для Характеристик
    elif query.data.startswith("stats_"):
        part_num = int(query.data.split("_")[1])
        total_parts = 10
        parts = [STATS_TEXT_PART1, STATS_TEXT_PART2, STATS_TEXT_PART3, STATS_TEXT_PART4,
                STATS_TEXT_PART5, STATS_TEXT_PART6, STATS_TEXT_PART7, STATS_TEXT_PART8,
                STATS_TEXT_PART9, STATS_TEXT_PART10]
        
        reply_markup = InlineKeyboardMarkup(create_nav_buttons(part_num, total_parts, "stats"))
        await query.edit_message_text(
            f"📊 <b>Характеристики ({part_num+1}/{total_parts}):</b>\n\n{parts[part_num]}",
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    # Обработка для Глоссария 
    elif query.data.startswith("glossary_"):
        part_num = int(query.data.split("_")[1])
        total_parts = 5
        parts = [GLOSSARY_TEXT_PART1, GLOSSARY_TEXT_PART2, GLOSSARY_TEXT_PART3,
                GLOSSARY_TEXT_PART4, GLOSSARY_TEXT_PART5]
        
        reply_markup = InlineKeyboardMarkup(create_nav_buttons(part_num, total_parts, "glossary"))
        await query.edit_message_text(
            f"📚 <b>Глоссарий ({part_num+1}/{total_parts}):</b>\n\n{parts[part_num]}",
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )

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
        self.section_content = RULES_TEXT_PART1 + RULES_TEXT_PART2 + RULES_TEXT_PART3
    
    @staticmethod
    def get_or_create(user_id: int) -> "UserSession":
        """Получить или создать сессию пользователя"""
        if user_id not in user_sessions:
            user_sessions[user_id] = {
                "section": "rules",
                "content": RULES_TEXT_PART1 + RULES_TEXT_PART2 + RULES_TEXT_PART3
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
            "content": RULES_TEXT_PART1 + RULES_TEXT_PART2 + RULES_TEXT_PART3
        })
        return session.get("section", "rules"), session.get("content", RULES_TEXT_PART1 + RULES_TEXT_PART2 + RULES_TEXT_PART3)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	"""Обработчик обычных текстовых сообщений через Ollama"""
	if not update.message or not update.message.text:
		return

	user_id = update.effective_user.id
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

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text(HELP_TEXT, parse_mode=ParseMode.HTML)

async def cmd_rules(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message and update.effective_user:
        user_id = update.effective_user.id
        session = UserSession(user_id)
        session.set_section("rules", RULES_TEXT_PART1 + RULES_TEXT_PART2 + RULES_TEXT_PART3)
        keyboard = [[InlineKeyboardButton("Далее ➡️", callback_data="rules_1")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            RULES_TEXT_PART1,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )

async def cmd_dice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message and update.effective_user:
        user_id = update.effective_user.id
        session = UserSession(user_id)
        session.set_section("dice", DICE_RULES_TEXT_PART1 + DICE_RULES_TEXT_PART2 + DICE_RULES_TEXT_PART3 + DICE_RULES_TEXT_PART4 + DICE_RULES_TEXT_PART5)
        keyboard = [[InlineKeyboardButton("Далее ➡️", callback_data="dice_1")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            DICE_RULES_TEXT_PART1,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )

async def cmd_combat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message and update.effective_user:
        user_id = update.effective_user.id
        session = UserSession(user_id)
        session.set_section("combat", 
            COMBAT_RULES_TEXT_PART1 + COMBAT_RULES_TEXT_PART2 + 
            COMBAT_RULES_TEXT_PART3 + COMBAT_RULES_TEXT_PART4 +
            COMBAT_RULES_TEXT_PART5 + COMBAT_RULES_TEXT_PART6 +
            COMBAT_RULES_TEXT_PART7
        )
        keyboard = [[InlineKeyboardButton("Далее ➡️", callback_data="combat_1")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            COMBAT_RULES_TEXT_PART1,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message and update.effective_user:
        user_id = update.effective_user.id
        session = UserSession(user_id)
        session.set_section("stats", 
            STATS_TEXT_PART1 + STATS_TEXT_PART2 + STATS_TEXT_PART3 +
            STATS_TEXT_PART4 + STATS_TEXT_PART5 + STATS_TEXT_PART6 +
            STATS_TEXT_PART7 + STATS_TEXT_PART8 + STATS_TEXT_PART9 +
            STATS_TEXT_PART10
        )
        keyboard = [[InlineKeyboardButton("Далее ➡️", callback_data="stats_1")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            STATS_TEXT_PART1,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )

async def cmd_glossary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message and update.effective_user:
        user_id = update.effective_user.id
        session = UserSession(user_id)
        session.set_section("glossary", 
            GLOSSARY_TEXT_PART1 + GLOSSARY_TEXT_PART2 + GLOSSARY_TEXT_PART3 +
            GLOSSARY_TEXT_PART4 + GLOSSARY_TEXT_PART5
        )
        keyboard = [[InlineKeyboardButton("Далее ➡️", callback_data="glossary_1")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            GLOSSARY_TEXT_PART1,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )

async def cmd_classes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /classes - красивый список классов с инлайн-кнопками"""
    if not update.message:
        return
    
    user_id = update.effective_user.id
    session = UserSession(user_id)
    session.set_section("classes", "")

    # Убраны параметры page и page_size
    text, markup = build_classes_simple_page()
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)

async def cmd_races(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /races - список рас с кликабельными названиями"""
    if not update.message or not update.effective_user:
        return
    
    user_id = update.effective_user.id
    session = UserSession(user_id)
    session.set_section("races", "")

    text, markup = build_races_page(page=1)
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)

async def cmd_spells(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /spells - выбор уровня заклинаний"""
    if not update.message or not update.effective_user:
        return
    
    user_id = update.effective_user.id
    session = UserSession(user_id)
    session.set_section("spells", "")
    
    text, markup = build_spells_level_selection()
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)

async def race_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик клика на название расы"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if not data.startswith("race_detail_"):
        await query.edit_message_text("❌ Ошибка: неверный формат данных")
        return
    
    race_key_part = data.replace("race_detail_", "")
    
    # Показываем первую страницу детальной информации
    text, markup = build_race_detail_page(race_key_part, page=1)
    
    # Проверяем длину текста и разбиваем при необходимости
    if len(text) > 4096:
        # Разбиваем текст на части
        parts = split_message(text)
        if parts:
            # Отправляем первую часть с кнопками
            await query.edit_message_text(parts[0], parse_mode=ParseMode.HTML, reply_markup=markup)
            # Остальные части без кнопок
            for part in parts[1:]:
                await query.message.reply_text(part, parse_mode=ParseMode.HTML)
        else:
            await query.edit_message_text("❌ Ошибка: текст слишком длинный", parse_mode=ParseMode.HTML)
    else:
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)


async def race_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Пагинация списка рас и детальной информации"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("race_page_"):
        try:
            page = int(data.replace("race_page_", ""))
        except ValueError:
            page = 1

        text, markup = build_races_page(page=page)
        await query.edit_message_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
    elif data.startswith("race_detail_page_"):
        # Пагинация внутри детальной информации о расе
        parts = data.replace("race_detail_page_", "").split("_")
        if len(parts) >= 2:
            try:
                page = int(parts[-1])
                # Собираем ключ расы (может содержать подчеркивания)
                race_key_parts = parts[:-1]
                race_key = "_".join(race_key_parts)
                
                text, markup = build_race_detail_page(race_key, page=page)
                
                # Проверяем длину текста и разбиваем при необходимости
                if len(text) > 4096:
                    # Разбиваем текст на части
                    message_parts = split_message(text)
                    if message_parts:
                        # Отправляем первую часть с кнопками
                        await query.edit_message_text(message_parts[0], parse_mode=ParseMode.HTML, reply_markup=markup)
                        # Остальные части без кнопок
                        for part in message_parts[1:]:
                            await query.message.reply_text(part, parse_mode=ParseMode.HTML)
                    else:
                        await query.edit_message_text("❌ Ошибка: текст слишком длинный", parse_mode=ParseMode.HTML)
                else:
                    await query.edit_message_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
            except ValueError:
                await query.edit_message_text("❌ Ошибка пагинации")

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
    
    data = query.data
    
    if data == "spell_level_select":
        # Возврат к выбору уровня
        text, markup = build_spells_level_selection()
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
    elif data.startswith("spell_level_"):
        # Выбор конкретного уровня
        level = data.replace("spell_level_", "")
        text, markup = build_spells_page(level=level, page=1)
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)


async def spell_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Пагинация списка заклинаний"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    # Формат: spell_page_{level}_{page}
    if data.startswith("spell_page_"):
        data_parts = data.replace("spell_page_", "")
        parts = data_parts.split("_")
        
        if len(parts) < 2:
            await query.answer("❌ Ошибка навигации")
            return
        
        level = parts[0]
        try:
            page = int(parts[1])
        except ValueError:
            page = 1
        
        text, markup = build_spells_page(level=level, page=page)
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)


async def spell_detail_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик клика на заклинание - показ деталей"""
    query = update.callback_query
    await query.answer()
    
    # Формат: spell_detail_{level}_{index}_{current_page}
    data = query.data.replace("spell_detail_", "")
    parts = data.split("_")
    
    if len(parts) < 3:
        await query.edit_message_text("❌ Ошибка: неверный формат данных")
        return
    
    level = parts[0]
    try:
        spell_index = int(parts[1])
        return_page = int(parts[2])  # Страница, с которой пришли
    except ValueError:
        await query.edit_message_text("❌ Ошибка: неверные параметры")
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
    keyboard.append([InlineKeyboardButton("◀️ Назад к списку", callback_data=f"spell_page_{level}_{return_page}")])
    keyboard.append([InlineKeyboardButton("🔙 К выбору уровня", callback_data="spell_level_select")])
    
    markup = InlineKeyboardMarkup(keyboard)
    
    # Разбиваем если слишком длинное (Telegram ограничение - 4096 символов)
    if len(detail_text) > 4000:
        parts = split_message(detail_text, limit=4000)
        await query.edit_message_text(parts[0], parse_mode=ParseMode.HTML, reply_markup=markup)
        for part in parts[1:]:
            await query.message.reply_text(part, parse_mode=ParseMode.HTML)
    else:
        await query.edit_message_text(detail_text, parse_mode=ParseMode.HTML, reply_markup=markup)


# ========== ОБРАБОТЧИКИ ДЛЯ КЛАССОВ ==========


async def classes_simple_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик упрощенных колбэков для классов"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("class_simple_"):
        # Показ деталей класса
        short_id = data.replace("class_simple_", "")
        class_key = _get_class_key_from_id(short_id)
        
        if class_key:
            text, markup = format_class_simple_detail(class_key)
            await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        else:
            await query.edit_message_text("❌ Класс не найден")
    
    elif data.startswith("classes_page_"):
        # Пагинация - теперь просто показываем список
        text, markup = build_classes_simple_page()  # Без параметров
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
    
    elif data == "classes_info":
        # Информация
        await query.answer("Используйте кнопки для навигации")
    
    elif data == "classes_back_simple":
        # Возврат к списку
        text, markup = build_classes_simple_page()  # Без параметров
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)


async def class_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик подробной информации о классе"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
	
    # Формат: cls_{short_id}_{section}_{page}
    if not data.startswith("cls_"):
        await query.edit_message_text("❌ Ошибка: неверный формат запроса")
        return
    
    parts = data.replace("cls_", "").split("_")
    
    if len(parts) < 3:
        await query.edit_message_text("❌ Ошибка: неполный запрос")
        return
    
    short_id = parts[0]
    section_code = parts[1]
    try:
        page = int(parts[2])
    except ValueError:
        page = 1
    
    # Расшифровываем код секции
    section_map = {
        "m": "main",
        "a": "abilities", 
        "r": "archetypes",
        "q": "quick_start"
    }
    section = section_map.get(section_code, "main")
    
    # Получаем полный ключ класса
    class_key = _get_class_key_from_id(short_id)
    if not class_key:
        await query.edit_message_text("❌ Класс не найден")
        return
    
    # Используем вашу существующую функцию format_class_detail
    try:
        text, markup = format_class_detail(class_key, section=section, page=page)
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
    except Exception as e:
        print(f"❌ Ошибка при форматировании класса: {e}")
        await query.edit_message_text("❌ Произошла ошибка при загрузке информации о классе")


async def class_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик для возврата к списку классов"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "info":
        await query.answer("Информация о текущей странице")
        return
    
    # Просто возвращаем к списку классов (без параметров)
    text, markup = build_classes_simple_page()
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)


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
    
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        handle_reply_keyboard
    ))
    
    # Обработчики для кнопок "Далее" в правилах
    app.add_handler(CallbackQueryHandler(handle_inline_button, pattern="^rules_"))
    app.add_handler(CallbackQueryHandler(handle_inline_button, pattern="^dice_"))
    app.add_handler(CallbackQueryHandler(handle_inline_button, pattern="^combat_"))
    app.add_handler(CallbackQueryHandler(handle_inline_button, pattern="^stats_"))
    app.add_handler(CallbackQueryHandler(handle_inline_button, pattern="^glossary_"))
    
    # Обработчики для пагинации рас
    app.add_handler(CallbackQueryHandler(race_page_callback, pattern="^race_page_"))
    app.add_handler(CallbackQueryHandler(race_page_callback, pattern="^race_detail_page_"))
    
    # Обработчики для классов
    app.add_handler(CallbackQueryHandler(class_callback, pattern="^cls_"))
    app.add_handler(CallbackQueryHandler(class_page_callback, pattern="^class_page_"))
    
    # Обработчики для заклинаний
    app.add_handler(CallbackQueryHandler(spell_level_callback, pattern="^spell_level_"))
    app.add_handler(CallbackQueryHandler(spell_page_callback, pattern="^spell_page_"))
    app.add_handler(CallbackQueryHandler(spell_detail_callback, pattern="^spell_detail_"))
    app.add_handler(CallbackQueryHandler(spell_level_select_callback, pattern="^spell_level_select$"))
    
    # Обработчики для рас
    app.add_handler(CallbackQueryHandler(race_callback, pattern="^race_detail_"))
    
    print("🎲 D&D Helper Bot is starting... Press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
	main()
