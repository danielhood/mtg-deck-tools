"""Per-card and deck-level USD price filters for the candidate pool."""

from __future__ import annotations

from mtg_deck_tools.builder.pool import CardCandidate
from mtg_deck_tools.models.criteria import DeckCriteria


def has_card_price_range(criteria: DeckCriteria) -> bool:
    return (
        criteria.card_price_min_usd is not None or criteria.card_price_max_usd is not None
    )


def passes_card_price_usd(
    *,
    price_usd: float | None,
    price_known: bool,
    min_usd: float | None,
    max_usd: float | None,
    strict: bool,
) -> bool:
    """True when USD price satisfies optional per-card min/max (shared with commander search)."""
    if not price_known or price_usd is None:
        if min_usd is not None:
            return False
        return not strict
    price = price_usd
    if min_usd is not None and price < min_usd:
        return False
    if max_usd is not None and price > max_usd:
        return False
    return True


def _passes_card_price_range(
    candidate: CardCandidate,
    *,
    min_usd: float | None,
    max_usd: float | None,
    strict: bool,
) -> bool:
    return passes_card_price_usd(
        price_usd=candidate.price_usd,
        price_known=candidate.price_known,
        min_usd=min_usd,
        max_usd=max_usd,
        strict=strict,
    )


def filter_card_price_range(
    candidates: list[CardCandidate],
    criteria: DeckCriteria,
) -> list[CardCandidate]:
    """Keep candidates within optional per-card min/max USD (priced cards only when min set)."""
    min_usd = criteria.card_price_min_usd
    max_usd = criteria.card_price_max_usd
    if min_usd is None and max_usd is None:
        return candidates
    return [
        c
        for c in candidates
        if _passes_card_price_range(
            c,
            min_usd=min_usd,
            max_usd=max_usd,
            strict=criteria.strict_budget,
        )
    ]


def filter_budget_remaining(
    candidates: list[CardCandidate],
    budget_remaining: float | None,
    *,
    strict: bool,
) -> list[CardCandidate]:
    if budget_remaining is None:
        return candidates
    filtered: list[CardCandidate] = []
    for candidate in candidates:
        if not candidate.price_known or candidate.price_usd is None:
            if strict:
                continue
            filtered.append(candidate)
            continue
        if candidate.price_usd <= budget_remaining:
            filtered.append(candidate)
    return filtered


def filter_candidates_by_price(
    candidates: list[CardCandidate],
    criteria: DeckCriteria,
    budget_remaining: float | None = None,
) -> list[CardCandidate]:
    """Apply per-card min/max, then remaining deck budget cap."""
    pool = filter_card_price_range(candidates, criteria)
    return filter_budget_remaining(
        pool,
        budget_remaining,
        strict=criteria.strict_budget,
    )
