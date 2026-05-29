"""Wizard mechanics tests."""

from mtg_deck_tools.wizard.mechanics import (
    keyword_mechanic_choices,
    validate_mechanic_lists,
)


def test_keyword_mechanic_choices_exclude_partner():
    ids = {c.id for c in keyword_mechanic_choices()}
    assert "flying" in ids
    assert "partner" not in ids


def test_validate_mechanic_lists_rejects_overlap():
    errors = validate_mechanic_lists(["flying", "trample"], ["flying"])
    assert errors
    assert "flying" in errors[0]


def test_validate_mechanic_lists_ok():
    assert validate_mechanic_lists(["flying"], ["trample"]) == []
