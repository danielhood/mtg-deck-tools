"""Mana symbol Markdown formatting tests."""

from __future__ import annotations

from mtg_deck_tools.builder.mana_symbols import format_mana_notation


def test_mana_cost_parentheses_and_bold_digits() -> None:
    result = format_mana_notation("{4}{W}{W}", description=False)
    assert result == "**4**(W)(W)"
    assert "{" not in result


def test_mana_cost_hybrid_parentheses() -> None:
    result = format_mana_notation("{W/U}", description=False)
    assert result == "(W/U)"


def test_description_tap_untap_and_mana() -> None:
    result = format_mana_notation(
        "{T}: Add {G}. {Q}: Add {G}{G}.",
        description=True,
    )
    assert result == "**Tap**: Add (G). **Untap**: Add (G)(G)."


def test_description_numeric_in_reminder() -> None:
    result = format_mana_notation(
        "Equip {2} ({2}: Attach to target creature you control.)",
        description=True,
    )
    assert result.count("**2**") == 2
