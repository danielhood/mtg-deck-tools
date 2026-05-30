"""Availability heuristics for deck building (see planning/08-card-availability.md)."""

from __future__ import annotations

import sqlite3
from datetime import UTC, date, datetime

STOCKED_SET_TYPES = frozenset(
    {
        "core",
        "commander",
        "masters",
        "draft_innovation",
        "expansion",
        "alchemy",
        "standard",
    }
)

PRICE_PENDING_MONTHS = 4
OBSCURE_AGE_MONTHS = 120
POPULAR_EDHREC_MAX = 8000
OBSCURE_EDHREC_MIN = 15000

DEFAULT_AVAILABILITY_P25 = 35.0


def _parse_released_at(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def months_since_released(released_at: str | None, *, today: date | None = None) -> int | None:
    released = _parse_released_at(released_at)
    if released is None:
        return None
    ref = today or datetime.now(UTC).date()
    return (ref.year - released.year) * 12 + (ref.month - released.month)


def compute_availability_score(
    *,
    price_known: bool,
    edhrec_rank: int | None,
    released_at: str | None,
    set_type: str | None,
    reprint: bool,
) -> float:
    """
    Heuristic 0–100: higher means more likely obtainable (priced, played, reprinted).
    """
    score = 40.0
    if price_known:
        score += 40.0

    if edhrec_rank is not None:
        if edhrec_rank <= 500:
            score += 12.0
        elif edhrec_rank <= 2000:
            score += 8.0
        elif edhrec_rank <= 8000:
            score += 4.0
        elif edhrec_rank <= 15000:
            score += 1.0
        elif edhrec_rank > 20000:
            score -= 8.0

    if set_type in STOCKED_SET_TYPES:
        score += 4.0

    if reprint:
        score += 3.0

    if not price_known:
        age = months_since_released(released_at)
        if age is not None and age <= PRICE_PENDING_MONTHS:
            score += 5.0
        elif age is not None and age >= OBSCURE_AGE_MONTHS:
            score -= 12.0
        if edhrec_rank is None or edhrec_rank > OBSCURE_EDHREC_MIN:
            score -= 10.0

    return max(0.0, min(100.0, round(score, 2)))


def classify_unpriced_card(
    *,
    edhrec_rank: int | None,
    released_at: str | None,
) -> str:
    """
    Classify null-price cards for output notes.

    Returns ``price_pending`` (new or popular) or ``likely_obscure``.
    """
    age = months_since_released(released_at)
    if age is not None and age <= PRICE_PENDING_MONTHS:
        return "price_pending"
    if edhrec_rank is not None and edhrec_rank <= POPULAR_EDHREC_MAX:
        return "price_pending"
    if age is not None and age >= OBSCURE_AGE_MONTHS and (
        edhrec_rank is None or edhrec_rank > OBSCURE_EDHREC_MIN
    ):
        return "likely_obscure"
    if edhrec_rank is None or edhrec_rank > 20000:
        return "likely_obscure"
    return "price_pending"


def format_unpriced_warning(name: str, classification: str) -> str:
    if classification == "likely_obscure":
        return (
            f"Likely obscure: {name} (no USD price; may be hard to find; "
            "not counted toward budget)."
        )
    return (
        f"Price pending: {name} (new or popular; USD price may appear soon; "
        "not counted toward budget)."
    )


def record_availability_percentile(conn: sqlite3.Connection) -> float | None:
    """Store the 25th percentile availability score in import_metadata."""
    rows = conn.execute(
        """
        SELECT availability_score FROM cards
        WHERE commander_legal = 1
          AND commander_eligible = 0
          AND availability_score IS NOT NULL
        ORDER BY availability_score
        """
    ).fetchall()
    if not rows:
        return None
    scores = [float(r[0]) for r in rows]
    idx = min(len(scores) - 1, max(0, len(scores) // 4))
    p25 = scores[idx]
    conn.execute(
        "INSERT OR REPLACE INTO import_metadata (key, value) VALUES (?, ?)",
        ("availability_p25", str(p25)),
    )
    return p25


def get_availability_p25(conn: sqlite3.Connection) -> float:
    row = conn.execute(
        "SELECT value FROM import_metadata WHERE key = 'availability_p25'"
    ).fetchone()
    if row is None:
        return DEFAULT_AVAILABILITY_P25
    try:
        return float(row[0])
    except (TypeError, ValueError):
        return DEFAULT_AVAILABILITY_P25
