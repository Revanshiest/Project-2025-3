from src.character_creator import Character
from src.level_up import LevelUpSession, create_levelup_session, build_levelup_cantrips_message, build_levelup_spells_message


def test_build_levelup_cantrips_message():
    c = Character(id="c1", user_id=1, class_id="wizard", class_name="Волшебник", level=1)
    session = create_levelup_session(1, c)
    # Принудительно указываем, что при повышении даётся 1 новый канtrip
    session.gains.new_cantrips = 1
    text, markup = build_levelup_cantrips_message(session)
    assert text is not None
    assert "Выбери заговоры" in text


def test_toggle_levelup_cantrips():
    c = Character(id="c3", user_id=3, class_id="wizard", class_name="Волшебник", level=1)
    session = create_levelup_session(3, c)
    session.gains.new_cantrips = 1
    text, markup = build_levelup_cantrips_message(session)
    # Toggle first available cantrip
    from src.level_up import handle_levelup_cantrip_toggle
    text2, markup2 = handle_levelup_cantrip_toggle(session, 0)
    assert session.selected_cantrips
    # Toggle again to remove
    text3, markup3 = handle_levelup_cantrip_toggle(session, 0)
    assert not session.selected_cantrips


def test_build_levelup_spells_message():
    c = Character(id="c2", user_id=2, class_id="wizard", class_name="Волшебник", level=1)
    session = create_levelup_session(2, c)
    session.gains.new_spells_known = 1
    text, markup = build_levelup_spells_message(session)
    assert text is not None
    assert "Выбери заклинания" in text


def test_toggle_levelup_spells():
    c = Character(id="c4", user_id=4, class_id="wizard", class_name="Волшебник", level=1)
    session = create_levelup_session(4, c)
    session.gains.new_spells_known = 1
    text, markup = build_levelup_spells_message(session)
    from src.level_up import handle_levelup_spell_toggle
    text2, markup2 = handle_levelup_spell_toggle(session, 0)
    assert session.selected_spells
    text3, markup3 = handle_levelup_spell_toggle(session, 0)
    assert not session.selected_spells
