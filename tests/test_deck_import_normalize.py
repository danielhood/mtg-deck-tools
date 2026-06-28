"""Tests for card name normalization."""

from mtg_deck_tools.deck_import.normalize import normalize_card_name


def test_normalize_card_name_strips_punctuation() -> None:
    assert normalize_card_name("Jace, the Mind Sculptor") == "jace the mind sculptor"


def test_normalize_card_name_casefolds() -> None:
    assert normalize_card_name("Sol Ring") == "sol ring"
