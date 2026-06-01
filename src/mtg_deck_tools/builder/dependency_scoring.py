"""Pick-time dependency scoring during slot fill (D3)."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from typing import Any

from mtg_deck_tools.builder.deck import DeckCard
from mtg_deck_tools.builder.pool import CardCandidate
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.rules.dependency_profiles import (
    artifact_spell_min,
    aura_spell_min,
    energy_profile_floors,
)
from mtg_deck_tools.rules.dependencies import (
    CardEffectRow,
    fetch_card_effects,
    load_profile_defaults,
    payload_matches_card,
)

SearchPoolEntry = tuple[str, float]  # type_line, cmc


@dataclass
class DeckBuildStats:
    """Aggregated dependency signals for the partial deck during fill."""

    energy_producers: int = 0
    energy_consumers: int = 0
    aura_spells: int = 0
    artifact_count: int = 0
    subtype_counts: dict[str, int] = field(default_factory=dict)
    needs_energy_consumer: bool = False
    needs_energy_producer: bool = False
    energy_producer_floor: int = 0
    energy_consumer_floor: int = 0
    energy_package_requested: bool = False
    aura_spell_floor: int = 0
    artifact_spell_floor: int = 0
    aura_package_requested: bool = False
    artifact_package_requested: bool = False
    needs_elf_support: bool = False
    elf_other_minimum: int = 5


def card_effects_enabled(conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='card_effects'"
    ).fetchone()
    if not row:
        return False
    count = conn.execute("SELECT COUNT(*) FROM card_effects").fetchone()[0]
    return count > 0


def _count_subtype_on_cards(cards: list[DeckCard], subtype: str) -> int:
    return sum(1 for c in cards if subtype in (c.type_line or ""))


def _count_type_on_cards(cards: list[DeckCard], card_type: str) -> int:
    needle = card_type.capitalize()
    return sum(1 for c in cards if needle in (c.type_line or ""))


def build_search_pool(
    conn: sqlite3.Connection,
    partial: list[DeckCard],
    commander_oracle_ids: set[str],
) -> list[SearchPoolEntry]:
    pool: list[SearchPoolEntry] = [(c.type_line or "", c.cmc) for c in partial]
    if not commander_oracle_ids:
        return pool
    placeholders = ",".join("?" * len(commander_oracle_ids))
    rows = conn.execute(
        f"""
        SELECT type_line, cmc FROM cards
        WHERE oracle_id IN ({placeholders})
        """,
        list(commander_oracle_ids),
    ).fetchall()
    for row in rows:
        pool.append((row["type_line"] or "", float(row["cmc"] or 0)))
    return pool


def build_deck_build_stats(
    conn: sqlite3.Connection,
    partial: list[DeckCard],
    *,
    commander_oracle_ids: set[str] | None = None,
    profiles: dict[str, dict[str, Any]] | None = None,
    criteria: DeckCriteria | None = None,
) -> DeckBuildStats:
    """Compute running stats from cards already in the partial deck."""
    profile_cfg = profiles or load_profile_defaults()
    oracle_ids = [c.oracle_id for c in partial]
    if commander_oracle_ids:
        oracle_ids.extend(oid for oid in commander_oracle_ids if oid not in oracle_ids)
    effects_map = fetch_card_effects(conn, oracle_ids) if oracle_ids else {}

    stats = DeckBuildStats(
        aura_spells=sum(1 for c in partial if "Aura" in (c.type_line or "")),
        artifact_count=_count_type_on_cards(partial, "artifact"),
    )

    for card in partial:
        for effect in effects_map.get(card.oracle_id, []):
            if effect.effect_kind == "energy_produce":
                stats.energy_producers += 1
            elif effect.effect_kind == "energy_consume":
                stats.energy_consumers += 1

    for subtype in ("Elf", "Goblin", "Zombie", "Vampire", "Dragon"):
        count = _count_subtype_on_cards(partial, subtype)
        if count:
            stats.subtype_counts[subtype] = count

    stats.needs_energy_consumer = stats.energy_producers > 0 and stats.energy_consumers == 0
    stats.needs_energy_producer = stats.energy_consumers > 0 and stats.energy_producers == 0

    if criteria is not None:
        from mtg_deck_tools.rules.dependency_scope import build_dependency_scope

        scope = build_dependency_scope(criteria)
        if scope.energy_user_intent:
            p_min, c_min = energy_profile_floors(profile_cfg)
            stats.energy_package_requested = True
            stats.energy_producer_floor = p_min
            stats.energy_consumer_floor = c_min
            if stats.energy_producers < p_min:
                stats.needs_energy_producer = True
            if stats.energy_consumers < c_min:
                stats.needs_energy_consumer = True
        if scope.aura_support_min:
            stats.aura_package_requested = True
            stats.aura_spell_floor = aura_spell_min(profile_cfg)
        if scope.artifacts_user_intent:
            stats.artifact_package_requested = True
            stats.artifact_spell_floor = artifact_spell_min(profile_cfg)

    elf_min = int(profile_cfg.get("elves", {}).get("payoff_creature_min", 5))
    stats.elf_other_minimum = elf_min
    has_elf_lord = False
    for card in partial:
        for effect in effects_map.get(card.oracle_id, []):
            if effect.effect_kind == "buff_subtype":
                subtypes = effect.payload.get("subtypes") or []
                if subtypes == ["Elf"]:
                    has_elf_lord = True
                    break
        if has_elf_lord:
            break
    if has_elf_lord:
        elves = stats.subtype_counts.get("Elf", 0)
        others = elves - 1
        stats.needs_elf_support = others < elf_min

    return stats


def count_search_targets(
    search_pool: list[SearchPoolEntry],
    payload: dict[str, Any],
) -> int:
    if payload.get("any_card"):
        return len(search_pool)
    return sum(
        1 for type_line, cmc in search_pool if payload_matches_card(type_line, cmc, payload)
    )


def dependency_pick_score(
    candidate: CardCandidate,
    candidate_effects: list[CardEffectRow],
    stats: DeckBuildStats,
    search_pool: list[SearchPoolEntry],
    *,
    weight: float = 1.0,
) -> float:
    """Additive score adjustment for a pool candidate (higher = more desirable)."""
    score = 0.0
    if stats.aura_package_requested and "Aura" in (candidate.type_line or ""):
        if stats.aura_spells < stats.aura_spell_floor:
            score += 6.0 * weight
    if stats.artifact_package_requested and "Artifact" in (candidate.type_line or ""):
        if stats.artifact_count < stats.artifact_spell_floor:
            score += 5.0 * weight

    for effect in candidate_effects or []:
        if effect.effect_kind == "energy_produce" and stats.energy_package_requested:
            if stats.energy_producers < stats.energy_producer_floor:
                score += 8.0 * weight
        elif effect.effect_kind == "energy_consume" and stats.energy_package_requested:
            if stats.energy_consumers < stats.energy_consumer_floor:
                score += 8.0 * weight
        if effect.effect_kind == "energy_consume" and stats.needs_energy_consumer:
            score += 5.0 * weight
        elif effect.effect_kind == "energy_produce" and stats.needs_energy_producer:
            score += 3.5 * weight
        elif effect.effect_kind == "energy_consume" and stats.energy_producers >= 2:
            if stats.energy_consumers < stats.energy_producers:
                score += 2.0 * weight
        elif effect.effect_kind == "search_library":
            if effect.confidence < 0.6 and effect.payload.get("any_card"):
                continue
            targets = count_search_targets(search_pool, effect.payload)
            if targets == 0:
                score -= 10.0 * weight
            else:
                score += 0.5 * weight
        elif effect.effect_kind == "buff_subtype":
            subtypes = effect.payload.get("subtypes") or []
            if subtypes == ["Elf"] and stats.needs_elf_support:
                score -= 1.0 * weight
        elif effect.effect_kind == "whenever_cast_type":
            types = effect.payload.get("types") or []
            if types == ["artifact"] and stats.artifact_count < 8:
                score += 1.5 * weight

    if stats.needs_elf_support and "Elf" in (candidate.type_line or ""):
        score += 2.5 * weight

    return score


def passes_strict_dependency_filter(
    candidate: CardCandidate,
    candidate_effects: list[CardEffectRow],
    stats: DeckBuildStats,
    search_pool: list[SearchPoolEntry],
) -> bool:
    """
    Pick-time exclusion (D4): reject candidates that would be dead or unsupported
    given the partial deck and commander search pool.
    """
    for effect in candidate_effects or []:
        if effect.effect_kind == "search_library":
            if effect.confidence < 0.6 and effect.payload.get("any_card"):
                continue
            if count_search_targets(search_pool, effect.payload) == 0:
                return False
        elif effect.effect_kind == "energy_consume" and stats.energy_producers == 0:
            return False
        elif effect.effect_kind == "buff_subtype":
            subtypes = effect.payload.get("subtypes") or []
            if subtypes == ["Elf"]:
                others = stats.subtype_counts.get("Elf", 0)
                if others < stats.elf_other_minimum:
                    return False
    return True


def filter_strict_dependency_candidates(
    candidates: list[CardCandidate],
    *,
    conn: sqlite3.Connection,
    partial: list[DeckCard],
    commander_oracle_ids: set[str],
) -> list[CardCandidate]:
    """Return candidates allowed under strict pick-time dependency rules."""
    if not candidates:
        return candidates
    deck_stats = build_deck_build_stats(
        conn,
        partial,
        commander_oracle_ids=commander_oracle_ids,
    )
    search_pool = build_search_pool(conn, partial, commander_oracle_ids)
    effect_map = fetch_card_effects(conn, [c.oracle_id for c in candidates])
    return [
        candidate
        for candidate in candidates
        if passes_strict_dependency_filter(
            candidate,
            effect_map.get(candidate.oracle_id, []),
            deck_stats,
            search_pool,
        )
    ]
