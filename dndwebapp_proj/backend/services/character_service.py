import logging
import random
import re
from typing import Dict, List

from backend.models.character import Character

logger = logging.getLogger(__name__)


class CharacterService:
    """
    Сервис для создания и управления персонажами D&D.
    Содержит бизнес-логику создания, бросков характеристик и сохранения.
    """

    # Маппинг русских названий характеристик → поля модели
    ABILITY_NAME_MAP = {
        "Сил": "strength",
        "Ловкост": "dexterity",
        "Телосложени": "constitution",
        "Интеллект": "intelligence",
        "Мудрост": "wisdom",
        "Харизм": "charisma",
    }

    def __init__(self):
        # Сервис теперь полностью Stateless (без состояния)
        pass

    # ========== МЕТОДЫ ГЕНЕРАЦИИ ХАРАКТЕРИСТИК ==========

    def roll_abilities(self) -> List[int]:
        """Бросить 4d6, отбросить наименьший для каждой характеристики"""
        scores = []
        for _ in range(6):
            rolls = sorted([random.randint(1, 6) for _ in range(4)], reverse=True)
            score = sum(rolls[:3])
            scores.append(score)
        return sorted(scores, reverse=True)

    def get_standard_array(self) -> List[int]:
        return [15, 14, 13, 12, 10, 8]

    def get_point_buy_cost(self, score: int) -> int:
        costs = {8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9}
        return costs.get(score, 0)

    def validate_point_buy(self, scores: Dict[str, int], total_points: int = 27) -> bool:
        total_cost = sum(self.get_point_buy_cost(s) for s in scores.values())
        return total_cost <= total_points and all(8 <= s <= 15 for s in scores.values())

    # ========== ПРИМЕНЕНИЕ БОНУСОВ И КЛАССОВ ==========

    def _parse_ability_bonus(self, text: str, ability_ru_name: str) -> int:
        """
        Извлекает числовой бонус для конкретной характеристики из текста.
        Ищет паттерн вида '<характеристика> увеличивается на <число>'
        рядом с упоминанием конкретной характеристики.
        
        Примеры текстов:
          'Сила увеличивается на 2, Телосложение увеличивается на 1'
          'значение Харизмы увеличивается на 2'
        """
        # Ищем конкретный бонус рядом с именем характеристики
        pattern = rf'{ability_ru_name}\w*\s+увеличивается\s+на\s+(\d+)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return 0

    def apply_racial_bonuses(self, character: Character, race_data: Dict):
        ability_increase = race_data.get("Увеличение характеристик", "")
        if ability_increase:
            for ru_name, en_name in self.ABILITY_NAME_MAP.items():
                bonus = self._parse_ability_bonus(ability_increase, ru_name)
                if bonus > 0:
                    current = getattr(character, en_name, 10)
                    setattr(character, en_name, current + bonus)
        
        speed_text = race_data.get("Скорость", "")
        if speed_text:
            speed_match = re.search(r'(\d+)\s*фут', speed_text)
            if speed_match:
                character.speed = int(speed_match.group(1))
        
        languages = race_data.get("Язык", race_data.get("Языки", ""))
        if languages:
            common_langs = ["Общий", "Эльфийский", "Дварфийский", "Орочий", "Гоблинский", 
                           "Гигантский", "Драконий", "Бездны", "Инфернальный", "Небесный"]
            for lang in common_langs:
                if lang.lower() in languages.lower() and lang not in character.languages:
                    character.languages.append(lang)
            if not character.languages:
                character.languages.append("Общий")
        
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

    def apply_class_features(self, character: Character, class_data: Dict, level: int = 1):
        character.hit_dice = class_data.get("hit_dice", "1d8")
        character.saving_throws = class_data.get("saving_throws", [])
        character.armor_proficiencies = class_data.get("armor_proficiencies", [])
        character.weapon_proficiencies = class_data.get("weapon_proficiencies", [])
        character.tool_proficiencies.extend(class_data.get("tool_proficiencies", []))
        
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

    def apply_background(self, character: Character, background_data: Dict):
        character.background_name = background_data.get("name", "")
        skill_profs = background_data.get("skill_proficiencies", {})
        fixed_skills = skill_profs.get("fixed", [])
        for skill in fixed_skills:
            if skill not in character.skills:
                character.skills.append(skill)
        
        equipment = background_data.get("equipment", {})
        character.gold += equipment.get("gold", 0)
        
        feature = background_data.get("feature", {})
        character.background_feature = f"{feature.get('name', '')}: {feature.get('description', '')[:300]}"
