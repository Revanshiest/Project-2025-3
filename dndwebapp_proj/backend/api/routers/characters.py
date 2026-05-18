from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from datetime import datetime
from uuid import uuid4
from pydantic import BaseModel

from backend.services.character_service import CharacterService
from backend.services.level_up_service import LevelUpService
from backend.repositories.data_repository import DataRepository
from backend.repositories.character_repository import CharacterRepository
from backend.models.character import Character
from backend.api.dependencies import get_character_service, get_level_up_service, get_data_repo, get_char_repo

router = APIRouter(prefix="/api/v1/characters", tags=["Characters"])

class CharacterCreationRequest(BaseModel):
    user_id: int
    name: str
    race_name: str
    class_id: str
    background_id: str = ""
    abilities: Dict[str, int]
    cantrips: List[str] = []
    known_spells: List[str] = []
    equipment: List[str] = []

# --- Статические маршруты (должны быть ДО параметризованных) ---

@router.get("/tools/roll-abilities")
def roll_abilities(char_service: CharacterService = Depends(get_character_service)):
    """Сгенерировать случайные характеристики (4d6 отбрасывая худший)"""
    return {"rolls": char_service.roll_abilities()}

@router.get("/tools/standard-array")
def standard_array(char_service: CharacterService = Depends(get_character_service)):
    """Получить стандартный набор характеристик"""
    return {"array": char_service.get_standard_array()}

@router.post("/create")
def create_character(
    request: CharacterCreationRequest, 
    char_service: CharacterService = Depends(get_character_service),
    data_repo: DataRepository = Depends(get_data_repo),
    char_repo: CharacterRepository = Depends(get_char_repo)
):
    """
    Создать нового персонажа на основе финального выбора пользователя.
    Бэкенд только проверяет и применяет расовые бонусы и способности.
    Всё промежуточное состояние хранится на фронтенде.
    """
    # Создаем чистую модель
    character = Character()
    character.user_id = request.user_id
    character.id = f"{request.user_id}_{uuid4().hex[:12]}"
    character.name = request.name
    character.created_at = datetime.now().isoformat()
    character.updated_at = datetime.now().isoformat()
    
    # Устанавливаем характеристики
    character.strength = request.abilities.get("strength", 10)
    character.dexterity = request.abilities.get("dexterity", 10)
    character.constitution = request.abilities.get("constitution", 10)
    character.intelligence = request.abilities.get("intelligence", 10)
    character.wisdom = request.abilities.get("wisdom", 10)
    character.charisma = request.abilities.get("charisma", 10)
    
    # Применяем расу (400 если не найдена)
    race_data = data_repo.get_race_by_name(request.race_name)
    if not race_data:
        raise HTTPException(
            status_code=400,
            detail=f"Раса '{request.race_name}' не найдена в справочнике",
        )
    character.race_name = request.race_name
    character.race_key = race_data.get("key", "")
    char_service.apply_racial_bonuses(character, race_data.get("data", {}))
        
    # Применяем класс (400 если не найден)
    class_data = data_repo.get_class_by_id(request.class_id)
    if not class_data:
        raise HTTPException(
            status_code=400,
            detail=f"Класс '{request.class_id}' не найден в справочнике",
        )
    character.class_id = request.class_id
    character.class_name = class_data.get("name", request.class_id)
    char_service.apply_class_features(character, class_data, level=1)
    
    # Применяем предысторию
    if request.background_id:
        bg_data = data_repo.load_backgrounds().get(request.background_id)
        if bg_data:
            character.background_id = request.background_id
            character.background_name = bg_data.get("name", request.background_id)
            
    # Сохраняем заклинания и снаряжение
    character.spells.cantrips = request.cantrips
    character.spells.known_spells = request.known_spells
    character.equipment = request.equipment
        
    # Обновляем модификаторы и хиты
    character.update_modifiers()
    character.calculate_hp()
    if data_repo.is_spellcaster(request.class_id):
        character.update_spell_info()
        
    # Сохраняем в репозиторий (вместо сервиса)
    success = char_repo.save(character)
    
    if not success:
        raise HTTPException(status_code=500, detail="Ошибка сохранения персонажа")
        
    return {"status": "success", "character_id": character.id, "character": character}

# --- Параметризованные маршруты ---

@router.get("/{user_id}")
def get_user_characters(user_id: int, char_repo: CharacterRepository = Depends(get_char_repo)):
    """Получить список всех персонажей пользователя"""
    return char_repo.get_by_user(user_id)

@router.get("/{user_id}/{char_id}")
def get_character(user_id: int, char_id: str, char_repo: CharacterRepository = Depends(get_char_repo)):
    """Получить детальную информацию о конкретном персонаже"""
    char = char_repo.get_by_id(user_id, char_id)
    if not char:
        raise HTTPException(status_code=404, detail="Персонаж не найден")
    return char

@router.delete("/{user_id}/{char_id}")
def delete_character(user_id: int, char_id: str, char_repo: CharacterRepository = Depends(get_char_repo)):
    """Удалить персонажа"""
    success = char_repo.delete(user_id, char_id)
    if not success:
        raise HTTPException(status_code=404, detail="Персонаж не найден или ошибка удаления")
    return {"status": "success", "message": "Персонаж удален"}

class AddXpRequest(BaseModel):
    xp: int

@router.post("/{user_id}/{char_id}/add-xp")
def add_experience(
    user_id: int, 
    char_id: str, 
    request: AddXpRequest,
    char_repo: CharacterRepository = Depends(get_char_repo),
    level_up_service: LevelUpService = Depends(get_level_up_service)
):
    """Добавить опыт персонажу. Автоматически повышает уровень, если опыта достаточно (упрощенный вариант)"""
    char = char_repo.get_by_id(user_id, char_id)
    if not char:
        raise HTTPException(status_code=404, detail="Персонаж не найден")
        
    char.experience += request.xp
    
    # Простая проверка: достиг ли нового уровня?
    new_level = level_up_service._calculate_level_for_xp(char.experience)
    levels_gained = new_level - char.level
    
    if levels_gained > 0:
        char.level = new_level
        # Простейшее автоматическое повышение (average HP, без выбора спеллов)
        for _ in range(levels_gained):
            hit_dice = char.hit_dice if char.hit_dice else "1d8"
            dice_value = int(hit_dice.split("d")[1])
            avg_hp = (dice_value // 2) + 1
            hp_gain = max(1, avg_hp + char.con_mod)
            char.max_hp += hp_gain
            char.current_hp = char.max_hp
            
        char.update_modifiers()
        char.update_spell_info()
    
    char_repo.save(char)
    return {"status": "success", "leveled_up": levels_gained > 0, "character": char}
