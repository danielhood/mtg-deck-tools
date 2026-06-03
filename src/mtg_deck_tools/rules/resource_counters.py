"""Shared produce/consume balance for player resource counters (experience, blood, +1/+1)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import sqlite3

from mtg_deck_tools.builder.deck import DeckCard
from mtg_deck_tools.rules.dependencies import (
    CardEffectRow,
    DependencyIssue,
    DependencyReport,
    ProfileSummary,
    fetch_card_effects,
    load_profile_defaults,
)
from mtg_deck_tools.rules.dependency_scope import DependencyScope


@dataclass(frozen=True)
class ResourceCounterSpec:
    """One resource counter family (mirrors energy_produce / energy_consume)."""

    profile_id: str
    rule_id: str
    produce_kind: str
    consume_kind: str
    display_name: str
    producer_label: str
    consumer_label: str


RESOURCE_COUNTER_SPECS: tuple[ResourceCounterSpec, ...] = (
    ResourceCounterSpec(
        profile_id="experience",
        rule_id="EXPERIENCE_BALANCE",
        produce_kind="experience_produce",
        consume_kind="experience_consume",
        display_name="experience",
        producer_label="experience producer(s)",
        consumer_label="cards that use experience counters",
    ),
    ResourceCounterSpec(
        profile_id="blood",
        rule_id="BLOOD_BALANCE",
        produce_kind="blood_produce",
        consume_kind="blood_consume",
        display_name="blood",
        producer_label="blood counter producer(s)",
        consumer_label="cards that care about blood counters",
    ),
    ResourceCounterSpec(
        profile_id="plus_one",
        rule_id="PLUS_ONE_BALANCE",
        produce_kind="plus_one_produce",
        consume_kind="plus_one_consume",
        display_name="+1/+1",
        producer_label="+1/+1 counter producer(s)",
        consumer_label="cards that care about +1/+1 counters",
    ),
)

RESOURCE_RULE_IDS: frozenset[str] = frozenset(s.rule_id for s in RESOURCE_COUNTER_SPECS)
RESOURCE_PROFILE_IDS: frozenset[str] = frozenset(s.profile_id for s in RESOURCE_COUNTER_SPECS)


def spec_for_rule(rule_id: str) -> ResourceCounterSpec | None:
    for spec in RESOURCE_COUNTER_SPECS:
        if spec.rule_id == rule_id:
            return spec
    return None


def resource_profile_floors(
    profile_id: str,
    profiles: dict[str, dict[str, Any]] | None = None,
) -> tuple[int, int]:
    cfg = (profiles or load_profile_defaults()).get(profile_id, {})
    return (
        int(cfg.get("producer_min", 2)),
        int(cfg.get("consumer_min", 2)),
    )


def collect_resource_roles(
    effects_map: dict[str, list[CardEffectRow]],
    maindeck: list[DeckCard],
    spec: ResourceCounterSpec,
) -> tuple[list[str], list[str]]:
    producers: list[str] = []
    consumers: list[str] = []
    for card in maindeck:
        for effect in effects_map.get(card.oracle_id, []):
            if effect.effect_kind == spec.produce_kind:
                producers.append(card.name)
            elif effect.effect_kind == spec.consume_kind:
                consumers.append(card.name)
    return producers, consumers


def count_resource_cards(
    conn: sqlite3.Connection,
    cards: list[DeckCard],
    spec: ResourceCounterSpec,
) -> tuple[int, int]:
    effects = fetch_card_effects(conn, [c.oracle_id for c in cards])
    producers = 0
    consumers = 0
    for card in cards:
        for effect in effects.get(card.oracle_id, []):
            if effect.effect_kind == spec.produce_kind:
                producers += 1
            elif effect.effect_kind == spec.consume_kind:
                consumers += 1
    return producers, consumers


def resource_role_oracle_ids(
    conn: sqlite3.Connection,
    cards: list[DeckCard],
    spec: ResourceCounterSpec,
) -> tuple[set[str], set[str]]:
    effects = fetch_card_effects(conn, [c.oracle_id for c in cards])
    producers: set[str] = set()
    consumers: set[str] = set()
    for card in cards:
        for effect in effects.get(card.oracle_id, []):
            if effect.effect_kind == spec.produce_kind:
                producers.add(card.oracle_id)
            elif effect.effect_kind == spec.consume_kind:
                consumers.add(card.oracle_id)
    return producers, consumers


def should_warn_resource_imbalance(
    *,
    scope: DependencyScope,
    profile_id: str,
    producer_count: int,
    consumer_count: int,
    profiles: dict[str, dict[str, Any]] | None = None,
) -> bool:
    if producer_count == 0 and consumer_count == 0:
        return False
    if producer_count > 0 and consumer_count > 0:
        return False
    if scope.resource_user_intent(profile_id):
        return True
    cfg = (profiles or load_profile_defaults()).get(profile_id, {})
    dominant_min = int(cfg.get("incidental_imbalance_min", 2))
    return max(producer_count, consumer_count) >= dominant_min


def append_resource_balance(
    report: DependencyReport,
    *,
    spec: ResourceCounterSpec,
    scope: DependencyScope,
    producers: list[str],
    consumers: list[str],
    severity: str,
    strict: bool,
) -> None:
    imbalanced = (producers and not consumers) or (consumers and not producers)
    warn = imbalanced and should_warn_resource_imbalance(
        scope=scope,
        profile_id=spec.profile_id,
        producer_count=len(producers),
        consumer_count=len(consumers),
    )
    if warn and producers and not consumers:
        report.issues.append(
            DependencyIssue(
                rule_id=spec.rule_id,
                status=severity,
                message=(
                    f"Deck has {len(producers)} {spec.producer_label} "
                    f"({', '.join(producers[:5])}"
                    f"{', …' if len(producers) > 5 else ''}) but no {spec.consumer_label}."
                ),
                profile_id=spec.profile_id,
                detail={"producers": producers, "consumers": []},
            )
        )
    elif warn and consumers and not producers:
        report.issues.append(
            DependencyIssue(
                rule_id=spec.rule_id,
                status=severity,
                message=(
                    f"Deck has {len(consumers)} {spec.consumer_label} but no "
                    f"{spec.producer_label}."
                ),
                profile_id=spec.profile_id,
                detail={"producers": [], "consumers": consumers},
            )
        )
    report.profiles.append(
        ProfileSummary(
            profile_id=spec.profile_id,
            counts={"producer": len(producers), "consumer": len(consumers)},
            status=severity if strict and warn else ("warn" if warn else "pass"),
            messages=[],
        )
    )
