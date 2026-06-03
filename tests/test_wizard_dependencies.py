"""UX2 wizard dependency helpers."""

from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.wizard.dependencies import (
    activated_profiles_for_wizard,
    format_mechanic_focus_summary,
)


def test_activated_profiles_empty_without_selections() -> None:
    assert activated_profiles_for_wizard(DeckCriteria()) == []


def test_activated_profiles_energy_and_tokens() -> None:
    criteria = DeckCriteria(
        themes=["tokens"],
        include_mechanics=["energy", "rad"],
    )
    ids = [p.profile_id for p in activated_profiles_for_wizard(criteria)]
    assert ids == ["energy", "rad", "tokens"]


def test_activated_profiles_voltron_aura_and_equipment() -> None:
    criteria = DeckCriteria(themes=["voltron"])
    ids = [p.profile_id for p in activated_profiles_for_wizard(criteria)]
    assert "aura_support" in ids
    assert "equipment" in ids


def test_activated_profiles_theme_only() -> None:
    criteria = DeckCriteria(themes=["aristocrats", "recursion", "landfall", "enchantress"])
    ids = {p.profile_id for p in activated_profiles_for_wizard(criteria)}
    assert ids == {"sacrifice", "graveyard", "landfall", "enchantments"}


def test_format_mechanic_focus_summary() -> None:
    text = format_mechanic_focus_summary({"energy": "engine", "tokens": "supported"})
    assert "Energy focus: engine" in text
    assert "Token focus: supported" in text


def test_format_mechanic_focus_summary_empty() -> None:
    assert format_mechanic_focus_summary({}) == "(default)"
