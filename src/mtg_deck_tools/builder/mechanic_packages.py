"""Ensure included mechanics (e.g. energy) meet profile floors after slot fill."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from mtg_deck_tools.builder.dependency_repair import MAX_REPAIR_SWAPS, swap_energy_card
from mtg_deck_tools.builder.dependency_scoring import card_effects_enabled
from mtg_deck_tools.builder.deck import DeckCard
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.rules.dependencies import fetch_card_effects
from mtg_deck_tools.rules.dependency_profiles import energy_profile_floors
from mtg_deck_tools.rules.dependency_scope import build_dependency_scope


@dataclass
class MechanicPackageResult:
    cards: list[DeckCard]
    messages: list[str]
    swaps: int = 0


def _energy_role_oracle_ids(
    conn: sqlite3.Connection,
    cards: list[DeckCard],
) -> tuple[set[str], set[str]]:
    effects = fetch_card_effects(conn, [c.oracle_id for c in cards])
    producers: set[str] = set()
    consumers: set[str] = set()
    for card in cards:
        for effect in effects.get(card.oracle_id, []):
            if effect.effect_kind == "energy_produce":
                producers.add(card.oracle_id)
            elif effect.effect_kind == "energy_consume":
                consumers.add(card.oracle_id)
    return producers, consumers


def count_energy_cards(
    conn: sqlite3.Connection,
    cards: list[DeckCard],
) -> tuple[int, int]:
    """Return (producer_count, consumer_count) on the maindeck."""
    if not cards:
        return 0, 0
    effects = fetch_card_effects(conn, [c.oracle_id for c in cards])
    producers = 0
    consumers = 0
    for card in cards:
        for effect in effects.get(card.oracle_id, []):
            if effect.effect_kind == "energy_produce":
                producers += 1
            elif effect.effect_kind == "energy_consume":
                consumers += 1
    return producers, consumers


def ensure_energy_package(
    conn: sqlite3.Connection,
    cards: list[DeckCard],
    *,
    criteria: DeckCriteria,
    identity: list[str],
    commander_oracle_ids: set[str],
    commander_theme_tags: set[str],
) -> MechanicPackageResult:
    """
    When the user includes energy, swap cards until profile floors are met.

    Uses ``dependency-profiles.yaml`` producer_min / consumer_min (default 2 each).
    """
    scope = build_dependency_scope(criteria)
    if not scope.energy_user_intent:
        return MechanicPackageResult(list(cards), [])

    producer_min, consumer_min = energy_profile_floors()
    working = list(cards)
    messages: list[str] = []
    swaps = 0

    for _ in range(MAX_REPAIR_SWAPS):
        producers, consumers = count_energy_cards(conn, working)
        if producers >= producer_min and consumers >= consumer_min:
            break

        if producers < producer_min:
            effect_kind = "energy_produce"
        elif consumers < consumer_min:
            effect_kind = "energy_consume"
        elif producers > 0 and consumers == 0:
            effect_kind = "energy_consume"
        elif consumers > 0 and producers == 0:
            effect_kind = "energy_produce"
        else:
            break

        producer_ids, consumer_ids = _energy_role_oracle_ids(conn, working)
        protect: set[str] = set()
        if effect_kind == "energy_produce" and len(consumer_ids) < consumer_min:
            protect = consumer_ids
        elif effect_kind == "energy_consume" and len(producer_ids) < producer_min:
            protect = producer_ids

        result = swap_energy_card(
            conn,
            working,
            effect_kind,
            criteria=criteria,
            identity=identity,
            commander_oracle_ids=commander_oracle_ids,
            commander_theme_tags=commander_theme_tags,
            protect_oracle_ids=protect,
        )
        if result is None:
            messages.append(
                f"Energy package: could not add {effect_kind.replace('_', ' ')} "
                f"(have {producers} producer(s), {consumers} consumer(s); "
                f"want ≥{producer_min} / ≥{consumer_min})."
            )
            break
        working, msg = result
        messages.append(msg.replace("Dependency repair:", "Energy package:"))
        swaps += 1

    return MechanicPackageResult(working, messages, swaps)


def ensure_included_mechanic_packages(
    conn: sqlite3.Connection,
    cards: list[DeckCard],
    *,
    criteria: DeckCriteria,
    identity: list[str],
    commander_oracle_ids: set[str],
    commander_theme_tags: set[str],
) -> MechanicPackageResult:
    """Run package passes for mechanics the user explicitly included."""
    if not card_effects_enabled(conn):
        return MechanicPackageResult(list(cards), [])

    working = list(cards)
    all_messages: list[str] = []
    total_swaps = 0

    energy_result = ensure_energy_package(
        conn,
        working,
        criteria=criteria,
        identity=identity,
        commander_oracle_ids=commander_oracle_ids,
        commander_theme_tags=commander_theme_tags,
    )
    working = energy_result.cards
    all_messages.extend(energy_result.messages)
    total_swaps += energy_result.swaps

    return MechanicPackageResult(working, all_messages, total_swaps)
