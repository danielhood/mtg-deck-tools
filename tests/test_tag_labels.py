"""Mechanic tag display label tests."""

from __future__ import annotations

from mtg_deck_tools.tags.labels import format_tag_display_name, format_tag_list


def test_format_tag_display_name_uses_taxonomy_description() -> None:
    assert format_tag_display_name("landfall") == "Landfall triggers"
    assert format_tag_display_name("recursion") == "Graveyard recursion"


def test_format_tag_display_name_title_case_fallback() -> None:
    assert format_tag_display_name("double_strike") == "Double Strike"
    assert format_tag_display_name("deathtouch") == "Deathtouch"


def test_format_tag_list() -> None:
    result = format_tag_list(["recursion", "deathtouch"])
    assert result == "Graveyard recursion, Deathtouch"
