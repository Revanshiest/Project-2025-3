"""
Парсер предысторий D&D 5e
Преобразует сырые данные из scraped JSON в унифицированный формат
для интерактивного создания персонажа
"""

import json
import os
import subprocess
import re
from typing import Optional, List, Dict, Any

# Конфигурация Ollama
OLLAMA_MODEL = "gpt-oss:120b-cloud"

# Пути к файлам
INPUT_DIR = "../sub/parsed_backgrounds"
OUTPUT_DIR = "parsed_backgrounds"

# Словари для маппинга
SKILLS_RU_TO_ID = {
    "акробатика": "acrobatics",
    "уход за животными": "animal_handling",
    "магия": "arcana",
    "атлетика": "athletics",
    "обман": "deception",
    "история": "history",
    "проницательность": "insight",
    "запугивание": "intimidation",
    "расследование": "investigation",
    "медицина": "medicine",
    "природа": "nature",
    "восприятие": "perception",
    "выступление": "performance",
    "убеждение": "persuasion",
    "религия": "religion",
    "ловкость рук": "sleight_of_hand",
    "скрытность": "stealth",
    "выживание": "survival"
}

SKILLS_ID_TO_RU = {v: k.capitalize() for k, v in SKILLS_RU_TO_ID.items()}

ALIGNMENT_MAP = {
    "добрый": "good",
    "злой": "evil",
    "законный": "lawful",
    "хаотичный": "chaotic",
    "нейтральный": "neutral",
    "любой": "any"
}

PROMPT_TEMPLATE = '''Ты — парсер данных D&D 5e. Преобразуй сырые данные предыстории в структурированный JSON.

ВХОДНЫЕ ДАННЫЕ:
{raw_data}

ТРЕБУЕМЫЙ ФОРМАТ JSON (верни ТОЛЬКО JSON без markdown):
{{
  "id": "<snake_case_id на английском>",
  "name": "<название на русском>",
  "name_en": "<English name>",
  "source": "PHB",
  "description": "<основное описание предыстории>",
  
  "skill_proficiencies": {{
    "fixed": ["<skill_id>"],
    "choice": {{"count": 0, "from": []}}
  }},
  
  "tool_proficiencies": {{
    "fixed": [{{"id": "<tool_id>", "name": "<название>"}}],
    "choice": {{"count": 0, "type": null, "description": null}}
  }},
  
  "languages": {{
    "fixed": [],
    "choice_count": 0
  }},
  
  "equipment": {{
    "items": [{{"id": "<item_id>", "name": "<название>", "quantity": 1, "choice": false}}],
    "gold": 0
  }},
  
  "feature": {{
    "id": "<feature_id>",
    "name": "<название умения>",
    "name_en": "<English name>",
    "description": "<описание>"
  }},
  
  "specialty": null,
  
  "personality": {{
    "traits": {{"name": "Черта характера", "dice": "d8", "select_count": 2, "options": [{{"roll": 1, "text": "<текст>"}}]}},
    "ideals": {{"name": "Идеал", "dice": "d6", "select_count": 1, "options": [{{"roll": 1, "text": "<текст>", "alignment": "any"}}]}},
    "bonds": {{"name": "Привязанность", "dice": "d6", "select_count": 1, "options": [{{"roll": 1, "text": "<текст>"}}]}},
    "flaws": {{"name": "Слабость", "dice": "d6", "select_count": 1, "options": [{{"roll": 1, "text": "<текст>"}}]}}
  }},
  
  "variants": []
}}

ПРАВИЛА:
1. skill_id: acrobatics, animal_handling, arcana, athletics, deception, history, insight, intimidation, investigation, medicine, nature, perception, performance, persuasion, religion, sleight_of_hand, stealth, survival
2. alignment: good, evil, lawful, chaotic, neutral, any
3. Извлеки золото из текста снаряжения (например "15 зм" -> 15)
4. Распарси таблицы personality из tables
5. Верни ТОЛЬКО валидный JSON'''


