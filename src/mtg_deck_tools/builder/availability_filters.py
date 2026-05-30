"""Filter and rank candidates by import-time availability score."""

from __future__ import annotations

import sqlite3

from mtg_deck_tools.availability.score import get_availability_p25
from mtg_deck_tools.builder.pool import CardCandidate
from mtg_deck_tools.models.criteria import DeckCriteria


def filter_candidates_by_availability(
    conn: sqlite3.Connection,
    candidates: list[CardCandidate],
    criteria: DeckCriteria,
) -> list[CardCandidate]:
    """When prefer_available is set, drop cards below the import-time 25th percentile."""
    if not criteria.prefer_available:
        return candidates
    threshold = get_availability_p25(conn)
    filtered: list[CardCandidate] = []
    for candidate in candidates:
        score = candidate.availability_score
        if score is None:
            score = 50.0
        if score >= threshold:
            filtered.append(candidate)
    return filtered
