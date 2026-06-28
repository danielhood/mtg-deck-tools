"""Tests for plain-text deck list parsing."""

from __future__ import annotations

import pytest

from mtg_deck_tools.deck_import.parse_text import (
    parse_card_line,
    parse_text_deck_list,
)


def test_parse_card_line_quantity_prefix_x() -> None:
    name, qty = parse_card_line("1x Grave Pact")
    assert name == "Grave Pact"
    assert qty == 1


def test_parse_card_line_quantity_prefix_number() -> None:
    name, qty = parse_card_line("14 Swamp")
    assert name == "Swamp"
    assert qty == 14


def test_parse_card_line_quantity_suffix() -> None:
    name, qty = parse_card_line("Forest x13")
    assert name == "Forest"
    assert qty == 13


def test_parse_text_deck_list_sections_and_comments() -> None:
    text = """
    Commander
    Meren of Clan Nel Toth

    Deck
    1x Grave Pact
    1 Sol Ring
  # comment
    Forest x2
    """
    parsed = parse_text_deck_list(text)
    assert parsed.commanders == ["Meren of Clan Nel Toth"]
    assert [(line.name, line.quantity) for line in parsed.maindeck] == [
        ("Grave Pact", 1),
        ("Sol Ring", 1),
        ("Forest", 2),
    ]


def test_parse_text_deck_list_ignores_sideboard() -> None:
    text = """
    Commander
    Test Commander

    Deck
    Sol Ring

    Sideboard
    Counterspell
    """
    parsed = parse_text_deck_list(text)
    assert [line.name for line in parsed.maindeck] == ["Sol Ring"]


def test_parse_text_deck_list_lines_before_header_are_deck() -> None:
    parsed = parse_text_deck_list("Sol Ring\nLightning Greaves")
    assert parsed.commanders == []
    assert [line.name for line in parsed.maindeck] == ["Sol Ring", "Lightning Greaves"]


def test_parse_card_line_rejects_non_positive_quantity() -> None:
    with pytest.raises(ValueError, match="positive"):
        parse_text_deck_list("Deck\n0x Sol Ring")
