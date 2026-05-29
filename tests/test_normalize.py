"""Card normalization tests."""

from mtg_deck_tools.import_.normalize import normalize_card


def test_normalize_basic_creature():
    raw = {
        "oracle_id": "00000000-0000-0000-0000-000000000001",
        "id": "scry-id",
        "name": "Test Creature",
        "lang": "en",
        "layout": "normal",
        "type_line": "Legendary Creature — Human",
        "oracle_text": "Flying",
        "mana_cost": "{2}{U}",
        "cmc": 3.0,
        "colors": ["U"],
        "color_identity": ["U"],
        "keywords": ["Flying"],
        "legalities": {"commander": "legal"},
        "prices": {"usd": "1.50"},
    }
    row = normalize_card(raw)
    assert row is not None
    assert row["commander_eligible"] == 1
    assert row["playable"] is True
    assert row["price_known"] == 1
    assert row["price_usd"] == 1.5


def test_normalize_skips_non_english_via_playable():
    raw = {
        "oracle_id": "00000000-0000-0000-0000-000000000002",
        "name": "Carte",
        "lang": "fr",
        "layout": "normal",
        "type_line": "Creature",
        "legalities": {"commander": "legal"},
    }
    row = normalize_card(raw)
    assert row is not None
    assert row["playable"] is False
