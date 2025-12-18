from src.character_creator import Character, apply_racial_bonuses
from src.character_data import get_race_by_name


def test_apply_racial_bonuses_only_adds_traits():
    rd = get_race_by_name("Ааракокра")
    assert rd is not None

    race_data = rd["data"]
    char = Character()
    # ensure empty
    assert char.racial_traits == []

    apply_racial_bonuses(char, race_data)

    # После применения у нас есть только элементы из поля traits
    assert len(char.racial_traits) > 0

    # Никакое поле вроде 'age' или 'size' не должно быть вставлено как 'Возраст:' и т.п.
    joined = "\n".join(char.racial_traits)
    assert "Возраст" not in joined
    assert "Размер" not in joined
    assert "Скорость" not in joined

    # Проверяем, что имена известных способностей присутствуют
    assert any("Полёт" in t or "Когти" in t or "Полёт" in t for t in char.racial_traits)
