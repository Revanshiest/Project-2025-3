from fastapi import APIRouter, Depends, HTTPException
from backend.repositories.data_repository import DataRepository
from backend.api.dependencies import get_data_repo

router = APIRouter(prefix="/api/v1/reference", tags=["Reference"])

@router.get("/races")
def get_races(repo: DataRepository = Depends(get_data_repo)):
    """Получить список всех рас"""
    races = repo.load_races()
    # Возвращаем список краткой информации для фронтенда
    result = []
    for key, data in races.items():
        if isinstance(data, dict):
            name = data.get("name") or data.get("Название") or key
            desc = data.get("description") or data.get("Описание") or ""
            
            # Если описание отсутствует, генерируем его динамически из структурированных полей
            if not desc:
                ability_increases = []
                if isinstance(data.get("ability_score_increase"), dict):
                    score_names = {
                        "strength": "Сила", "dexterity": "Ловкость", "constitution": "Телосложение",
                        "intelligence": "Интеллект", "wisdom": "Мудрость", "charisma": "Харизма", "any": "Любая"
                    }
                    for stat, bonus in data["ability_score_increase"].items():
                        ability_increases.append(f"{score_names.get(stat, stat)} +{bonus}")
                
                desc_parts = []
                if ability_increases:
                    desc_parts.append(f"Увеличение характеристик: {', '.join(ability_increases)}")
                if data.get("size"):
                    desc_parts.append(f"Размер: {data.get('size')}")
                
                speed = data.get("speed")
                if isinstance(speed, dict):
                    speeds = []
                    if "walk" in speed: speeds.append(f"пешком {speed['walk']} фт.")
                    if "fly" in speed: speeds.append(f"летая {speed['fly']} фт.")
                    if "swim" in speed: speeds.append(f"плавая {speed['swim']} фт.")
                    desc_parts.append(f"Скорость: {', '.join(speeds)}")
                elif speed:
                    desc_parts.append(f"Скорость: {speed} фт.")
                    
                if data.get("age"):
                    desc_parts.append(f"Возраст: {data.get('age')}")
                
                if data.get("languages"):
                    desc_parts.append(f"Языки: {', '.join(data.get('languages'))}")
                    
                traits = data.get("traits")
                if isinstance(traits, list) and traits:
                    desc_parts.append("\nОсобенности расы:")
                    for trait in traits:
                        if isinstance(trait, dict):
                            t_name = trait.get("name", "")
                            t_desc = trait.get("description", "")
                            desc_parts.append(f"• {t_name}: {t_desc}")
                
                desc = "\n".join(desc_parts)

            result.append({"key": key, "name": name, "description": desc})
    return {"total": len(result), "items": result}
    
@router.get("/races/{name}")
def get_race_by_name(name: str, repo: DataRepository = Depends(get_data_repo)):
    """Получить детальную информацию о расе"""
    race = repo.get_race_by_name(name)
    if not race:
        raise HTTPException(status_code=404, detail="Раса не найдена")
    return race

@router.get("/classes")
def get_classes(repo: DataRepository = Depends(get_data_repo)):
    """Получить список всех классов"""
    classes = repo.load_classes_structured()
    result = []
    for class_id, data in classes.items():
        name = data.get("name", class_id)
        desc = data.get("description", "")
        
        # Если описание отсутствует, генерируем его динамически из структурированных полей
        if not desc:
            desc_parts = []
            if data.get("hit_dice"):
                desc_parts.append(f"Кость хитов: {data.get('hit_dice')}")
            
            saves = data.get("saving_throws")
            if isinstance(saves, list) and saves:
                stat_map = {
                    "str": "Сила", "dex": "Ловкость", "con": "Телосложение",
                    "int": "Интеллект", "wis": "Мудрость", "cha": "Харизма"
                }
                save_names = [stat_map.get(s, s) for s in saves]
                desc_parts.append(f"Спасброски: {', '.join(save_names)}")
                
            weapons = data.get("weapon_proficiencies")
            if isinstance(weapons, list) and weapons:
                w_map = {
                    "simple": "простое оружие", "martial": "воинское оружие", 
                    "shortsword": "короткий меч", "rapier": "рапира", 
                    "longsword": "длинный меч", "hand_crossbow": "ручной арбалет"
                }
                weapon_names = [w_map.get(w, w) for w in weapons]
                desc_parts.append(f"Владение оружием: {', '.join(weapon_names)}")
                
            armors = data.get("armor_proficiencies")
            if isinstance(armors, list) and armors:
                a_map = {
                    "light": "легкие доспехи", "medium": "средние доспехи", 
                    "heavy": "тяжелые доспехи", "shields": "щиты"
                }
                armor_names = [a_map.get(a, a) for a in armors]
                desc_parts.append(f"Владение доспехами: {', '.join(armor_names)}")

            features = data.get("features", {})
            if isinstance(features, dict) and "1" in features:
                lvl1_feats = features["1"]
                if isinstance(lvl1_feats, list) and lvl1_feats:
                    desc_parts.append("\nУмения 1-го уровня:")
                    for feat in lvl1_feats:
                        if isinstance(feat, dict):
                            f_name = feat.get("name", "")
                            f_desc = feat.get("description", "")
                            desc_parts.append(f"• {f_name}: {f_desc}")
            
            desc = "\n".join(desc_parts)

        is_spellcaster = repo.is_spellcaster(class_id)
        result.append({
            "id": class_id, 
            "name": name, 
            "description": desc,
            "is_spellcaster": is_spellcaster
        })
    return {"total": len(result), "items": result}

@router.get("/classes/{class_id}")
def get_class_by_id(class_id: str, repo: DataRepository = Depends(get_data_repo)):
    """Получить детальную информацию о классе"""
    cls = repo.get_class_by_id(class_id)
    if not cls:
        raise HTTPException(status_code=404, detail="Класс не найден")
    return cls

@router.get("/spells/{level}")
def get_spells(level: str, repo: DataRepository = Depends(get_data_repo)):
    """Получить заклинания определенного уровня"""
    spells = repo.load_spells_by_level(level)
    if not spells:
        raise HTTPException(status_code=404, detail="Заклинания не найдены")
    return {"level": level, "items": spells}

@router.get("/skills")
def get_skills(repo: DataRepository = Depends(get_data_repo)):
    """Получить список всех навыков"""
    skills = repo.load_skills()
    return {"total": len(skills), "items": skills}

@router.get("/backgrounds")
def get_backgrounds(repo: DataRepository = Depends(get_data_repo)):
    """Получить список всех предысторий"""
    backgrounds = repo.load_backgrounds()
    result = []
    for key, data in backgrounds.items():
        name = data.get("name", key)
        desc = data.get("description", "")
        result.append({"id": key, "name": name, "description": desc})
    return {"total": len(result), "items": result}

@router.get("/items")
def get_items(repo: DataRepository = Depends(get_data_repo)):
    """Получить список всех предметов"""
    items = repo.load_items()
    # Assume items is a dict or list. If dict with categories, we flatten it or return as is.
    # Let's return as is for now.
    return items
