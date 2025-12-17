"""
Скрипт для парсинга классов D&D через gpt-oss:120b
Преобразует сырые данные классов в структурированный JSON
"""

import json
import requests
import os
from pathlib import Path
from typing import Optional

# Настройки
OLLAMA_URL = "http://localhost:11434"
MODEL = "gpt-oss:120b-cloud"

# Папки
CLASSES_DIR = Path(__file__).parent / "classes"
OUTPUT_DIR = Path(__file__).parent / "classes_structured"

# Шаблон для выходных данных
TEMPLATE_EXAMPLE = """
{
  "id": "fighter",
  "name": "Воин",
  "name_en": "Fighter",
  "hit_dice": "1d10",
  "primary_abilities": ["str", "dex"],
  "saving_throws": ["str", "con"],
  "armor_proficiencies": ["light", "medium", "heavy", "shields"],
  "weapon_proficiencies": ["simple", "martial"],
  "tool_proficiencies": [],
  "skill_choices": {
    "count": 2,
    "from": ["acrobatics", "athletics", "perception", "survival", "intimidation", "history", "insight", "animal_handling"]
  },
  "starting_gold": "5d4x10",
  "features": {
    "1": [
      {
        "id": "fighting_style",
        "name": "Боевой стиль",
        "name_en": "Fighting Style",
        "description": "Полное описание способности...",
        "choices": [
          {"id": "archery", "name": "Стрельба", "description": "..."}
        ]
      },
      {
        "id": "second_wind",
        "name": "Второе дыхание",
        "name_en": "Second Wind",
        "description": "...",
        "usage": {"type": "short_rest", "uses": 1}
      }
    ],
    "2": [...],
    "3": [
      {
        "id": "subclass_choice",
        "name": "Название выбора архетипа",
        "name_en": "...",
        "description": "...",
        "subclass_feature": true,
        "subclass_levels": [3, 7, 10, 15, 18]
      }
    ]
  }
}
"""

# Маппинг навыков на английские ID
SKILL_MAP = {
    "акробатика": "acrobatics",
    "атлетика": "athletics",
    "анализ": "investigation",
    "восприятие": "perception",
    "выживание": "survival",
    "выступление": "performance",
    "запугивание": "intimidation",
    "история": "history",
    "ловкость рук": "sleight_of_hand",
    "магия": "arcana",
    "медицина": "medicine",
    "обман": "deception",
    "природа": "nature",
    "проницательность": "insight",
    "религия": "religion",
    "скрытность": "stealth",
    "убеждение": "persuasion",
    "уход за животными": "animal_handling"
}

# Маппинг классов на английские ID
CLASS_MAP = {
    "Варвар": ("barbarian", "Barbarian"),
    "Бард": ("bard", "Bard"),
    "Воин": ("fighter", "Fighter"),
    "Волшебник": ("wizard", "Wizard"),
    "Друид": ("druid", "Druid"),
    "Жрец": ("cleric", "Cleric"),
    "Изобретатель": ("artificer", "Artificer"),
    "Колдун": ("warlock", "Warlock"),
    "Монах": ("monk", "Monk"),
    "Паладин": ("paladin", "Paladin"),
    "Плут": ("rogue", "Rogue"),
    "Следопыт": ("ranger", "Ranger"),
    "Чародей": ("sorcerer", "Sorcerer")
}


def call_llm(prompt: str) -> Optional[str]:
    """Вызов LLM через Ollama API"""
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 8000
                }
            },
            timeout=300
        )
        
        if response.status_code == 200:
            return response.json().get("response", "")
        else:
            print(f"❌ Ошибка API: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")
        return None


def extract_json_from_response(response: str) -> Optional[dict]:
    """Извлечение JSON из ответа LLM"""
    # Ищем JSON в ответе
    try:
        # Пробуем найти JSON блок
        start = response.find('{')
        end = response.rfind('}') + 1
        
        if start != -1 and end > start:
            json_str = response[start:end]
            return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка парсинга JSON: {e}")
    
    return None


