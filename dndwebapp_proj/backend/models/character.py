from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any

class CharacterSpells(BaseModel):
    """
    Модель заклинаний. Наследуется от BaseModel, чтобы Pydantic 
    мог автоматически проверять типы данных.
    """
    cantrips: List[str] = Field(default_factory=list, description="Изученные заговоры")
    known_spells: List[str] = Field(default_factory=list, description="Известные заклинания")
    prepared_spells: List[str] = Field(default_factory=list, description="Подготовленные заклинания")
    spellbook: List[str] = Field(default_factory=list, description="Книга заклинаний (для волшебника)")
    max_cantrips: int = Field(default=0, ge=0) # ge=0 значит "больше или равно нулю"
    max_known: int = Field(default=0, ge=0)
    max_prepared: int = Field(default=0, ge=0)
    spell_slots: Dict[int, int] = Field(default_factory=dict, description="Уровень -> Количество ячеек")
    spell_slots_used: Dict[int, int] = Field(default_factory=dict)
    spellcasting_ability: str = ""
    spell_save_dc: int = 0
    spell_attack_bonus: int = 0

class Character(BaseModel):
    """
    Главная модель персонажа D&D. 
    BaseModel обеспечивает 100% валидацию типов на входе и выходе API.
    """
    id: str = ""
    user_id: int = 0
    name: str = ""
    race_key: str = ""
    race_name: str = ""
    class_id: str = ""
    class_name: str = ""
    archetype_name: str = ""
    background_id: str = ""
    background_name: str = ""
    level: int = Field(default=1, ge=1, le=20) # Уровень строго от 1 до 20
    experience: int = Field(default=0, ge=0)
    proficiency_bonus: int = 2
    
    # Характеристики (с валидацией, чтобы не было отрицательных)
    strength: int = Field(default=10, ge=0, le=30)
    dexterity: int = Field(default=10, ge=0, le=30)
    constitution: int = Field(default=10, ge=0, le=30)
    intelligence: int = Field(default=10, ge=0, le=30)
    wisdom: int = Field(default=10, ge=0, le=30)
    charisma: int = Field(default=10, ge=0, le=30)
    
    str_mod: int = 0
    dex_mod: int = 0
    con_mod: int = 0
    int_mod: int = 0
    wis_mod: int = 0
    cha_mod: int = 0
    
    max_hp: int = Field(default=0, ge=0)
    current_hp: int = Field(default=0, ge=0)
    temp_hp: int = Field(default=0, ge=0)
    hit_dice: str = ""
    hit_dice_remaining: int = 0
    
    armor_class: int = 10
    speed: int = 30
    
    armor_proficiencies: List[str] = Field(default_factory=list)
    weapon_proficiencies: List[str] = Field(default_factory=list)
    tool_proficiencies: List[str] = Field(default_factory=list)
    saving_throws: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    
    equipment: List[str] = Field(default_factory=list)
    gold: int = Field(default=0, ge=0)
    features: List[Dict[str, Any]] = Field(default_factory=list)
    spells: CharacterSpells = Field(default_factory=CharacterSpells)
    racial_traits: List[str] = Field(default_factory=list)
    granted_abilities: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    personality_traits: List[str] = Field(default_factory=list)
    ideals: List[str] = Field(default_factory=list)
    bonds: List[str] = Field(default_factory=list)
    flaws: List[str] = Field(default_factory=list)
    background_feature: str = ""
    created_at: str = ""
    updated_at: str = ""

    def update_modifiers(self) -> None:
        """
        Рассчитывает модификаторы характеристик по правилам D&D 5e.
        Формула: modifier = (ability_score - 10) // 2
        """
        self.str_mod = (self.strength - 10) // 2
        self.dex_mod = (self.dexterity - 10) // 2
        self.con_mod = (self.constitution - 10) // 2
        self.int_mod = (self.intelligence - 10) // 2
        self.wis_mod = (self.wisdom - 10) // 2
        self.cha_mod = (self.charisma - 10) // 2

    def calculate_hp(self) -> None:
        """
        Рассчитывает максимальное HP персонажа.
        На 1 уровне: max значение кости хитов + модификатор Телосложения.
        На последующих уровнях: + (среднее значение кости + con_mod) за каждый уровень.
        HP не может быть меньше 1.
        """
        hit_dice_map = {
            "1d6": 6, "1d8": 8, "1d10": 10, "1d12": 12
        }
        max_die = hit_dice_map.get(self.hit_dice, 8)

        # 1 уровень: максимальное значение кости + con_mod
        hp = max_die + self.con_mod

        # Последующие уровни: среднее значение кости + con_mod
        if self.level > 1:
            average_roll = max_die // 2 + 1
            hp += (average_roll + self.con_mod) * (self.level - 1)

        self.max_hp = max(hp, 1)
        self.current_hp = self.max_hp
        self.hit_dice_remaining = self.level

    def update_spell_info(self) -> None:
        """
        Рассчитывает DC спасброска заклинаний и бонус атаки заклинанием.
        Формулы по PHB:
          spell_save_dc = 8 + proficiency_bonus + spellcasting_ability_modifier
          spell_attack_bonus = proficiency_bonus + spellcasting_ability_modifier
        """
        ability_mod_map = {
            "intelligence": self.int_mod,
            "wisdom": self.wis_mod,
            "charisma": self.cha_mod,
            "strength": self.str_mod,
            "dexterity": self.dex_mod,
            "constitution": self.con_mod,
        }
        casting_mod = ability_mod_map.get(
            self.spells.spellcasting_ability.lower(), 0
        )
        self.spells.spell_save_dc = 8 + self.proficiency_bonus + casting_mod
        self.spells.spell_attack_bonus = self.proficiency_bonus + casting_mod

    def to_dict(self) -> dict:
        """Совместимость со старым кодом: выгрузка в словарь"""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: dict) -> "Character":
        """Совместимость со старым кодом: создание из словаря"""
        # Pydantic сам проверит все поля при создании
        return cls.model_validate(data)

