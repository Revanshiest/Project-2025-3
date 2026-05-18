import logging
import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from backend.models.character import Character
from backend.repositories.data_repository import DataRepository

logger = logging.getLogger(__name__)


class LevelUpStep(Enum):
    START = "start"
    SHOW_GAINS = "show_gains"
    HP_ROLL = "hp_roll"
    ABILITY_INCREASE = "ability_increase"
    ARCHETYPE = "archetype"
    NEW_SPELLS = "new_spells"
    NEW_CANTRIPS = "new_cantrips"
    EXPERTISE = "expertise"
    FEATURE_CHOICE = "feature_choice"
    COMPLETE = "complete"

@dataclass
class LevelUpGains:
    new_level: int = 0
    hp_gain: int = 0
    hp_roll_options: Tuple[int, int] = (0, 0)
    new_features: List[Dict] = field(default_factory=list)
    ability_score_improvement: bool = False
    archetype_choice: bool = False
    archetype_level: int = 0
    available_archetypes: List[str] = field(default_factory=list)
    new_cantrips: int = 0
    new_spells_known: int = 0
    new_spell_slots: Dict[int, int] = field(default_factory=dict)
    max_spell_level: int = 0
    expertise_choice: bool = False
    expertise_count: int = 0
    archetype_feature_choices: List[Dict] = field(default_factory=list)

@dataclass
class LevelUpSession:
    user_id: int
    character_id: str
    character: Character
    step: LevelUpStep = LevelUpStep.START
    gains: LevelUpGains = field(default_factory=LevelUpGains)
    hp_choice: str = ""
    selected_abilities: Dict[str, int] = field(default_factory=dict)
    selected_archetype: str = ""
    selected_spells: List[str] = field(default_factory=list)
    selected_cantrips: List[str] = field(default_factory=list)
    selected_expertise: List[str] = field(default_factory=list)
    selected_archetype_choices: Dict[str, List[str]] = field(default_factory=dict)
    current_page: int = 1
    items_per_page: int = 8

