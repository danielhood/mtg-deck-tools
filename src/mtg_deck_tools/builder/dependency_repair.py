"""Post-build dependency repair via targeted card swaps (D5)."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any

from mtg_deck_tools.builder.budget_backfill import (
    _deck_card_from_candidate,
    _used_ids,
    _used_names,
)
from mtg_deck_tools.builder.dependency_scoring import (
    build_deck_build_stats,
    build_search_pool,
    card_effects_enabled,
    dependency_pick_score,
    filter_strict_dependency_candidates,
)
from mtg_deck_tools.builder.deck import DeckCard
from mtg_deck_tools.builder.pool import CardCandidate, fetch_candidates, fetch_card_tags
from mtg_deck_tools.builder.availability_filters import filter_candidates_by_availability
from mtg_deck_tools.builder.price_filters import filter_candidates_by_price
from mtg_deck_tools.builder.rarity_filters import filter_candidates_by_rarity
from mtg_deck_tools.builder.scorer import score_candidate
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.rules.dependencies import (
    DependencyIssue,
    fetch_card_effects,
    payload_matches_card,
    validate_dependencies,
)

MAX_REPAIR_SWAPS = 10
ISSUE_PRIORITY = (
    "TUTOR_TARGET_EXISTS",
    "ENERGY_BALANCE",
    "TYPE_SYNERGY_MIN",
    "AURA_SUPPORT_MIN",
)
SWAP_SLOT_ORDER = ("flex", "synergy", "wincon", "draw", "removal", "board_wipe", "ramp")


@dataclass
class DependencyRepairResult:
    cards: list[DeckCard]
    messages: list[str]
    swaps: int = 0


def _issue_sort_key(issue: DependencyIssue) -> tuple[int, int]:
    status_rank = 0 if issue.status == "fail" else 1
    try:
        rule_rank = ISSUE_PRIORITY.index(issue.rule_id)
    except ValueError:
        rule_rank = len(ISSUE_PRIORITY)
    return (status_rank, rule_rank)


def _pick_issue(report) -> DependencyIssue | None:
    if not report.issues:
        return None
    return min(report.issues, key=_issue_sort_key)


def _pick_victim(
    cards: list[DeckCard],
    *,
    protect_oracle_ids: set[str],
) -> DeckCard | None:
    for slot in SWAP_SLOT_ORDER:
        for card in cards:
            if card.slot != slot:
                continue
            if card.oracle_id in protect_oracle_ids:
                continue
            if "Basic" in card.type_line:
                continue
            return card
    return None


def _apply_swap(
    cards: list[DeckCard],
    victim: DeckCard,
    replacement: CardCandidate,
    tags: list[str],
) -> list[DeckCard]:
    working = list(cards)
    idx = working.index(victim)
    working[idx] = _deck_card_from_candidate(
        replacement,
        slot=victim.slot,
        tags=tags,
        quantity=victim.quantity,
    )
    return working


def _fetch_with_effect_kind(
    conn: sqlite3.Connection,
    *,
    effect_kind: str,
    identity: list[str],
    exclude_oracle_ids: set[str],
    exclude_names: set[str],
    criteria: DeckCriteria,
    limit: int = 200,
) -> list[CardCandidate]:
    from mtg_deck_tools.builder.pool import _color_identity_clauses, _row_to_candidate

    sql = """
        SELECT DISTINCT c.oracle_id, c.name, c.cmc, c.type_line, c.mana_cost,
               c.color_identity, c.price_usd, c.price_known, c.edhrec_rank,
               c.oracle_text, c.keywords, c.is_basic_land, c.produced_mana,
               c.scryfall_uri, c.image_uri, c.released_at, c.power, c.toughness,
               c.rarity, c.availability_score
        FROM cards c
        JOIN card_effects e ON e.oracle_id = c.oracle_id AND e.effect_kind = ?
        WHERE c.commander_legal = 1 AND c.commander_eligible = 0
    """
    params: list[Any] = [effect_kind]

    if exclude_oracle_ids:
        placeholders = ",".join("?" * len(exclude_oracle_ids))
        sql += f" AND c.oracle_id NOT IN ({placeholders})"
        params.extend(sorted(exclude_oracle_ids))

    if exclude_names:
        placeholders = ",".join("?" * len(exclude_names))
        sql += f" AND c.name NOT IN ({placeholders})"
        params.extend(sorted(exclude_names))

    identity_sql, identity_params = _color_identity_clauses(identity)
    sql += identity_sql
    params.extend(identity_params)
    sql += " LIMIT ?"
    params.append(limit)

    rows = conn.execute(sql, params).fetchall()
    candidates = [_row_to_candidate(r) for r in rows]
    candidates = filter_candidates_by_price(candidates, criteria, criteria.budget_usd)
    candidates = filter_candidates_by_rarity(candidates, criteria)
    return filter_candidates_by_availability(conn, candidates, criteria)


def _score_repair_pick(
    conn: sqlite3.Connection,
    candidates: list[CardCandidate],
    *,
    partial: list[DeckCard],
    commander_oracle_ids: set[str],
    slot: str,
    criteria: DeckCriteria,
    commander_theme_tags: set[str],
) -> CardCandidate | None:
    if not candidates:
        return None
    tag_map = fetch_card_tags(conn, [c.oracle_id for c in candidates])
    deck_stats = build_deck_build_stats(
        conn,
        partial,
        commander_oracle_ids=commander_oracle_ids,
        criteria=criteria,
    )
    search_pool = build_search_pool(conn, partial, commander_oracle_ids)
    effect_map = fetch_card_effects(conn, [c.oracle_id for c in candidates])
    type_counts: dict[str, int] = {}
    best: CardCandidate | None = None
    best_score = float("-inf")
    for candidate in candidates:
        score = score_candidate(
            candidate,
            slot=slot,
            archetype_themes=criteria.themes,
            include_mechanics=criteria.include_mechanics,
            commander_theme_tags=commander_theme_tags,
            card_tags=tag_map.get(candidate.oracle_id, []),
            type_counts=type_counts,
            budget_remaining=None,
            budget_usd=criteria.budget_usd,
            deck_stats=deck_stats,
            candidate_effects=effect_map.get(candidate.oracle_id, []),
            search_pool=search_pool,
        )
        score += dependency_pick_score(
            candidate,
            effect_map.get(candidate.oracle_id, []),
            deck_stats,
            search_pool,
        )
        if score > best_score:
            best_score = score
            best = candidate
    return best


def _prepare_pool(
    conn: sqlite3.Connection,
    candidates: list[CardCandidate],
    *,
    partial: list[DeckCard],
    commander_oracle_ids: set[str],
    criteria: DeckCriteria,
) -> list[CardCandidate]:
    if criteria.strict_dependencies and candidates:
        return filter_strict_dependency_candidates(
            candidates,
            conn=conn,
            partial=partial,
            commander_oracle_ids=commander_oracle_ids,
        )
    return candidates


def _fix_tutor_target(
    conn: sqlite3.Connection,
    cards: list[DeckCard],
    issue: DependencyIssue,
    *,
    criteria: DeckCriteria,
    identity: list[str],
    commander_oracle_ids: set[str],
    commander_theme_tags: set[str],
) -> tuple[list[DeckCard], str] | None:
    detail = issue.detail or {}
    payload = detail.get("payload")
    if not payload:
        return None
    protect = {issue.card_oracle_id} if issue.card_oracle_id else set()
    victim = _pick_victim(cards, protect_oracle_ids=protect)
    if victim is None:
        return None

    exclude_ids = _used_ids(cards) | commander_oracle_ids
    exclude_names = _used_names(cards)
    pool = fetch_candidates(
        conn,
        identity=identity,
        exclude_oracle_ids=exclude_ids,
        exclude_names=exclude_names,
        avoid_mechanics=criteria.avoid_mechanics,
        require_theme_tags=None,
        nonlands_only=True,
        limit=400,
    )
    pool = [
        c
        for c in pool
        if payload_matches_card(c.type_line, c.cmc, payload)
    ]
    pool = filter_candidates_by_price(pool, criteria, criteria.budget_usd)
    pool = filter_candidates_by_rarity(pool, criteria)
    pool = filter_candidates_by_availability(conn, pool, criteria)
    pool = _prepare_pool(
        conn,
        pool,
        partial=cards,
        commander_oracle_ids=commander_oracle_ids,
        criteria=criteria,
    )
    pick = _score_repair_pick(
        conn,
        pool,
        partial=cards,
        commander_oracle_ids=commander_oracle_ids,
        slot=victim.slot,
        criteria=criteria,
        commander_theme_tags=commander_theme_tags,
    )
    if pick is None:
        return None
    tags = fetch_card_tags(conn, [pick.oracle_id]).get(pick.oracle_id, [])
    updated = _apply_swap(cards, victim, pick, tags)
    return (
        updated,
        f"Dependency repair: replaced {victim.name} with {pick.name} (tutor target).",
    )


def swap_energy_card(
    conn: sqlite3.Connection,
    cards: list[DeckCard],
    effect_kind: str,
    *,
    criteria: DeckCriteria,
    identity: list[str],
    commander_oracle_ids: set[str],
    commander_theme_tags: set[str],
    protect_oracle_ids: set[str] | None = None,
) -> tuple[list[DeckCard], str] | None:
    """Replace a flex/synergy card with an energy producer or consumer."""
    victim = _pick_victim(cards, protect_oracle_ids=protect_oracle_ids or set())
    if victim is None:
        return None

    exclude_ids = _used_ids(cards) | commander_oracle_ids
    exclude_names = _used_names(cards)
    pool = _fetch_with_effect_kind(
        conn,
        effect_kind=effect_kind,
        identity=identity,
        exclude_oracle_ids=exclude_ids,
        exclude_names=exclude_names,
        criteria=criteria,
    )
    pool = _prepare_pool(
        conn,
        pool,
        partial=cards,
        commander_oracle_ids=commander_oracle_ids,
        criteria=criteria,
    )
    pick = _score_repair_pick(
        conn,
        pool,
        partial=cards,
        commander_oracle_ids=commander_oracle_ids,
        slot=victim.slot,
        criteria=criteria,
        commander_theme_tags=commander_theme_tags,
    )
    if pick is None:
        return None
    tags = fetch_card_tags(conn, [pick.oracle_id]).get(pick.oracle_id, [])
    updated = _apply_swap(cards, victim, pick, tags)
    role = "payoff" if effect_kind == "energy_consume" else "producer"
    return (
        updated,
        f"Dependency repair: replaced {victim.name} with {pick.name} (energy {role}).",
    )


def _fix_energy_balance(
    conn: sqlite3.Connection,
    cards: list[DeckCard],
    issue: DependencyIssue,
    *,
    criteria: DeckCriteria,
    identity: list[str],
    commander_oracle_ids: set[str],
    commander_theme_tags: set[str],
) -> tuple[list[DeckCard], str] | None:
    detail = issue.detail or {}
    producers = detail.get("producers") or []
    consumers = detail.get("consumers") or []
    effect_kind = "energy_consume" if producers and not consumers else "energy_produce"
    return swap_energy_card(
        conn,
        cards,
        effect_kind,
        criteria=criteria,
        identity=identity,
        commander_oracle_ids=commander_oracle_ids,
        commander_theme_tags=commander_theme_tags,
    )


def _fix_subtype_support(
    conn: sqlite3.Connection,
    cards: list[DeckCard],
    issue: DependencyIssue,
    *,
    criteria: DeckCriteria,
    identity: list[str],
    commander_oracle_ids: set[str],
    commander_theme_tags: set[str],
) -> tuple[list[DeckCard], str] | None:
    detail = issue.detail or {}
    subtype = detail.get("subtype")
    card_type = detail.get("type")
    if subtype:
        label = subtype

        def match(c: CardCandidate) -> bool:
            return subtype in c.type_line and "Creature" in c.type_line

    elif card_type:
        label = card_type
        needle = card_type.capitalize()

        def match(c: CardCandidate) -> bool:
            return needle in c.type_line

    else:
        return None

    protect = {issue.card_oracle_id} if issue.card_oracle_id else set()
    victim = _pick_victim(cards, protect_oracle_ids=protect)
    if victim is None:
        return None

    exclude_ids = _used_ids(cards) | commander_oracle_ids
    exclude_names = _used_names(cards)
    pool = fetch_candidates(
        conn,
        identity=identity,
        exclude_oracle_ids=exclude_ids,
        exclude_names=exclude_names,
        avoid_mechanics=criteria.avoid_mechanics,
        require_theme_tags=None,
        nonlands_only=True,
        limit=400,
    )
    pool = [c for c in pool if match(c)]
    pool = filter_candidates_by_price(pool, criteria, criteria.budget_usd)
    pool = filter_candidates_by_rarity(pool, criteria)
    pool = filter_candidates_by_availability(conn, pool, criteria)
    pool = _prepare_pool(
        conn,
        pool,
        partial=cards,
        commander_oracle_ids=commander_oracle_ids,
        criteria=criteria,
    )
    pick = _score_repair_pick(
        conn,
        pool,
        partial=cards,
        commander_oracle_ids=commander_oracle_ids,
        slot=victim.slot,
        criteria=criteria,
        commander_theme_tags=commander_theme_tags,
    )
    if pick is None:
        return None
    tags = fetch_card_tags(conn, [pick.oracle_id]).get(pick.oracle_id, [])
    updated = _apply_swap(cards, victim, pick, tags)
    return (
        updated,
        f"Dependency repair: replaced {victim.name} with {pick.name} ({label} support).",
    )


def _fix_aura_support(
    conn: sqlite3.Connection,
    cards: list[DeckCard],
    *,
    criteria: DeckCriteria,
    identity: list[str],
    commander_oracle_ids: set[str],
    commander_theme_tags: set[str],
) -> tuple[list[DeckCard], str] | None:
    victim = _pick_victim(cards, protect_oracle_ids=set())
    if victim is None:
        return None

    exclude_ids = _used_ids(cards) | commander_oracle_ids
    exclude_names = _used_names(cards)
    pool = fetch_candidates(
        conn,
        identity=identity,
        exclude_oracle_ids=exclude_ids,
        exclude_names=exclude_names,
        avoid_mechanics=criteria.avoid_mechanics,
        require_theme_tags=None,
        nonlands_only=True,
        limit=400,
    )
    pool = [c for c in pool if "Aura" in c.type_line]
    pool = filter_candidates_by_price(pool, criteria, criteria.budget_usd)
    pool = filter_candidates_by_rarity(pool, criteria)
    pool = filter_candidates_by_availability(conn, pool, criteria)
    pool = _prepare_pool(
        conn,
        pool,
        partial=cards,
        commander_oracle_ids=commander_oracle_ids,
        criteria=criteria,
    )
    pick = _score_repair_pick(
        conn,
        pool,
        partial=cards,
        commander_oracle_ids=commander_oracle_ids,
        slot=victim.slot,
        criteria=criteria,
        commander_theme_tags=commander_theme_tags,
    )
    if pick is None:
        return None
    tags = fetch_card_tags(conn, [pick.oracle_id]).get(pick.oracle_id, [])
    updated = _apply_swap(cards, victim, pick, tags)
    return (
        updated,
        f"Dependency repair: replaced {victim.name} with {pick.name} (Aura support).",
    )


def _attempt_repair(
    conn: sqlite3.Connection,
    cards: list[DeckCard],
    issue: DependencyIssue,
    *,
    criteria: DeckCriteria,
    identity: list[str],
    commander_oracle_ids: set[str],
    commander_theme_tags: set[str],
) -> tuple[list[DeckCard], str] | None:
    if issue.rule_id == "TUTOR_TARGET_EXISTS":
        return _fix_tutor_target(
            conn,
            cards,
            issue,
            criteria=criteria,
            identity=identity,
            commander_oracle_ids=commander_oracle_ids,
            commander_theme_tags=commander_theme_tags,
        )
    if issue.rule_id == "ENERGY_BALANCE":
        return _fix_energy_balance(
            conn,
            cards,
            issue,
            criteria=criteria,
            identity=identity,
            commander_oracle_ids=commander_oracle_ids,
            commander_theme_tags=commander_theme_tags,
        )
    if issue.rule_id == "TYPE_SYNERGY_MIN":
        return _fix_subtype_support(
            conn,
            cards,
            issue,
            criteria=criteria,
            identity=identity,
            commander_oracle_ids=commander_oracle_ids,
            commander_theme_tags=commander_theme_tags,
        )
    if issue.rule_id == "AURA_SUPPORT_MIN":
        return _fix_aura_support(
            conn,
            cards,
            criteria=criteria,
            identity=identity,
            commander_oracle_ids=commander_oracle_ids,
            commander_theme_tags=commander_theme_tags,
        )
    return None


def repair_dependency_issues(
    conn: sqlite3.Connection,
    cards: list[DeckCard],
    *,
    criteria: DeckCriteria,
    identity: list[str],
    commanders: list[dict[str, Any]],
    commander_oracle_ids: set[str],
    commander_theme_tags: set[str],
    strict: bool = False,
) -> DependencyRepairResult:
    """
    Swap cards in flex/synergy slots to resolve dependency warnings when possible.
    """
    if not card_effects_enabled(conn):
        return DependencyRepairResult(list(cards), [])

    working = list(cards)
    messages: list[str] = []
    swaps = 0

    for _ in range(MAX_REPAIR_SWAPS):
        report = validate_dependencies(
            conn,
            maindeck=working,
            commanders=commanders,
            criteria=criteria,
            strict=strict,
        )
        if report.passed:
            break
        issue = _pick_issue(report)
        if issue is None:
            break
        result = _attempt_repair(
            conn,
            working,
            issue,
            criteria=criteria,
            identity=identity,
            commander_oracle_ids=commander_oracle_ids,
            commander_theme_tags=commander_theme_tags,
        )
        if result is None:
            break
        working, msg = result
        messages.append(msg)
        swaps += 1

    return DependencyRepairResult(working, messages, swaps=swaps)
