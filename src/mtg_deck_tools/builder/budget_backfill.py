"""Post-fill budget trimming by swapping expensive cards for cheaper alternatives."""

from __future__ import annotations

import sqlite3

from mtg_deck_tools.builder.deck import DeckCard, slot_theme_tags
from mtg_deck_tools.builder.pool import CardCandidate, fetch_candidates, fetch_card_tags
from mtg_deck_tools.builder.scorer import score_candidate, score_land_budget
from mtg_deck_tools.models.criteria import DeckCriteria


def _card_cost(card: DeckCard) -> float:
    if card.price_known and card.price_usd is not None:
        return card.price_usd * card.quantity
    return 0.0


def _deck_budget_spent(cards: list[DeckCard]) -> float:
    return sum(_card_cost(c) for c in cards)


def _deck_card_from_candidate(
    candidate: CardCandidate,
    *,
    slot: str,
    tags: list[str],
    quantity: int = 1,
) -> DeckCard:
    return DeckCard(
        oracle_id=candidate.oracle_id,
        name=candidate.name,
        slot=slot,
        quantity=quantity,
        cmc=candidate.cmc,
        mana_cost=candidate.mana_cost,
        type_line=candidate.type_line,
        price_usd=candidate.price_usd,
        price_known=candidate.price_known,
        scryfall_uri=candidate.scryfall_uri,
        image_uri=candidate.image_uri,
        mechanic_tags=tags,
        oracle_text=candidate.oracle_text,
        produced_mana=list(candidate.produced_mana),
        released_at=candidate.released_at,
        power=candidate.power,
        toughness=candidate.toughness,
    )


def _used_ids(cards: list[DeckCard]) -> set[str]:
    return {c.oracle_id for c in cards if "Basic" not in c.type_line}


def _used_names(cards: list[DeckCard]) -> set[str]:
    return {c.name for c in cards if "Basic" not in c.type_line}


