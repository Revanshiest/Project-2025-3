from src.character_data import load_races, get_race_names


def test_load_races_returns_dict():
    races = load_races()
    assert isinstance(races, dict), "load_races should return a dict"


def test_get_race_names_contains_known_race():
    names = get_race_names()
    assert isinstance(names, list)
    # Expect at least one known race name to be present
    assert any('Ааракокра' in n for n in names)
