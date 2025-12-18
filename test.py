"""
Тестовый скрипт для проверки основного функционала проекта Project-2025-3.
Проверяет загрузку данных, работу основных функций и отсутствие критических ошибок.
"""
import sys
import traceback

# Импортируем основные модули
try:
    from src import character_data, character_creator, character_creation, level_up, ollama, texts
    import main
    print("✅ Импорт всех модулей прошёл успешно.")

    # Проверка справочных текстов
    text_attrs = [
        "START_TEXT", "HELP_TEXT", "RULES_TEXT", "DICE_RULES_TEXT",
        "COMBAT_RULES_TEXT_PART1", "COMBAT_RULES_TEXT_PART2", "COMBAT_RULES_TEXT_PART3", "COMBAT_RULES_TEXT_PART4",
        "STATS_TEXT_PART1", "STATS_TEXT_PART2", "GLOSSARY_TEXT_PART1", "GLOSSARY_TEXT_PART2", "RACES_SHORT_DESCRIPTIONS"
    ]
    for attr in text_attrs:
        if not hasattr(texts, attr):
            print(f"❌ В модуле texts отсутствует: {attr}")
        else:
            val = getattr(texts, attr)
            if not val:
                print(f"⚠️  {attr} пустой!")
            else:
                print(f"✅ {attr} загружен ({'dict' if isinstance(val, dict) else 'str'})")
except Exception as e:
    print("❌ Ошибка импорта модулей:", e)
    traceback.print_exc()
    sys.exit(1)

# Проверка загрузки данных
try:
    races = character_data.load_races()
    classes = character_data.load_classes_structured()
    backgrounds = character_data.load_backgrounds()
    skills = character_data.load_skills()
    items = character_data.load_items()
    spells = character_data.load_spells_by_level("1")
    print(f"✅ Данные загружены: расы={len(races)}, классы={len(classes)}, предыстории={len(backgrounds)}, навыки={len(skills)}, предметы={len(items)}, заклинания={len(spells)}")
except Exception as e:
    print("❌ Ошибка загрузки данных:", e)
    traceback.print_exc()

# Проверка создания персонажа (минимальный тест)
try:
    from src.character_creator import Character
    test_char = Character(
        id="test_id",
        name="Тестовый Герой",
        race_key="человек",
        race_name="Человек",
        class_id="fighter",
        class_name="Воин",
        background_id="acolyte",
        background_name="Аколит",
        level=1,
        experience=0,
        proficiency_bonus=2,
        strength=15,
        dexterity=14,
        constitution=13,
        intelligence=12,
        wisdom=10,
        charisma=8,
        skills=[],
        equipment=[],
        spells=None,
        features=[],
        max_hp=10,
        current_hp=10,
        hit_dice_remaining=1,
        archetype_name=""
    )
    print("✅ Персонаж создан успешно:", test_char)
except Exception as e:
    print("❌ Ошибка создания персонажа:", e)
    traceback.print_exc()

# Проверка работы OllamaClient (инициализация)
try:
    client = ollama.OllamaClient()
    print("✅ OllamaClient инициализирован.")
except Exception as e:
    print("⚠️  OllamaClient: ошибка инициализации (это нормально, если Ollama не запущен):", e)

print("\nВсе базовые проверки завершены. Для полного теста используйте юнит-тесты и ручное тестирование Telegram-бота.")
