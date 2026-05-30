"""Minimum rarity filtering for candidate pools."""

from __future__ import annotations

from mtg_deck_tools.builder.pool import CardCandidate
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.rules.rarity import passes_min_rarity


def filter_candidates_by_rarity(
    candidates: list[CardCandidate],
    criteria: DeckCriteria,
) -> list[CardCandidate]:
    """Keep candidates at or above criteria.min_rarity (basic lands always pass)."""
    return [
        c
        for c in candidates
        if passes_min_rarity(
            rarity=c.rarity,
            min_rarity=criteria.min_rarity,
            is_basic_land=c.is_basic_land,
        )
    ]
