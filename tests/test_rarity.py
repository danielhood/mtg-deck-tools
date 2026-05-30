"""Rarity filtering and display tests."""

from __future__ import annotations

import pytest

from mtg_deck_tools.builder.pool import CardCandidate
from mtg_deck_tools.builder.rarity_filters import filter_candidates_by_rarity
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.rules.rarity import (
    format_rarity_display,
    passes_min_rarity,
)


def _candidate(*, rarity: str | None, is_basic_land: bool = False) -> CardCandidate:
    return CardCandidate(
        oracle_id="x",
        name="Test",
        cmc=2.0,
        type_line="Creature",
        mana_cost="{1}{G}",
        color_identity=["G"],
        price_usd=1.0,
        price_known=True,
        edhrec_rank=1000,
        oracle_text="",
        keywords=[],
        is_basic_land=is_basic_land,
        produced_mana=[],
        scryfall_uri=None,
        image_uri=None,
        rarity=rarity,
    )


def test_passes_min_rarity_common_allows_all() -> None:
    assert passes_min_rarity(rarity="common", min_rarity="common")
    assert passes_min_rarity(rarity=None, min_rarity="common")


def test_passes_min_rarity_uncommon_excludes_common() -> None:
    assert passes_min_rarity(rarity="uncommon", min_rarity="uncommon")
    assert not passes_min_rarity(rarity="common", min_rarity="uncommon")
    assert not passes_min_rarity(rarity=None, min_rarity="uncommon")


def test_passes_min_rarity_basic_land_always_passes() -> None:
    assert passes_min_rarity(
        rarity="common",
        min_rarity="mythic",
        is_basic_land=True,
    )


def test_filter_candidates_by_rarity() -> None:
    pool = [
        _candidate(rarity="common"),
        _candidate(rarity="rare"),
        _candidate(rarity="common", is_basic_land=True),
    ]
    criteria = DeckCriteria(min_rarity="rare", colors=["G"])
    filtered = filter_candidates_by_rarity(pool, criteria)
    assert len(filtered) == 2
    assert {c.rarity for c in filtered if not c.is_basic_land} == {"rare"}


def test_deck_criteria_normalizes_min_rarity() -> None:
    criteria = DeckCriteria(min_rarity="Rare")
    assert criteria.min_rarity == "rare"


def test_deck_criteria_rejects_invalid_min_rarity() -> None:
    with pytest.raises(ValueError, match="min_rarity"):
        DeckCriteria(min_rarity="legendary")


def test_format_rarity_display() -> None:
    assert format_rarity_display("mythic") == "Mythic"
    assert format_rarity_display(None) == "—"