def load_raw_backgrounds() -> List[Dict]:
    """Загружает сырые данные предысторий."""
    all_file = os.path.join(INPUT_DIR, "all_backgrounds.json")
    
    if os.path.exists(all_file):
        with open(all_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return list(data.values())
    
    # Если нет общего файла, собираем из отдельных
    backgrounds = []
    for filename in os.listdir(INPUT_DIR):
        if filename.endswith('.json') and filename != 'all_backgrounds.json':
            filepath = os.path.join(INPUT_DIR, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                backgrounds.append(json.load(f))
    
    return backgrounds


def check_ollama_connection() -> bool:
    """Проверяет подключение к Ollama."""
    print(f"🔍 Проверка Ollama и модели '{OLLAMA_MODEL}'...")
    
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            print(f"❌ Ошибка при запуске ollama: {result.stderr}")
            return False
        
        models = result.stdout.strip().split('\n')[1:]
        model_names = [line.split()[0] for line in models if line.strip()]
        
        print(f"✅ Ollama работает. Доступные модели: {len(model_names)}")
        
        if not any(OLLAMA_MODEL in name for name in model_names):
            print(f"⚠️ Модель '{OLLAMA_MODEL}' не найдена!")
            return False
        
        print(f"✅ Модель '{OLLAMA_MODEL}' доступна")
        return True
        
    except FileNotFoundError:
        print("❌ Ollama не установлена или не в PATH")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def call_ollama(prompt: str) -> Optional[str]:
    """Отправляет запрос к Ollama."""
    try:
        print("   📤 Отправка запроса в Ollama...")
        
        result = subprocess.run(
            ["ollama", "run", OLLAMA_MODEL, prompt],
            capture_output=True,
            text=True,
            timeout=600,
            encoding='utf-8'
        )
        
        if result.returncode != 0:
            print(f"❌ Ошибка Ollama: {result.stderr}")
            return None
        
        response = result.stdout.strip()
        print(f"   📥 Получен ответ ({len(response)} символов)")
        return response
            
    except subprocess.TimeoutExpired:
        print("❌ Таймаут запроса")
        return None
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None


def extract_json_from_response(response: str) -> Optional[dict]:
    """Извлекает JSON из ответа модели."""
    if not response:
        return None
    
    # Убираем markdown-блоки
    if "```" in response:
        parts = response.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                response = part
                break
    
    # Ищем JSON
    try:
        start_idx = response.find("{")
        end_idx = response.rfind("}") + 1
        if start_idx != -1 and end_idx > start_idx:
            json_str = response[start_idx:end_idx]
            return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"   ⚠️ Ошибка парсинга JSON: {e}")
        print(f"   Ответ: {response[:300]}...")
    
    return None


def parse_skills_from_text(text: str) -> Dict[str, Any]:
    """Парсит навыки из текста."""
    result = {"fixed": [], "choice": {"count": 0, "from": []}}
    
    if not text:
        return result
    
    text_lower = text.lower()
    
    for skill_ru, skill_id in SKILLS_RU_TO_ID.items():
        if skill_ru in text_lower:
            result["fixed"].append(skill_id)
    
    # Проверяем на выбор
    if "на ваш выбор" in text_lower or "любые" in text_lower:
        match = re.search(r'(\d+)\s*(навык|любых)', text_lower)
        if match:
            result["choice"]["count"] = int(match.group(1))
    
    return result


def parse_languages_from_text(text: str) -> Dict[str, Any]:
    """Парсит языки из текста."""
    result = {"fixed": [], "choice_count": 0}
    
    if not text:
        return result
    
    text_lower = text.lower()
    
    # Ищем количество языков на выбор
    if "два на ваш выбор" in text_lower or "два языка" in text_lower:
        result["choice_count"] = 2
    elif "один на ваш выбор" in text_lower or "один язык" in text_lower:
        result["choice_count"] = 1
    elif match := re.search(r'(\d+)\s*язык', text_lower):
        result["choice_count"] = int(match.group(1))
    
    return result


def parse_gold_from_text(text: str) -> int:
    """Извлекает золото из текста снаряжения."""
    if not text:
        return 0
    
    match = re.search(r'(\d+)\s*зм', text.lower())
    if match:
        return int(match.group(1))
    return 0


def parse_tables_to_personality(tables: List[Dict]) -> Dict[str, Any]:
    """Преобразует таблицы в структуру personality."""
    result = {
        "traits": {"name": "Черта характера", "dice": "d8", "select_count": 2, "options": []},
        "ideals": {"name": "Идеал", "dice": "d6", "select_count": 1, "options": []},
        "bonds": {"name": "Привязанность", "dice": "d6", "select_count": 1, "options": []},
        "flaws": {"name": "Слабость", "dice": "d6", "select_count": 1, "options": []}
    }
    
    for table in tables:
        rows = table.get("rows", [])
        if not rows:
            continue
        
        # Определяем тип таблицы по первой строке
        first_row = rows[0] if rows else []
        if len(first_row) < 2:
            continue
        
        table_type = first_row[1].lower() if len(first_row) > 1 else ""
        
        target_key = None
        if "черта характера" in table_type:
            target_key = "traits"
        elif "идеал" in table_type:
            target_key = "ideals"
        elif "привязанность" in table_type:
            target_key = "bonds"
        elif "слабость" in table_type:
            target_key = "flaws"
        
        if target_key:
            # Парсим строки таблицы (пропускаем заголовок)
            for row in rows[1:]:
                if len(row) >= 2:
                    try:
                        roll = int(row[0])
                        text = row[1]
                        
                        option = {"roll": roll, "text": text}
                        
                        # Для идеалов извлекаем мировоззрение
                        if target_key == "ideals":
                            alignment = "any"
                            for align_ru, align_en in ALIGNMENT_MAP.items():
                                if align_ru in text.lower():
                                    alignment = align_en
                                    break
                            option["alignment"] = alignment
                        
                        result[target_key]["options"].append(option)
                    except (ValueError, IndexError):
                        continue
    
    return result


def parse_specialty_table(tables: List[Dict]) -> Optional[Dict]:
    """Ищет и парсит таблицу специализации."""
    specialty_keywords = ["амплуа", "специализация", "преступная деятельность", "гильдейский бизнес"]
    
    for table in tables:
        rows = table.get("rows", [])
        if not rows or len(rows) < 2:
            continue
        
        first_row = rows[0]
        if len(first_row) < 2:
            continue
        
        table_name = first_row[1].lower()
        
        # Проверяем что это не personality таблица
        if any(kw in table_name for kw in ["черта", "идеал", "привязанность", "слабость"]):
            continue
        
        # Проверяем что это specialty
        is_specialty = any(kw in table_name for kw in specialty_keywords)
        
        # Или если таблица начинается с к10/к8/к6 и не personality
        dice_match = re.match(r'к(\d+)', first_row[0].lower())
        if dice_match and not any(kw in table_name for kw in ["черта", "идеал", "привязанность", "слабость"]):
            is_specialty = True
        
        if is_specialty:
            dice = f"d{dice_match.group(1)}" if dice_match else "d8"
            options = []
            
            for row in rows[1:]:
                if len(row) >= 2:
                    try:
                        roll = int(row[0])
                        options.append({"roll": roll, "name": row[1]})
                    except ValueError:
                        continue
            
            if options:
                return {
                    "name": first_row[1],
                    "name_en": "",
                    "description": "",
                    "dice": dice,
                    "select_count": {"min": 1, "max": 1},
                    "options": options
                }
    
    return None


def extract_english_name(title: str, url: str) -> str:
    """Извлекает английское название из URL или title."""
    # Из URL: 757-entertainer -> Entertainer
    if url:
        match = re.search(r'\d+-([a-z-]+)', url.lower())
        if match:
            name = match.group(1).replace('-', ' ').title()
            return name
    
    # Из title: [Entertainer]
    if '[' in title and ']' in title:
        start = title.index('[') + 1
        end = title.index(']')
        return title[start:end]
    
    return ""


def extract_id(title: str, url: str) -> str:
    """Генерирует ID из URL или названия."""
    if url:
        match = re.search(r'\d+-([a-z-]+)', url.lower())
        if match:
            return match.group(1).replace('-', '_')
    
    # Из русского названия (транслитерация)
    name = title.split('—')[0].strip().lower()
    translit = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya', ' ': '_'
    }
    result = ''.join(translit.get(c, c) for c in name)
    return result


