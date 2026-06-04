"""Basic land pricing rules."""

from mtg_deck_tools.builder.deck_load import _deck_card_from_saved
from mtg_deck_tools.builder.price_filters import passes_card_price_usd
from mtg_deck_tools.import_.normalize import normalize_card
from mtg_deck_tools.pricing import BASIC_LAND_PRICE_USD, resolve_card_price


def test_normalize_basic_land_fixed_price_without_scryfall_usd() -> None:
    raw = {
        "oracle_id": "00000000-0000-0000-0000-000000000099",
        "name": "Swamp",
        "lang": "en",
        "layout": "normal",
        "type_line": "Basic Land — Swamp",
        "legalities": {"commander": "legal"},
        "prices": {},
    }
    row = normalize_card(raw)
    assert row is not None
    assert row["is_basic_land"] == 1
    assert row["price_usd"] == BASIC_LAND_PRICE_USD
    assert row["price_known"] == 1


def test_normalize_basic_land_overrides_scryfall_usd() -> None:
    raw = {
        "oracle_id": "00000000-0000-0000-0000-000000000098",
        "name": "Plains",
        "lang": "en",
        "layout": "normal",
        "type_line": "Basic Land — Plains",
        "legalities": {"commander": "legal"},
        "prices": {"usd": "2.00"},
    }
    row = normalize_card(raw)
    assert row is not None
    assert row["price_usd"] == BASIC_LAND_PRICE_USD


def test_resolve_card_price_from_type_line() -> None:
    assert resolve_card_price(
        price_usd=None,
        price_known=False,
        type_line="Basic Land — Island",
    ) == (BASIC_LAND_PRICE_USD, True)


def test_passes_card_price_range_exempts_basic_lands() -> None:
    assert passes_card_price_usd(
        price_usd=BASIC_LAND_PRICE_USD,
        price_known=True,
        min_usd=3.0,
        max_usd=20.0,
        strict=True,
        is_basic_land=True,
    )


def test_deck_load_applies_basic_land_price() -> None:
    card = _deck_card_from_saved(
        {
            "oracle_id": "x",
            "name": "Forest",
            "slot": "lands",
            "type_line": "Basic Land — Forest",
            "price_usd": 2.0,
            "price_known": True,
        }
    )
    assert card.price_usd == BASIC_LAND_PRICE_USD
    assert card.price_known is True
