"""Equipment depth heuristics (Priority 6 — beyond artifact count)."""

from __future__ import annotations

from typing import Any

from mtg_deck_tools.builder.deck import DeckCard
from mtg_deck_tools.rules.dependencies import (
    CardEffectRow,
    DependencyIssue,
    DependencyReport,
    ProfileSummary,
)
from mtg_deck_tools.rules.dependency_profiles import equipment_profile_floors
from mtg_deck_tools.rules.dependency_scope import DependencyScope

RULE_EQUIPMENT_BALANCE = "EQUIPMENT_BALANCE"

EQUIPMENT_RULE_IDS: frozenset[str] = frozenset({RULE_EQUIPMENT_BALANCE})


def _count_equipment(cards: list[DeckCard]) -> int:
    return sum(1 for c in cards if "Equipment" in (c.type_line or ""))


def _count_carrier_creatures(cards: list[DeckCard]) -> int:
    return sum(
        1
        for c in cards
        if "Creature" in (c.type_line or "")
        and "Vehicle" not in (c.type_line or "")
    )


def collect_equipment_roles(
    effects_map: dict[str, list[CardEffectRow]],
    cards: list[DeckCard],
) -> tuple[list[str], list[str]]:
    """Return (equipment card names via type line, whenever_equipped payoff names)."""
    equipment: list[str] = []
    equip_payoffs: list[str] = []

    for card in cards:
        kinds = {e.effect_kind for e in effects_map.get(card.oracle_id, [])}
        if "type_line_equipment" in kinds or "Equipment" in (card.type_line or ""):
            equipment.append(card.name)
        if "whenever_equipped" in kinds:
            equip_payoffs.append(card.name)

    return equipment, equip_payoffs


def _deck_has_equip_payoff(effects_map: dict[str, list[CardEffectRow]]) -> bool:
    for effects in effects_map.values():
        if any(e.effect_kind == "whenever_equipped" for e in effects):
            return True
    return False


def _should_check_equipment_balance(
    *,
    scope: DependencyScope,
    equipment_count: int,
    effects_map: dict[str, list[CardEffectRow]],
) -> bool:
    if scope.equipment_user_intent:
        return True
    if equipment_count == 0:
        return False
    if _deck_has_equip_payoff(effects_map):
        return True
    return equipment_count >= 2


def _should_warn_equip_payoff_imbalance(
    *,
    scope: DependencyScope,
    equip_payoff_count: int,
    equipment_count: int,
) -> bool:
    if equip_payoff_count == 0:
        return False
    if equipment_count > 0:
        return False
    if scope.equipment_user_intent:
        return True
    return equip_payoff_count >= 2


def append_equipment_balance(
    report: DependencyReport,
    *,
    scope: DependencyScope,
    maindeck: list[DeckCard],
    effects_map: dict[str, list[CardEffectRow]],
    severity: str,
    strict: bool,
    profiles: dict[str, dict[str, Any]] | None = None,
) -> None:
    """Append EQUIPMENT_BALANCE issues and profile summary."""
    equipment_count = _count_equipment(maindeck)
    carrier_count = _count_carrier_creatures(maindeck)
    equipment_cards, equip_payoffs = collect_equipment_roles(effects_map, maindeck)
    equipment_min, carrier_min = equipment_profile_floors(profiles)

    check = _should_check_equipment_balance(
        scope=scope,
        equipment_count=equipment_count,
        effects_map=effects_map,
    )
    equip_payoff_warn = _should_warn_equip_payoff_imbalance(
        scope=scope,
        equip_payoff_count=len(equip_payoffs),
        equipment_count=equipment_count,
    )

    status = "pass"
    messages: list[str] = []

    if equip_payoff_warn:
        status = severity
        msg = (
            f"Deck has {len(equip_payoffs)} \"whenever equipped\" payoff(s) "
            f"({', '.join(equip_payoffs[:5])}"
            f"{', …' if len(equip_payoffs) > 5 else ''}) but no Equipment cards."
        )
        messages.append(msg)
        report.issues.append(
            DependencyIssue(
                rule_id=RULE_EQUIPMENT_BALANCE,
                status=severity,
                message=msg,
                profile_id="equipment",
                    detail={
                        "equipment": equipment_count,
                        "carriers": carrier_count,
                        "equip_payoffs": equip_payoffs,
                        "equipment_cards": equipment_cards,
                        "deficit": "equipment",
                    },
            )
        )
    elif check:
        if equipment_count < equipment_min:
            status = severity
            msg = (
                f"Only {equipment_count} Equipment card(s) in the deck "
                f"(suggested minimum {equipment_min} for equipment support)."
            )
            messages.append(msg)
            report.issues.append(
                DependencyIssue(
                    rule_id=RULE_EQUIPMENT_BALANCE,
                    status=severity,
                    message=msg,
                    profile_id="equipment",
                    detail={
                        "equipment": equipment_count,
                        "carriers": carrier_count,
                        "equipment_minimum": equipment_min,
                        "carrier_minimum": carrier_min,
                        "equipment_cards": equipment_cards,
                        "deficit": "equipment",
                    },
                )
            )
        elif equipment_count > 0 and carrier_count < carrier_min:
            status = severity
            msg = (
                f"Only {carrier_count} creature(s) to carry Equipment "
                f"(suggested minimum {carrier_min} when running equipment)."
            )
            messages.append(msg)
            report.issues.append(
                DependencyIssue(
                    rule_id=RULE_EQUIPMENT_BALANCE,
                    status=severity,
                    message=msg,
                    profile_id="equipment",
                    detail={
                        "equipment": equipment_count,
                        "carriers": carrier_count,
                        "equipment_minimum": equipment_min,
                        "carrier_minimum": carrier_min,
                        "equipment_cards": equipment_cards,
                        "deficit": "carriers",
                    },
                )
            )

    report.profiles.append(
        ProfileSummary(
            profile_id="equipment",
            counts={
                "equipment": equipment_count,
                "carrier_creature": carrier_count,
                "equip_payoff": len(equip_payoffs),
            },
            status=status if strict and status != "pass" else ("warn" if status != "pass" else "pass"),
            messages=messages,
        )
    )