def parse_background_locally(raw_data: Dict) -> Dict:
    """Локальный парсинг без AI."""
    title = raw_data.get("title", "")
    url = raw_data.get("url", "")
    name_ru = raw_data.get("name_ru", title.split('—')[0].strip())
    
    # Базовая структура
    result = {
        "id": extract_id(title, url),
        "name": name_ru,
        "name_en": extract_english_name(title, url),
        "source": "PHB",
        "description": raw_data.get("main_description", ""),
        
        "skill_proficiencies": parse_skills_from_text(raw_data.get("skill_proficiencies", "")),
        
        "tool_proficiencies": {
            "fixed": [],
            "choice": {"count": 0, "type": None, "description": None}
        },
        
        "languages": parse_languages_from_text(raw_data.get("languages", "")),
        
        "equipment": {
            "items": [],
            "gold": parse_gold_from_text(raw_data.get("equipment", ""))
        },
        
        "feature": {
            "id": "",
            "name": raw_data.get("feature_name", "").replace("УМЕНИЕ: ", ""),
            "name_en": "",
            "description": raw_data.get("feature_description", "")
        },
        
        "specialty": parse_specialty_table(raw_data.get("tables", [])),
        
        "personality": parse_tables_to_personality(raw_data.get("tables", [])),
        
        "variants": []
    }
    
    # Генерируем ID для feature
    if result["feature"]["name"]:
        result["feature"]["id"] = result["feature"]["name"].lower().replace(" ", "_")
    
    return result


