from src.level_up import calculate_level_up_gains, create_levelup_session, apply_level_up
from src.character_creator import Character


def test_calculate_level_up_gains_includes_archetype_features():
    char = Character()
    char.class_id = "barbarian"
    char.class_name = "barbarian"
    char.level = 2  # next level will be 3 where archetype features appear
    char.archetype_name = "path_of_the_totem_warrior"

    gains = calculate_level_up_gains(char)
    assert gains.new_level == 3
    # Should offer archetype choice
    assert gains.archetype_choice is True
    assert len(gains.available_archetypes) > 0
    # Expect at least one archetype-related feature mentioning the archetype
    assert any("[path_of_the_totem_warrior]" in f.get("name", "") for f in gains.new_features)
    # Expect spells from grants to be noted
    assert any("beast_sense" in f.get("description", "") or "speak_with_animals" in f.get("description", "") for f in gains.new_features)


def test_get_archetypes_for_class_keys():
    from src.character_data import get_archetypes_for_class

    # English class id
    ar = get_archetypes_for_class("barbarian")
    assert isinstance(ar, dict) and len(ar) > 0

    # Russian class name
    ar_ru = get_archetypes_for_class("Варвар")
    assert isinstance(ar_ru, dict) and len(ar_ru) > 0


def test_apply_level_up_adds_prepared_spells_from_archetype():
    char = Character()
    char.class_id = "barbarian"
    char.class_name = "barbarian"
    char.level = 2
    char.archetype_name = "path_of_the_totem_warrior"

    gains = calculate_level_up_gains(char)
    session = create_levelup_session(user_id=1, character=char)
    session.gains = gains
    session.hp_choice = "average"
    session.selected_archetype = "path_of_the_totem_warrior"
    session.selected_cantrips = []

    updated = apply_level_up(session)

    # After applying, prepared_spells should include beast_sense and speak_with_animals
    prepared = getattr(updated.spells, "prepared_spells", [])
    assert "beast_sense" in prepared or "speak_with_animals" in prepared
    # Features should include archetype features
    assert any("[path_of_the_totem_warrior]" in f.get("name", "") for f in updated.features)


def test_selecting_archetype_augments_gains():
    from src.level_up import add_archetype_features_to_gains, calculate_level_up_gains
    char = Character()
    char.class_id = "barbarian"
    char.class_name = "barbarian"
    char.level = 2

    gains = calculate_level_up_gains(char)
    add_archetype_features_to_gains(gains, "barbarian", "path_of_the_totem_warrior")

    assert any("[path_of_the_totem_warrior]" in f.get("name", "") for f in gains.new_features)
    assert any("beast_sense" in f.get("description", "") or "speak_with_animals" in f.get("description", "") for f in gains.new_features)


def test_archetype_choice_ui_and_apply():
    # Simulate selection flow and application of choice
    from src.level_up import calculate_level_up_gains, add_archetype_features_to_gains, create_levelup_session, apply_level_up
    char = Character()
    char.class_id = "barbarian"
    char.class_name = "barbarian"
    char.level = 2

    gains = calculate_level_up_gains(char)
    add_archetype_features_to_gains(gains, "barbarian", "path_of_the_totem_warrior")

    # Expect at least one choice (totemic_spirit)
    assert gains.archetype_feature_choices
    choice = gains.archetype_feature_choices[0]
    assert choice["type"] in ("totem_animal", "environment") or choice["options"]

    session = create_levelup_session(10, char)
    session.gains = gains
    session.selected_archetype = "path_of_the_totem_warrior"
    # Simulate user choosing the first option for the first choice
    fid = choice["feature_id"]
    opt = choice["options"][0]
    session.selected_archetype_choices[fid] = [opt]

    updated = apply_level_up(session)
    # After apply, character should have a feature recording the choice
    assert any(opt in f.get("description", "") for f in updated.features)


def test_usage_grant_registration():
    from src.character_creator import Character
    from src.level_up import add_grant_from_feature
    from src.character_data import get_class_by_id

    char = Character()
    class_data = get_class_by_id("barbarian")
    feats = class_data.get("features", {}).get("1", [])
    # find the 'rage' feature
    rage = None
    for f in feats:
        if f.get("id") == "rage":
            rage = f
            break
    assert rage is not None

    add_grant_from_feature(char, rage, source="class", level=1)
    ga = char.granted_abilities.get("rage")
    assert ga is not None
    assert ga.get("uses_total") == 2
    assert ga.get("uses_remaining") == 2


def test_psi_warrior_no_choice_shows_features():
    from src.level_up import calculate_level_up_gains, add_archetype_features_to_gains
    char = Character()
    char.class_id = "fighter"
    char.class_name = "fighter"
    char.level = 2

    gains = calculate_level_up_gains(char)
    add_archetype_features_to_gains(gains, "fighter", "psi_warrior")

    # Для psi_warrior нет опций выбора — список choices должен быть пуст
    assert gains.archetype_feature_choices == []
    # Но должны быть добавлены фичи архетипа
    assert any("psi" in (f.get("name", "").lower() or "") or "psionic" in (f.get("description", "").lower() or "") for f in gains.new_features)