def _type_counts(cards: list[DeckCard]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for card in cards:
        if "Land" in card.type_line:
            continue
        primary = card.type_line.split("—")[0].strip().split()
        key = primary[-1] if primary else "Other"
        counts[key] = counts.get(key, 0) + card.quantity
    return counts


def _replacement_price_cap(
    *,
    budget_cap: float,
    other_spent: float,
    card_price: float,
) -> float:
    """
    Maximum USD price allowed for a swap replacement.

    When the deck is already over cap, ``budget_cap - other_spent`` is negative
    even though cheaper replacements still help — fall back to any card priced
    below the one being swapped.
    """
    cap_by_budget = budget_cap - other_spent
    cap_by_savings = card_price - 0.01
    if cap_by_budget <= 0:
        return max(0.0, cap_by_savings)
    return min(cap_by_budget, cap_by_savings)


def _find_replacement(
    conn: sqlite3.Connection,
    *,
    card: DeckCard,
    cards: list[DeckCard],
    criteria: DeckCriteria,
    identity: list[str],
    commander_oracle_ids: set[str],
    commander_theme_tags: set[str],
    budget_cap: float,
    other_spent: float,
) -> CardCandidate | None:
    """Find a cheaper card for the same slot that moves the deck toward the cap."""
    card_price = card.price_usd or 0.0
    max_price = _replacement_price_cap(
        budget_cap=budget_cap,
        other_spent=other_spent,
        card_price=card_price,
    )
    if max_price <= 0 or card_price <= 0:
        return None

    theme_tags = slot_theme_tags(card.slot, criteria)
    relax_steps: list[list[str] | None] = [theme_tags]
    if theme_tags is not None:
        relax_steps.append(None)

    exclude_ids = (_used_ids(cards) | commander_oracle_ids) - {card.oracle_id}
    exclude_names = _used_names(cards) - {card.name}

    lands_only = card.slot == "lands" and "Basic" not in card.type_line
    nonlands_only = not lands_only

    candidates: list[CardCandidate] = []
    for require_tags in relax_steps:
        pool = fetch_candidates(
            conn,
            identity=identity,
            exclude_oracle_ids=exclude_ids,
            exclude_names=exclude_names,
            avoid_mechanics=criteria.avoid_mechanics,
            require_theme_tags=require_tags,
            lands_only=lands_only,
            nonlands_only=nonlands_only,
            limit=300,
        )
        pool = [
            c
            for c in pool
            if c.price_known
            and c.price_usd is not None
            and c.price_usd <= max_price
            and c.price_usd < card_price
        ]
        if pool:
            candidates = pool
            break

    if not candidates:
        return None

    remaining_cards = [c for c in cards if c.oracle_id != card.oracle_id]
    type_counts = _type_counts(remaining_cards)
    tag_map = fetch_card_tags(conn, [c.oracle_id for c in candidates])

    best: CardCandidate | None = None
    best_score = float("-inf")
    for candidate in candidates:
        card_score = score_candidate(
            candidate,
            slot=card.slot,
            archetype_themes=criteria.themes,
            include_mechanics=criteria.include_mechanics,
            commander_theme_tags=commander_theme_tags,
            card_tags=tag_map.get(candidate.oracle_id, []),
            type_counts=type_counts,
            budget_remaining=max_price,
        )
        if card.slot == "lands":
            card_score += score_land_budget(
                candidate,
                budget_remaining=max_price,
                budget_total=criteria.budget_usd,
            )
        if card_score > best_score:
            best_score = card_score
            best = candidate
    return best


def trim_deck_to_budget(
    conn: sqlite3.Connection,
    cards: list[DeckCard],
    criteria: DeckCriteria,
    *,
    identity: list[str],
    commander_oracle_ids: set[str],
    commander_theme_tags: set[str],
    unpriced_names: list[str],
    warnings: list[str],
) -> tuple[list[DeckCard], float, list[str]]:
    """
    Swap expensive cards for cheaper alternatives until under budget cap.

    Returns updated cards, budget_spent, and any new warnings.
    """
    if criteria.budget_usd is None:
        return cards, _deck_budget_spent(cards), warnings

    working = list(cards)
    new_warnings = list(warnings)
    cap = criteria.budget_usd
    max_iterations = len(working) * 5

    for _ in range(max_iterations):
        spent = _deck_budget_spent(working)
        if spent <= cap:
            break

        swappable = [
            c
            for c in working
            if "Basic" not in c.type_line
            and c.price_known
            and c.price_usd is not None
            and c.price_usd > 0
        ]
        if not swappable:
            break

        swappable.sort(key=lambda c: c.price_usd or 0, reverse=True)
        swapped = False
        for card in swappable:
            other_spent = spent - _card_cost(card)
            replacement = _find_replacement(
                conn,
                card=card,
                cards=working,
                criteria=criteria,
                identity=identity,
                commander_oracle_ids=commander_oracle_ids,
                commander_theme_tags=commander_theme_tags,
                budget_cap=cap,
                other_spent=other_spent,
            )
            if replacement is None:
                continue
            if replacement.oracle_id == card.oracle_id:
                continue

            tags = fetch_card_tags(conn, [replacement.oracle_id]).get(
                replacement.oracle_id, []
            )
            idx = working.index(card)
            working[idx] = _deck_card_from_candidate(
                replacement,
                slot=card.slot,
                tags=tags,
                quantity=card.quantity,
            )
            new_warnings.append(
                f"Budget trim: replaced {card.name} (${card.price_usd:.2f}) "
                f"with {replacement.name} (${replacement.price_usd:.2f})."
            )
            swapped = True
            break

        if not swapped:
            new_warnings.append(
                f"Budget trim: could not bring deck below ${cap:.2f} "
                f"(estimated ${spent:.2f})."
            )
            break

    spent = _deck_budget_spent(working)
    return working, spent, new_warnings
