"""Constrained swap candidate filtering and picking (UX12)."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass

import sqlite3

from mtg_deck_tools.builder.availability_filters import filter_candidates_by_availability
from mtg_deck_tools.builder.budget_backfill import _deck_card_from_candidate
from mtg_deck_tools.builder.dependency_scoring import (
    build_deck_build_stats,
    build_search_pool,
    card_effects_enabled,
    filter_strict_dependency_candidates,
)
from mtg_deck_tools.builder.deck import DeckCard
from mtg_deck_tools.builder.filler import (
    TOP_POOL_SIZE,
    _BuildState,
    _pick_weighted,
    _type_counts,
)
from mtg_deck_tools.builder.pool import (
    CardCandidate,
    _row_to_candidate,
    fetch_card_by_oracle_id,
    fetch_candidates,
    fetch_card_tags,
)
from mtg_deck_tools.builder.price_filters import filter_candidates_by_price
from mtg_deck_tools.builder.rarity_filters import filter_candidates_by_rarity
from mtg_deck_tools.builder.scorer import score_candidate
from mtg_deck_tools.builder.slot_quality import refine_slot_candidates, slot_relax_steps
from mtg_deck_tools.models.swap_constraints import SwapConstraints
from mtg_deck_tools.rules.dependencies import fetch_card_effects

RARITY_RANK = {"common": 0, "uncommon": 1, "rare": 2, "mythic": 3}


@dataclass(frozen=True)
class SwapPreviewCandidate:
    oracle_id: str
    name: str
    mana_cost: str
    price_usd: float | None
    rarity: str | None


@dataclass(frozen=True)
class SwapPreviewPosition:
    from_oracle_id: str
    from_name: str
    slot: str
    candidates: list[SwapPreviewCandidate]


def _card_matches_type_lines(candidate: CardCandidate, constraints: SwapConstraints) -> bool:
    type_line = candidate.type_line or ""
    if constraints.type_lines_any:
        if not any(fragment in type_line for fragment in constraints.type_lines_any):
            return False
    if constraints.type_lines_none:
        if any(fragment in type_line for fragment in constraints.type_lines_none):
            return False
    return True


def _card_matches_colors(candidate: CardCandidate, colors: list[str]) -> bool:
    if not colors:
        return True
    identity = set(candidate.color_identity or [])
    return all(color in identity for color in colors)


def _card_matches_rarities(candidate: CardCandidate, rarities: list[str]) -> bool:
    if not rarities:
        return True
    rarity = (candidate.rarity or "").lower()
    if not rarity:
        return False
    allowed = {value.lower() for value in rarities}
    if rarity in allowed:
        return True
    rank = RARITY_RANK.get(rarity, -1)
    min_allowed = min(RARITY_RANK.get(value, 99) for value in allowed)
    return rank >= min_allowed


def _card_matches_max_price(candidate: CardCandidate, max_price: float | None) -> bool:
    if max_price is None:
        return True
    if candidate.price_usd is None:
        return True
    return candidate.price_usd <= max_price


def _card_matches_effect_role(
    conn: sqlite3.Connection,
    candidate: CardCandidate,
    constraints: SwapConstraints,
) -> bool:
    role = constraints.effect_role
    if role is None:
        return True
    if not card_effects_enabled(conn):
        return False
    effects = fetch_card_effects(conn, [candidate.oracle_id]).get(candidate.oracle_id, [])
    profile = role.profile_id.replace("_", "").lower()
    want = role.role.lower()
    for effect in effects:
        kind = effect.effect_kind.lower()
        payload = json.dumps(effect.payload).lower() if effect.payload else ""
        if want in kind and (not profile or profile in kind or profile in payload):
            return True
    if want == "equipment" and "Equipment" in (candidate.type_line or ""):
        return True
    return False


def filter_candidates_by_swap_constraints(
    conn: sqlite3.Connection,
    pool: list[CardCandidate],
    constraints: SwapConstraints | None,
) -> list[CardCandidate]:
    if constraints is None:
        return pool
    filtered: list[CardCandidate] = []
    for candidate in pool:
        if not _card_matches_type_lines(candidate, constraints):
            continue
        if not _card_matches_colors(candidate, constraints.colors_all):
            continue
        if not _card_matches_rarities(candidate, constraints.rarities):
            continue
        if not _card_matches_max_price(candidate, constraints.max_price_usd):
            continue
        if not _card_matches_effect_role(conn, candidate, constraints):
            continue
        filtered.append(candidate)
    return filtered


def _build_slot_pool(
    state: _BuildState,
    slot: str,
    *,
    relax_slot_guards: bool,
) -> list[CardCandidate]:
    candidates: list[CardCandidate] = []
    steps: list[list[str] | None] = [None] if relax_slot_guards else slot_relax_steps(slot, state.criteria)
    for require_tags in steps:
        pool = fetch_candidates(
            state.conn,
            identity=state.identity,
            exclude_oracle_ids=state.used_oracle_ids | state.commander_oracle_ids,
            exclude_names=state.used_names,
            avoid_mechanics=state.criteria.avoid_mechanics,
            require_theme_tags=require_tags,
            nonlands_only=True,
        )
        pool = filter_candidates_by_price(pool, state.criteria, state.budget_remaining())
        pool = filter_candidates_by_rarity(pool, state.criteria)
        pool = filter_candidates_by_availability(state.conn, pool, state.criteria)
        tag_map = fetch_card_tags(state.conn, [c.oracle_id for c in pool])
        refined = pool if relax_slot_guards else refine_slot_candidates(
            slot,
            pool,
            tag_map,
            criteria=state.criteria,
            require_theme_tags=require_tags,
        )
        if refined:
            candidates = refined
        if candidates:
            break
    return candidates


def _score_pool(
    state: _BuildState,
    slot: str,
    candidates: list[CardCandidate],
) -> list[tuple[CardCandidate, float]]:
    if (
        state.criteria.strict_dependencies
        and candidates
        and card_effects_enabled(state.conn)
    ):
        candidates = filter_strict_dependency_candidates(
            candidates,
            conn=state.conn,
            partial=state.cards,
            commander_oracle_ids=state.commander_oracle_ids,
        )
    tag_map = fetch_card_tags(state.conn, [c.oracle_id for c in candidates])
    type_counts = _type_counts(state.cards)
    deck_stats = None
    search_pool: list[tuple[str, float]] = []
    effect_map: dict[str, list] = {}
    if card_effects_enabled(state.conn):
        deck_stats = build_deck_build_stats(
            state.conn,
            state.cards,
            commander_oracle_ids=state.commander_oracle_ids,
            criteria=state.criteria,
        )
        search_pool = build_search_pool(
            state.conn,
            state.cards,
            state.commander_oracle_ids,
        )
        effect_map = fetch_card_effects(
            state.conn,
            [c.oracle_id for c in candidates],
        )
    scored: list[tuple[CardCandidate, float]] = []
    for candidate in candidates:
        score = score_candidate(
            candidate,
            slot=slot,
            archetype_themes=state.criteria.themes,
            include_mechanics=state.criteria.include_mechanics,
            commander_theme_tags=state.commander_theme_tags,
            card_tags=tag_map.get(candidate.oracle_id, []),
            type_counts=type_counts,
            budget_remaining=state.budget_remaining(),
            budget_usd=state.criteria.budget_usd,
            deck_stats=deck_stats,
            candidate_effects=effect_map.get(candidate.oracle_id, []),
            search_pool=search_pool,
        )
        scored.append((candidate, score))
    scored.sort(key=lambda row: row[1], reverse=True)
    return scored


def _pinned_candidate(
    state: _BuildState,
    constraints: SwapConstraints,
) -> CardCandidate:
    oracle_id = constraints.replacement_oracle_id
    if not oracle_id:
        raise ValueError("replacement_oracle_id is required.")
    if oracle_id in state.used_oracle_ids or oracle_id in state.commander_oracle_ids:
        raise ValueError(f"Card already in deck: {oracle_id}")
    row = fetch_card_by_oracle_id(state.conn, oracle_id)
    if row is None:
        raise ValueError(f"Unknown card: {oracle_id}")
    candidate = _row_to_candidate(row)
    filtered = filter_candidates_by_swap_constraints(state.conn, [candidate], constraints)
    if not filtered:
        raise ValueError(f"Replacement card does not match constraints: {candidate.name}")
    return candidate


def pick_swap_replacement(
    state: _BuildState,
    slot: str,
    *,
    constraints: SwapConstraints | None,
    rng: random.Random,
) -> CardCandidate | None:
    if constraints and constraints.replacement_oracle_id:
        return _pinned_candidate(state, constraints)

    relax = constraints is not None and constraints.slot_policy == "any"
    pool = _build_slot_pool(state, slot, relax_slot_guards=relax)
    pool = filter_candidates_by_swap_constraints(state.conn, pool, constraints)
    if not pool:
        return None
    scored = _score_pool(state, slot, pool)
    if not scored:
        return None
    picked = _pick_weighted(rng, scored[:TOP_POOL_SIZE], 1)
    return picked[0] if picked else None


def preview_swap_candidates(
    state: _BuildState,
    slot: str,
    *,
    constraints: SwapConstraints | None,
    limit: int = 8,
) -> list[SwapPreviewCandidate]:
    relax = constraints is not None and constraints.slot_policy == "any"
    pool = _build_slot_pool(state, slot, relax_slot_guards=relax)
    pool = filter_candidates_by_swap_constraints(state.conn, pool, constraints)
    scored = _score_pool(state, slot, pool)
    rows: list[SwapPreviewCandidate] = []
    for candidate, _ in scored[:limit]:
        rows.append(
            SwapPreviewCandidate(
                oracle_id=candidate.oracle_id,
                name=candidate.name,
                mana_cost=candidate.mana_cost,
                price_usd=candidate.price_usd,
                rarity=candidate.rarity,
            )
        )
    return rows


def add_candidate_to_state(state: _BuildState, slot: str, candidate: CardCandidate) -> DeckCard:
    tags = fetch_card_tags(state.conn, [candidate.oracle_id]).get(candidate.oracle_id, [])
    card = _deck_card_from_candidate(candidate, slot=slot, tags=tags)
    state.cards.append(card)
    state.used_oracle_ids.add(card.oracle_id)
    state.used_names.add(card.name)
    return card