class LevelUpService:
    """
    Сервис повышения уровня персонажей.
    """

    # Таблица опыта по PHB (Player's Handbook) D&D 5e.
    # Ключ — уровень, значение — минимальный XP для достижения этого уровня.
    XP_TABLE: Dict[int, int] = {
        1: 0,
        2: 300,
        3: 900,
        4: 2700,
        5: 6500,
        6: 14000,
        7: 23000,
        8: 34000,
        9: 48000,
        10: 64000,
        11: 85000,
        12: 100000,
        13: 120000,
        14: 140000,
        15: 165000,
        16: 195000,
        17: 225000,
        18: 265000,
        19: 305000,
        20: 355000,
    }

    def __init__(self, data_repo: DataRepository):
        self.data_repo = data_repo
        self._levelup_sessions: Dict[int, LevelUpSession] = {}

    def get_levelup_session(self, user_id: int) -> Optional[LevelUpSession]:
        return self._levelup_sessions.get(user_id)

    def create_levelup_session(self, user_id: int, character: Character) -> LevelUpSession:
        if user_id in self._levelup_sessions:
            logger.warning(
                "Перезапись существующей сессии повышения уровня для user_id=%d", user_id
            )
        session = LevelUpSession(
            user_id=user_id,
            character_id=character.id,
            character=character
        )
        self._levelup_sessions[user_id] = session
        return session

    def delete_levelup_session(self, user_id: int):
        if user_id in self._levelup_sessions:
            del self._levelup_sessions[user_id]

    def _get_proficiency_bonus(self, level: int) -> int:
        return (level - 1) // 4 + 2

    def _get_xp_threshold(self, level: int) -> int:
        """Возвращает минимальный XP для данного уровня из таблицы PHB."""
        return self.XP_TABLE.get(level, 0)

    def _calculate_level_for_xp(self, xp: int) -> int:
        """
        Определяет уровень персонажа на основе его текущего XP.
        Проходит таблицу от 20 к 1, чтобы найти максимальный подходящий уровень.
        """
        for level in range(20, 0, -1):
            if xp >= self.XP_TABLE[level]:
                return level
        return 1

    def calculate_level_up_gains(self, character: Character) -> LevelUpGains:
        new_level = character.level + 1
        gains = LevelUpGains(new_level=new_level)
        
        class_data = self.data_repo.get_class_by_id(character.class_id)
        if not class_data:
            return gains
        
        hit_dice = class_data.get("hit_dice", "1d8")
        dice_value = int(hit_dice.split("d")[1])
        average_hp = (dice_value // 2) + 1
        gains.hp_roll_options = (average_hp, dice_value)
        
        features = class_data.get("features", {})
        level_features = features.get(str(new_level), [])
        
        for feature in level_features:
            if isinstance(feature, dict):
                feature_info = {
                    "name": feature.get("name", ""),
                    "description": feature.get("description", ""),
                    "usage": feature.get("usage"),
                    "grants": feature.get("grants")
                }
                if feature.get("subclass_feature"):
                    gains.archetype_choice = True
                    gains.archetype_level = new_level
                    # Подгрузка архетипов временно опущена для упрощения, 
                    # в идеале нужно брать из data_repo.get_archetypes_for_class
                if feature.get("id") == "ability_score_improvement":
                    gains.ability_score_improvement = True
                gains.new_features.append(feature_info)
        
        # Для магов логика spellcasting_info будет здесь (опущена для краткости)
        if character.class_id in ["rogue", "bard"]:
            expertise_levels = {"rogue": [1, 6], "bard": [3, 10]}
            if new_level in expertise_levels.get(character.class_id, []):
                gains.expertise_choice = True
                gains.expertise_count = 2
        
        return gains

    def apply_level_up(self, session: LevelUpSession) -> Character:
        character = session.character
        gains = session.gains
        
        character.level = gains.new_level
        character.proficiency_bonus = self._get_proficiency_bonus(character.level)
        
        if session.hp_choice == "average":
            hp_gain = gains.hp_roll_options[0] + character.con_mod
        else:
            dice = gains.hp_roll_options[1]
            hp_gain = random.randint(1, dice) + character.con_mod
        
        hp_gain = max(1, hp_gain)
        character.max_hp += hp_gain
        character.current_hp = character.max_hp
        character.hit_dice_remaining = character.level
        
        for feature in gains.new_features:
            character.features.append({
                "level": gains.new_level,
                "name": feature.get("name", ""),
                "description": feature.get("description", "")
            })
        
        if gains.ability_score_improvement and session.selected_abilities:
            for ability, increase in session.selected_abilities.items():
                current = getattr(character, ability, 10)
                new_value = min(20, current + increase)
                setattr(character, ability, new_value)
        
        if session.selected_cantrips:
            character.spells.cantrips.extend(session.selected_cantrips)
        
        if session.selected_spells:
            character.spells.known_spells.extend(session.selected_spells)
        
        return character

    def roll_hp_for_level(self, hit_dice: str, con_mod: int) -> int:
        dice_value = int(hit_dice.split("d")[1])
        return max(1, random.randint(1, dice_value) + con_mod)

    def get_average_hp_for_level(self, hit_dice: str, con_mod: int) -> int:
        dice_value = int(hit_dice.split("d")[1])
        return max(1, (dice_value // 2) + 1 + con_mod)

    def can_level_up(self, character: Character) -> bool:
        """
        Проверяет, может ли персонаж повысить уровень на основе XP-таблицы PHB.
        Возвращает True, если текущий XP >= порога для следующего уровня.
        """
        if character.level >= 20:
            return False
        next_level = character.level + 1
        required_xp = self._get_xp_threshold(next_level)
        return character.experience >= required_xp

    def add_experience(self, character: Character, xp: int) -> Tuple[bool, int]:
        """
        Начисляет опыт персонажу и определяет, сколько уровней он может получить.
        
        Args:
            character: Персонаж, которому начисляется опыт.
            xp: Количество опыта для начисления.
            
        Returns:
            Tuple[bool, int]: (произошло ли повышение уровня, количество набранных уровней)
        """
        character.experience += xp
        new_level = self._calculate_level_for_xp(character.experience)
        levels_gained = new_level - character.level

        if levels_gained > 0:
            logger.info(
                "Персонаж %s получил %d XP (всего: %d). Доступно повышений: %d (с %d до %d)",
                character.id, xp, character.experience,
                levels_gained, character.level, new_level,
            )
            return True, levels_gained

        return False, 0
