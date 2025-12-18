from src.character_data import get_race_by_name
from src.character_creation import format_race_detail_text


def test_get_race_by_name_returns_data():
    rd = get_race_by_name("Ааракокра")
    assert rd is not None
    assert "data" in rd


def test_format_race_detail_text_contains_fields():
    rd = get_race_by_name("Ааракокра")
    assert rd is not None
    txt = format_race_detail_text("Ааракокра", rd["data"])
    assert "Скорость" in txt or "🏃" in txt
    assert "Полёт" in txt or "Полёт" in txt or "Когти" in txt or "Особенности" in txt
