"""Unit tests for search_library payload matching."""

from __future__ import annotations

from mtg_deck_tools.rules.tutor_payload import payload_matches_card


def test_artifact_or_enchantment_matches_either_type() -> None:
    payload = {"types": ["artifact", "enchantment"], "type_match": "any"}
    assert payload_matches_card("Artifact", 1.0, payload)
    assert payload_matches_card("Enchantment — Aura", 2.0, payload)
    assert not payload_matches_card("Creature — Elf", 2.0, payload)


def test_creature_or_planeswalker_union() -> None:
    payload = {"types": ["creature", "planeswalker"], "type_match": "any"}
    assert payload_matches_card("Creature — Human", 3.0, payload)
    assert payload_matches_card("Legendary Planeswalker — Jace", 4.0, payload)
    assert not payload_matches_card("Instant", 2.0, payload)


def test_min_and_max_cmc_on_creatures() -> None:
    assert payload_matches_card(
        "Creature — Beast",
        6.0,
        {"types": ["creature"], "min_cmc": 6},
    )
    assert not payload_matches_card(
        "Creature — Beast",
        5.0,
        {"types": ["creature"], "min_cmc": 6},
    )
    assert payload_matches_card(
        "Creature — Soldier",
        3.0,
        {"types": ["creature"], "max_cmc": 3},
    )
    assert not payload_matches_card(
        "Creature — Soldier",
        4.0,
        {"types": ["creature"], "max_cmc": 3},
    )


def test_colored_creature_requires_card_colors() -> None:
    payload = {"types": ["creature"], "colors": ["G"]}
    assert payload_matches_card(
        "Creature — Elf",
        1.0,
        payload,
        colors=["G"],
    )
    assert not payload_matches_card(
        "Creature — Merfolk",
        2.0,
        payload,
        colors=["U"],
    )
    assert not payload_matches_card(
        "Creature — Merfolk",
        2.0,
        payload,
        colors=[],
    )


def test_forest_land_subtype() -> None:
    payload = {"types": ["land"], "subtypes": ["Forest"]}
    assert payload_matches_card("Land — Forest", 0.0, payload)
    assert not payload_matches_card("Land — Island", 0.0, payload)
