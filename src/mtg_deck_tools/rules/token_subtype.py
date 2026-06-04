"""Token subtype produce/buff pairing (Priority 8)."""

from __future__ import annotations

from collections import Counter
from typing import Any

from mtg_deck_tools.builder.deck import DeckCard
from mtg_deck_tools.rules.dependencies import (
    CardEffectRow,
    DependencyIssue,
    DependencyReport,
    ProfileSummary,
    load_profile_defaults,
)
from mtg_deck_tools.rules.dependency_scope import DependencyScope

RULE_TOKEN_SUBTYPE_BUFF_SUPPORT = "TOKEN_SUBTYPE_BUFF_SUPPORT"

GENERIC_TOKEN_PAYOFF_SOURCES = frozenset(
    {
        "token_payoff_on_create",
        "token_payoff_on_enter",
        "token_payoff_for_each",
        "token_payoff_tokens_you_control",
    }
)


def token_profile_subtype_floors(
    profiles: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return dict((profiles or load_profile_defaults()).get("tokens", {}))


def _effect_subtypes(effect: CardEffectRow) -> list[str]:
    raw = effect.payload.get("subtypes") or []
    return [str(s) for s in raw if s]


def aggregate_token_produce_subtypes(
    effects_map: dict[str, list[CardEffectRow]],
    cards: list[DeckCard],
) -> Counter[str]:
    counts: Counter[str] = Counter()
    for card in cards:
        subtypes: set[str] = set()
        for effect in effects_map.get(card.oracle_id, []):
            if effect.effect_kind != "token_produce":
                continue
            subtypes.update(_effect_subtypes(effect))
        for subtype in subtypes:
            counts[subtype] += 1
    return counts


def aggregate_token_buff_subtypes(
    effects_map: dict[str, list[CardEffectRow]],
    cards: list[DeckCard],
) -> set[str]:
    buffs: set[str] = set()
    for card in cards:
        for effect in effects_map.get(card.oracle_id, []):
            if effect.effect_kind != "token_buff_subtype":
                continue
            buffs.update(_effect_subtypes(effect))
    return buffs


def deck_has_generic_token_payoff(
    effects_map: dict[str, list[CardEffectRow]],
    cards: list[DeckCard],
) -> bool:
    for card in cards:
        for effect in effects_map.get(card.oracle_id, []):
            if effect.effect_kind != "token_payoff":
                continue
            if effect.source in GENERIC_TOKEN_PAYOFF_SOURCES:
                return True
    return False


def first_missing_subtype_buff(
    *,
    produce_counts: Counter[str],
    buff_subtypes: set[str],
    producer_min: int,
    generic_payoff: bool,
) -> str | None:
    if generic_payoff or not produce_counts:
        return None
    for subtype, count in produce_counts.most_common():
        if count < producer_min:
            continue
        if subtype not in buff_subtypes:
            return subtype
    return None


def _should_check_token_subtype_buff(
    *,
    scope: DependencyScope,
    produce_counts: Counter[str],
    producer_min: int,
) -> bool:
    if scope.tokens_user_intent:
        return True
    return any(count >= producer_min for count in produce_counts.values())


def append_token_subtype_balance(
    report: DependencyReport,
    *,
    scope: DependencyScope,
    maindeck: list[DeckCard],
    effects_map: dict[str, list[CardEffectRow]],
    severity: str,
    strict: bool,
    profiles: dict[str, dict[str, Any]] | None = None,
) -> None:
    cfg = token_profile_subtype_floors(profiles)
    producer_min = int(cfg.get("token_subtype_producer_min", 3))

    produce_counts = aggregate_token_produce_subtypes(effects_map, maindeck)
    buff_subtypes = aggregate_token_buff_subtypes(effects_map, maindeck)
    generic_payoff = deck_has_generic_token_payoff(effects_map, maindeck)

    missing = first_missing_subtype_buff(
        produce_counts=produce_counts,
        buff_subtypes=buff_subtypes,
        producer_min=producer_min,
        generic_payoff=generic_payoff,
    )

    check = _should_check_token_subtype_buff(
        scope=scope,
        produce_counts=produce_counts,
        producer_min=producer_min,
    )
    warn = check and missing is not None
    status = severity if strict and warn else ("warn" if warn else "pass")

    if warn and missing:
        count = produce_counts[missing]
        report.issues.append(
            DependencyIssue(
                rule_id=RULE_TOKEN_SUBTYPE_BUFF_SUPPORT,
                status=severity,
                message=(
                    f"Deck has {count} card(s) creating {missing} tokens but no "
                    f"{missing} token buff or generic token anthem "
                    f"(e.g. \"{missing} tokens you control get …\" or "
                    f"\"tokens you control get …\")."
                ),
                profile_id="tokens",
                detail={
                    "subtype": missing,
                    "producer_count": count,
                    "produce_subtypes": dict(produce_counts),
                    "buff_subtypes": sorted(buff_subtypes),
                    "generic_payoff": generic_payoff,
                },
            )
        )

    report.profiles.append(
        ProfileSummary(
            profile_id="tokens_subtype",
            counts={
                "produce_subtypes": len(produce_counts),
                "buff_subtypes": len(buff_subtypes),
            },
            status=status,
            messages=[],
        )
    )


def dominant_missing_token_buff_subtype(
    effects_map: dict[str, list[CardEffectRow]],
    cards: list[DeckCard],
    *,
    profiles: dict[str, dict[str, Any]] | None = None,
) -> str | None:
    cfg = token_profile_subtype_floors(profiles)
    producer_min = int(cfg.get("token_subtype_producer_min", 3))
    produce_counts = aggregate_token_produce_subtypes(effects_map, cards)
    buff_subtypes = aggregate_token_buff_subtypes(effects_map, cards)
    generic_payoff = deck_has_generic_token_payoff(effects_map, cards)
    return first_missing_subtype_buff(
        produce_counts=produce_counts,
        buff_subtypes=buff_subtypes,
        producer_min=producer_min,
        generic_payoff=generic_payoff,
    )


def effect_payload_matches_subtype(effect: CardEffectRow, subtype: str) -> bool:
    return subtype in _effect_subtypes(effect)
