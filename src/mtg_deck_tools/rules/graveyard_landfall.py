"""Graveyard / landfall warn-only heuristics (Priority 5)."""

from __future__ import annotations

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

RULE_REANIMATION_SUPPORT = "REANIMATION_SUPPORT"
RULE_GRAVEYARD_COST_SUPPORT = "GRAVEYARD_COST_SUPPORT"
RULE_SELF_MILL_BALANCE = "SELF_MILL_BALANCE"
RULE_LANDFALL_BALANCE = "LANDFALL_BALANCE"

GRAVEYARD_LANDFALL_RULE_IDS: frozenset[str] = frozenset(
    {
        RULE_REANIMATION_SUPPORT,
        RULE_GRAVEYARD_COST_SUPPORT,
        RULE_SELF_MILL_BALANCE,
        RULE_LANDFALL_BALANCE,
    }
)


def graveyard_profile_floors(
    profiles: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return dict((profiles or load_profile_defaults()).get("graveyard", {}))


def landfall_profile_floors(
    profiles: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return dict((profiles or load_profile_defaults()).get("landfall", {}))


def _count_creatures(cards: list[DeckCard]) -> int:
    return sum(
        1
        for c in cards
        if "Creature" in (c.type_line or "") and "Vehicle" not in (c.type_line or "")
    )


def _avg_creature_cmc(cards: list[DeckCard]) -> float:
    cmcs = [
        c.cmc
        for c in cards
        if "Creature" in (c.type_line or "") and "Vehicle" not in (c.type_line or "")
    ]
    if not cmcs:
        return 0.0
    return sum(cmcs) / len(cmcs)


def _count_nonlands(cards: list[DeckCard]) -> int:
    return sum(1 for c in cards if "Land" not in (c.type_line or ""))


def collect_graveyard_roles(
    effects_map: dict[str, list[CardEffectRow]],
    cards: list[DeckCard],
) -> tuple[list[str], list[str], list[str], list[str]]:
    """Return (reanimate, graveyard_cost, mill_enabler, graveyard_payoff) card names.

    ``mill_enabler`` includes mill, surveil, discover, and looting-style discard.
    """
    reanimate: list[str] = []
    graveyard_cost: list[str] = []
    mill_enabler: list[str] = []
    graveyard_payoff: list[str] = []

    for card in cards:
        kinds = {e.effect_kind for e in effects_map.get(card.oracle_id, [])}
        if "reanimate" in kinds:
            reanimate.append(card.name)
        if "graveyard_cost" in kinds:
            graveyard_cost.append(card.name)
        if "mill_enabler" in kinds:
            mill_enabler.append(card.name)
        if "graveyard_payoff" in kinds:
            graveyard_payoff.append(card.name)

    return reanimate, graveyard_cost, mill_enabler, graveyard_payoff


def collect_landfall_roles(
    effects_map: dict[str, list[CardEffectRow]],
    cards: list[DeckCard],
) -> tuple[list[str], list[str]]:
    """Return (landfall_payoff, land_ramp) card names."""
    landfall_payoff: list[str] = []
    land_ramp: list[str] = []

    for card in cards:
        kinds = {e.effect_kind for e in effects_map.get(card.oracle_id, [])}
        if "landfall_payoff" in kinds:
            landfall_payoff.append(card.name)
        if "land_ramp" in kinds:
            land_ramp.append(card.name)

    return landfall_payoff, land_ramp


def self_mill_balanced(mill_count: int, payoff_count: int) -> bool:
    if mill_count == 0 and payoff_count == 0:
        return True
    return mill_count > 0 and payoff_count > 0


def _should_warn_self_mill_imbalance(
    *,
    scope: DependencyScope,
    mill_count: int,
    payoff_count: int,
    dominant_min: int,
) -> bool:
    if self_mill_balanced(mill_count, payoff_count):
        return False
    return scope.graveyard_user_intent


def _should_check_landfall_balance(
    *,
    scope: DependencyScope,
    landfall_payoff_count: int,
    cfg: dict[str, Any],
) -> bool:
    return scope.landfall_user_intent


def _should_warn_reanimation_support(
    *,
    scope: DependencyScope,
    reanimate_count: int,
    reanimation_card_min: int,
) -> bool:
    if reanimate_count == 0:
        return False
    if scope.graveyard_user_intent:
        return True
    return reanimate_count >= reanimation_card_min


def append_graveyard_landfall_balance(
    report: DependencyReport,
    *,
    scope: DependencyScope,
    maindeck: list[DeckCard],
    effects_map: dict[str, list[CardEffectRow]],
    severity: str,
    strict: bool,
    profiles: dict[str, dict[str, Any]] | None = None,
) -> None:
    """Append graveyard / landfall heuristic issues and profile summaries."""
    gy_cfg = graveyard_profile_floors(profiles)
    lf_cfg = landfall_profile_floors(profiles)

    reanimate, graveyard_cost, mill_enabler, graveyard_payoff = collect_graveyard_roles(
        effects_map, maindeck
    )
    landfall_payoff, land_ramp = collect_landfall_roles(effects_map, maindeck)

    creature_count = _count_creatures(maindeck)
    avg_creature_cmc = _avg_creature_cmc(maindeck)
    nonland_count = _count_nonlands(maindeck)

    reanimation_creature_min = int(gy_cfg.get("reanimation_creature_min", 15))
    reanimation_creature_cmc_max = float(gy_cfg.get("reanimation_creature_cmc_max", 5.0))
    graveyard_cost_nonland_min = int(gy_cfg.get("graveyard_cost_nonland_min", 35))
    graveyard_cost_card_min = int(gy_cfg.get("graveyard_cost_card_min", 2))
    self_mill_dominant_min = int(gy_cfg.get("self_mill_dominant_min", 3))
    reanimation_card_min = int(gy_cfg.get("reanimation_card_min", 3))
    land_ramp_min = int(lf_cfg.get("land_ramp_min", 1))

    reanimation_status = "pass"
    reanimation_messages: list[str] = []
    if _should_warn_reanimation_support(
        scope=scope,
        reanimate_count=len(reanimate),
        reanimation_card_min=reanimation_card_min,
    ):
        low_creatures = creature_count < reanimation_creature_min
        high_cmc = avg_creature_cmc > reanimation_creature_cmc_max
        if low_creatures or high_cmc:
            reanimation_status = severity
            if low_creatures:
                msg = (
                    f"Deck has reanimation ({', '.join(reanimate[:3])}"
                    f"{', …' if len(reanimate) > 3 else ''}) but only {creature_count} "
                    f"creature(s) (suggested minimum {reanimation_creature_min} for targets "
                    f"that die)."
                )
            else:
                msg = (
                    f"Deck has reanimation ({', '.join(reanimate[:3])}"
                    f"{', …' if len(reanimate) > 3 else ''}) but average creature CMC is "
                    f"{avg_creature_cmc:.1f} (suggested max {reanimation_creature_cmc_max:.1f} "
                    f"for reanimator curves)."
                )
            reanimation_messages.append(msg)
            report.issues.append(
                DependencyIssue(
                    rule_id=RULE_REANIMATION_SUPPORT,
                    status=severity,
                    message=msg,
                    profile_id="graveyard",
                    detail={
                        "reanimate": reanimate,
                        "creatures": creature_count,
                        "avg_creature_cmc": round(avg_creature_cmc, 2),
                        "creature_minimum": reanimation_creature_min,
                        "creature_cmc_max": reanimation_creature_cmc_max,
                        "deficit": "creatures" if low_creatures else "cmc",
                    },
                )
            )
    report.profiles.append(
        ProfileSummary(
            profile_id="graveyard_reanimation",
            counts={
                "reanimate": len(reanimate),
                "creature": creature_count,
            },
            status=reanimation_status,
            messages=reanimation_messages,
        )
    )

    graveyard_cost_status = "pass"
    graveyard_cost_messages: list[str] = []
    if len(graveyard_cost) >= graveyard_cost_card_min and nonland_count < graveyard_cost_nonland_min:
        graveyard_cost_status = severity
        msg = (
            f"Deck has {len(graveyard_cost)} delve/flashback card(s) "
            f"({', '.join(graveyard_cost[:3])}"
            f"{', …' if len(graveyard_cost) > 3 else ''}) but only {nonland_count} "
            f"nonland cards (suggested minimum {graveyard_cost_nonland_min} to fill the "
            f"graveyard over time)."
        )
        graveyard_cost_messages.append(msg)
        report.issues.append(
            DependencyIssue(
                rule_id=RULE_GRAVEYARD_COST_SUPPORT,
                status=severity,
                message=msg,
                profile_id="graveyard",
                detail={
                    "graveyard_cost": graveyard_cost,
                    "nonland_count": nonland_count,
                    "nonland_minimum": graveyard_cost_nonland_min,
                },
            )
        )
    report.profiles.append(
        ProfileSummary(
            profile_id="graveyard_cost",
            counts={
                "graveyard_cost": len(graveyard_cost),
                "nonland": nonland_count,
            },
            status=graveyard_cost_status,
            messages=graveyard_cost_messages,
        )
    )

    mill_imbalanced = not self_mill_balanced(len(mill_enabler), len(graveyard_payoff))
    mill_warn = mill_imbalanced and _should_warn_self_mill_imbalance(
        scope=scope,
        mill_count=len(mill_enabler),
        payoff_count=len(graveyard_payoff),
        dominant_min=self_mill_dominant_min,
    )
    mill_status = severity if strict and mill_warn else ("warn" if mill_warn else "pass")
    if mill_warn and mill_enabler and not graveyard_payoff:
        report.issues.append(
            DependencyIssue(
                rule_id=RULE_SELF_MILL_BALANCE,
                status=severity,
                message=(
                    f"Deck has {len(mill_enabler)} mill enabler(s) "
                    f"({', '.join(mill_enabler[:3])}"
                    f"{', …' if len(mill_enabler) > 3 else ''}) but no graveyard payoffs "
                    f"(e.g. \"for each card in your graveyard\")."
                ),
                profile_id="graveyard",
                detail={"mill_enabler": mill_enabler, "graveyard_payoff": []},
            )
        )
    elif mill_warn and graveyard_payoff and not mill_enabler:
        report.issues.append(
            DependencyIssue(
                rule_id=RULE_SELF_MILL_BALANCE,
                status=severity,
                message=(
                    f"Deck has {len(graveyard_payoff)} graveyard payoff(s) but no cards "
                    f"that mill or fill your graveyard."
                ),
                profile_id="graveyard",
                detail={"mill_enabler": [], "graveyard_payoff": graveyard_payoff},
            )
        )
    report.profiles.append(
        ProfileSummary(
            profile_id="graveyard_self_mill",
            counts={
                "mill_enabler": len(mill_enabler),
                "graveyard_payoff": len(graveyard_payoff),
            },
            status=mill_status,
            messages=[],
        )
    )

    landfall_status = "pass"
    landfall_messages: list[str] = []
    check_landfall = _should_check_landfall_balance(
        scope=scope,
        landfall_payoff_count=len(landfall_payoff),
        cfg=lf_cfg,
    )
    if check_landfall and landfall_payoff and len(land_ramp) < land_ramp_min:
        landfall_status = severity
        msg = (
            f"Deck has {len(landfall_payoff)} landfall payoff(s) "
            f"({', '.join(landfall_payoff[:3])}"
            f"{', …' if len(landfall_payoff) > 3 else ''}) but only {len(land_ramp)} "
            f"land ramp spell(s) (suggested minimum {land_ramp_min})."
        )
        landfall_messages.append(msg)
        report.issues.append(
            DependencyIssue(
                rule_id=RULE_LANDFALL_BALANCE,
                status=severity,
                message=msg,
                profile_id="landfall",
                detail={
                    "landfall_payoff": landfall_payoff,
                    "land_ramp": land_ramp,
                    "land_ramp_minimum": land_ramp_min,
                },
            )
        )
    report.profiles.append(
        ProfileSummary(
            profile_id="landfall",
            counts={
                "landfall_payoff": len(landfall_payoff),
                "land_ramp": len(land_ramp),
            },
            status=landfall_status,
            messages=landfall_messages,
        )
    )