def parse_background_with_ai(raw_data: Dict) -> Optional[Dict]:
    """Парсинг с использованием AI."""
    prompt = PROMPT_TEMPLATE.format(raw_data=json.dumps(raw_data, ensure_ascii=False, indent=2))
    
    response = call_ollama(prompt)
    result = extract_json_from_response(response)
    
    if result:
        return result
    
    print("   ⚠️ AI не смог распарсить, использую локальный парсинг")
    return parse_background_locally(raw_data)


def process_all_backgrounds(use_ai: bool = False):
    """Обрабатывает все предыстории."""
    print("📂 Загрузка сырых данных...")
    raw_backgrounds = load_raw_backgrounds()
    print(f"   Найдено: {len(raw_backgrounds)} предысторий")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    results = []
    failed = []
    
    for i, raw_data in enumerate(raw_backgrounds, 1):
        name = raw_data.get("name_ru", raw_data.get("title", f"Background {i}"))
        print(f"\n🔄 [{i}/{len(raw_backgrounds)}] Обработка: {name}")
        
        if use_ai:
            parsed = parse_background_with_ai(raw_data)
        else:
            parsed = parse_background_locally(raw_data)
        
        if parsed:
            results.append(parsed)
            
            # Сохраняем отдельный файл
            output_file = os.path.join(OUTPUT_DIR, f"{parsed['id']}.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(parsed, f, ensure_ascii=False, indent=2)
            print(f"   ✅ Сохранено: {output_file}")
        else:
            failed.append(name)
            print(f"   ❌ Ошибка обработки")
    
    # Сохраняем общий файл
    all_output = os.path.join(OUTPUT_DIR, "all_backgrounds_formatted.json")
    with open(all_output, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*50}")
    print(f"✅ Успешно обработано: {len(results)} предысторий")
    print(f"💾 Общий файл: {all_output}")
    
    if failed:
        print(f"❌ Ошибки: {len(failed)}")
        for name in failed:
            print(f"   - {name}")
    
    return results


def process_single_background(index: int = 0, use_ai: bool = False) -> Optional[Dict]:
    """Обрабатывает одну предысторию по индексу."""
    raw_backgrounds = load_raw_backgrounds()
    
    if index >= len(raw_backgrounds):
        print(f"❌ Индекс {index} вне диапазона (всего {len(raw_backgrounds)})")
        return None
    
    raw_data = raw_backgrounds[index]
    name = raw_data.get("name_ru", raw_data.get("title", "Unknown"))
    print(f"🔄 Обработка: {name}")
    
    if use_ai:
        return parse_background_with_ai(raw_data)
    else:
        return parse_background_locally(raw_data)


if __name__ == "__main__":
    # Режим работы
    USE_AI = False  # True для использования Ollama
    MODE = "all"    # "all" или номер индекса (0-13)
    
    if USE_AI:
        if not check_ollama_connection():
            print("\n⚠️ Переключаюсь на локальный парсинг...")
            USE_AI = False
    
    if MODE == "all":
        results = process_all_backgrounds(use_ai=USE_AI)
    else:
        try:
            index = int(MODE)
            result = process_single_background(index, use_ai=USE_AI)
            if result:
                print("\n📋 Результат:")
                print(json.dumps(result, ensure_ascii=False, indent=2))
                
                # Сохраняем
                os.makedirs(OUTPUT_DIR, exist_ok=True)
                output_file = os.path.join(OUTPUT_DIR, f"{result['id']}.json")
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"\n💾 Сохранено: {output_file}")
        except ValueError:
            print(f"❌ Неверный режим: {MODE}")
            print("   Используйте 'all' или число (индекс предыстории)")