def parse_class(class_name: str, raw_data: dict) -> Optional[dict]:
    """Парсинг одного класса"""
    
    class_id, class_en = CLASS_MAP.get(class_name, (class_name.lower(), class_name))
    
    prompt = f"""Преобразуй данные класса D&D 5e в структурированный JSON.

ВХОДНЫЕ ДАННЫЕ КЛАССА "{class_name}":
```json
{json.dumps(raw_data, ensure_ascii=False, indent=2)[:6000]}
```

ТРЕБОВАНИЯ К ВЫХОДНОМУ JSON:
1. Базовая информация класса (hit_dice, saving_throws, proficiencies, skill_choices)
2. Способности по уровням (features) - от 1 до 20 уровня
3. НЕ включай архетипы/подклассы - только пометь на каком уровне выбор архетипа (subclass_feature: true)
4. Для каждой способности: id (английский snake_case), name (русский), name_en (английский), description (полное описание)
5. Если способность имеет выборы (например боевой стиль) - добавь массив choices
6. Если способность имеет ограниченное использование - добавь usage (type: "short_rest" или "long_rest", uses: число)
7. Если способность улучшается на высоких уровнях - добавь upgrades с указанием уровня и изменений

ПРИМЕР СТРУКТУРЫ:
{TEMPLATE_EXAMPLE}

ВАЖНО:
- Используй id класса: "{class_id}"
- Используй name_en: "{class_en}"
- Навыки в skill_choices.from должны быть на английском: {json.dumps(list(SKILL_MAP.values()))}
- Верни ТОЛЬКО валидный JSON без комментариев и пояснений
- Описания способностей должны быть полными, не сокращай их

JSON:"""

    print(f"📤 Отправляю запрос для класса {class_name}...")
    response = call_llm(prompt)
    
    if not response:
        return None
    
    print(f"📥 Получен ответ, парсинг JSON...")
    return extract_json_from_response(response)


def process_all_classes():
    """Обработка всех классов"""
    
    # Создаём папку для выходных данных
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Получаем список файлов классов
    class_files = list(CLASSES_DIR.glob("*—Классы.json"))
    
    # Исключаем общий файл Классы.json
    class_files = [f for f in class_files if f.name != "Классы.json"]
    
    print(f"📂 Найдено {len(class_files)} файлов классов")
    
    results = {"success": [], "failed": []}
    
    for class_file in class_files:
        # Извлекаем имя класса
        class_name = class_file.stem.split("—")[0]
        
        # Пропускаем если уже обработан
        output_file = OUTPUT_DIR / f"{CLASS_MAP.get(class_name, (class_name.lower(),))[0]}.json"
        if output_file.exists():
            print(f"⏭️  {class_name} уже обработан, пропускаю")
            continue
        
        print(f"\n{'='*50}")
        print(f"🔄 Обрабатываю: {class_name}")
        print(f"{'='*50}")
        
        # Загружаем сырые данные
        try:
            with open(class_file, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        except Exception as e:
            print(f"❌ Ошибка загрузки {class_file}: {e}")
            results["failed"].append(class_name)
            continue
        
        # Парсим через LLM
        parsed = parse_class(class_name, raw_data)
        
        if parsed:
            # Сохраняем результат
            try:
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(parsed, f, ensure_ascii=False, indent=2)
                print(f"✅ Сохранено: {output_file.name}")
                results["success"].append(class_name)
            except Exception as e:
                print(f"❌ Ошибка сохранения: {e}")
                results["failed"].append(class_name)
        else:
            print(f"❌ Не удалось распарсить {class_name}")
            results["failed"].append(class_name)
    
    # Итоги
    print(f"\n{'='*50}")
    print("📊 ИТОГИ:")
    print(f"✅ Успешно: {len(results['success'])} - {', '.join(results['success'])}")
    print(f"❌ Ошибки: {len(results['failed'])} - {', '.join(results['failed'])}")


def process_single_class(class_name: str):
    """Обработка одного конкретного класса"""
    
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Находим файл
    class_file = CLASSES_DIR / f"{class_name}—Классы.json"
    
    if not class_file.exists():
        print(f"❌ Файл не найден: {class_file}")
        return
    
    print(f"🔄 Обрабатываю: {class_name}")
    
    with open(class_file, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    
    parsed = parse_class(class_name, raw_data)
    
    if parsed:
        class_id = CLASS_MAP.get(class_name, (class_name.lower(),))[0]
        output_file = OUTPUT_DIR / f"{class_id}.json"
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(parsed, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Сохранено: {output_file}")
    else:
        print(f"❌ Не удалось распарсить")


# Уровни ASI для каждого класса
ASI_LEVELS = {
    "default": [4, 8, 12, 16, 19],
    "fighter": [4, 6, 8, 12, 14, 16, 19],
    "rogue": [4, 8, 10, 12, 16, 19]
}

# Уровни архетипов для каждого класса
SUBCLASS_LEVELS = {
    "barbarian": [3, 6, 10, 14],
    "bard": [3, 6, 14],
    "cleric": [1, 2, 6, 8, 17],
    "druid": [2, 6, 10, 14],
    "fighter": [3, 7, 10, 15, 18],
    "monk": [3, 6, 11, 17],
    "paladin": [3, 7, 15, 20],
    "ranger": [3, 7, 11, 15],
    "rogue": [3, 9, 13, 17],
    "sorcerer": [1, 6, 14, 18],
    "warlock": [1, 6, 10, 14],
    "wizard": [2, 6, 10, 14],
    "artificer": [3, 5, 9, 15]
}


def validate_class(class_id: str, data: dict) -> dict:
    """Валидация распарсенного класса"""
    issues = []
    warnings = []
    
    # 1. Проверка базовых полей
    required_fields = ["id", "name", "name_en", "hit_dice", "saving_throws", 
                       "armor_proficiencies", "weapon_proficiencies", "skill_choices", "features"]
    
    for field in required_fields:
        if field not in data:
            issues.append(f"Отсутствует обязательное поле: {field}")
    
    if "features" not in data:
        return {"issues": issues, "warnings": warnings, "valid": False}
    
    features = data["features"]
    
    # 2. Проверка уровней ASI
    asi_levels = ASI_LEVELS.get(class_id, ASI_LEVELS["default"])
    for level in asi_levels:
        level_str = str(level)
        if level_str not in features:
            issues.append(f"Пропущен уровень {level} (должен быть ASI)")
        else:
            has_asi = any("ability_score" in f.get("id", "").lower() or 
                         "asi" in f.get("id", "").lower() or
                         "увеличение характеристик" in f.get("name", "").lower()
                         for f in features[level_str])
            if not has_asi:
                warnings.append(f"На уровне {level} нет ASI (Увеличение характеристик)")
    
    # 3. Проверка subclass_feature
    subclass_levels = SUBCLASS_LEVELS.get(class_id, [3])
    first_subclass_level = subclass_levels[0]
    level_str = str(first_subclass_level)
    
    if level_str in features:
        has_subclass = any(f.get("subclass_feature", False) for f in features[level_str])
        if not has_subclass:
            warnings.append(f"На уровне {first_subclass_level} нет пометки subclass_feature")
    else:
        issues.append(f"Пропущен уровень {first_subclass_level} (выбор архетипа)")
    
    # 4. Проверка пустых/коротких описаний
    for level, feats in features.items():
        for feat in feats:
            desc = feat.get("description", "")
            name = feat.get("name", "неизвестно")
            
            if not desc:
                issues.append(f"Пустое описание: {name} (ур. {level})")
            elif len(desc) < 20:
                warnings.append(f"Слишком короткое описание: {name} (ур. {level})")
            
            # Проверка странных символов
            if "∞" in name or "∞" in desc:
                warnings.append(f"Странные символы в: {name} (ур. {level})")
    
    # 5. Проверка hit_dice
    if "hit_dice" in data:
        hd = data["hit_dice"]
        valid_dice = ["1d6", "1d8", "1d10", "1d12"]
        if hd not in valid_dice:
            warnings.append(f"Необычная кость хитов: {hd}")
    
    # 6. Проверка saving_throws
    if "saving_throws" in data:
        saves = data["saving_throws"]
        valid_saves = ["str", "dex", "con", "int", "wis", "cha"]
        for s in saves:
            if s not in valid_saves:
                issues.append(f"Некорректный спасбросок: {s}")
        if len(saves) != 2:
            warnings.append(f"Количество спасбросков не равно 2: {len(saves)}")
    
    # 7. Проверка skill_choices
    if "skill_choices" in data:
        sc = data["skill_choices"]
        if "count" not in sc:
            issues.append("Нет количества навыков (skill_choices.count)")
        if "from" not in sc or not sc["from"]:
            issues.append("Нет списка навыков (skill_choices.from)")
    
    return {
        "issues": issues,
        "warnings": warnings,
        "valid": len(issues) == 0
    }


def validate_all_classes():
    """Валидация всех распарсенных классов"""
    
    report = {}
    
    class_files = list(OUTPUT_DIR.glob("*.json"))
    
    print(f"📋 Валидация {len(class_files)} классов...\n")
    
    total_issues = 0
    total_warnings = 0
    
    for class_file in class_files:
        class_id = class_file.stem
        
        try:
            with open(class_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            report[class_id] = {"issues": [f"Ошибка чтения файла: {e}"], "warnings": [], "valid": False}
            continue
        
        result = validate_class(class_id, data)
        report[class_id] = result
        
        # Вывод результатов
        status = "✅" if result["valid"] else "❌"
        print(f"{status} {class_id}.json")
        
        for issue in result["issues"]:
            print(f"   ❌ {issue}")
            total_issues += 1
        
        for warning in result["warnings"]:
            print(f"   ⚠️  {warning}")
            total_warnings += 1
        
        print()
    
    # Сохраняем отчёт
    report_file = OUTPUT_DIR / "validation_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"{'='*50}")
    print(f"📊 ИТОГО:")
    print(f"   ❌ Критических проблем: {total_issues}")
    print(f"   ⚠️  Предупреждений: {total_warnings}")
    print(f"📄 Отчёт сохранён: {report_file}")
    
    return report


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--validate":
            # Валидация всех классов
            validate_all_classes()
        else:
            # Обработка конкретного класса
            class_name = sys.argv[1]
            process_single_class(class_name)
    else:
        # Обработка всех классов
        process_all_classes()
