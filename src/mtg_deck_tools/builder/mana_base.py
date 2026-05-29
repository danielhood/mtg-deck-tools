"""Dynamic mana base: land count heuristic and pip-aware land mix."""

from __future__ import annotations

import re
from dataclasses import dataclass

from mtg_deck_tools.builder.pool import CardCandidate
LAND_RAMP_ORACLE = re.compile(r"(?i)search your library for .{0,60} land")
MANA_ROCK_TYPES = ("Artifact",)
COLORED_MANA = re.compile(r"\{([WUBRG])\}")

DEFAULT_MIN_LANDS = 30
DEFAULT_MAX_LANDS = 40
COMMANDER_DECK_SIZE = 99

BASIC_NAME_BY_COLOR = {
    "W": "Plains",
    "U": "Island",
    "B": "Swamp",
    "R": "Mountain",
    "G": "Forest",
}


@dataclass(frozen=True)
class RampBreakdown:
    total: int
    mana_rocks: int
    land_ramp: int
    other: int
    effective_reduction: float


@dataclass(frozen=True)
class ManaBasePlan:
    """Computed mana base targets before filling the lands slot."""

    template_lands: int
    suggested_lands: int
    actual_lands: int
    nonland_count: int
    ramp: RampBreakdown
    avg_cmc_nonland: float
    num_colors: int
    pip_weights: dict[str, int]
    nonbasic_target: int
    basic_target: int
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class ManaSourceCounts:
    """Per-color mana source tally for validation."""

    basics: dict[str, int]
    nonbasic_lands: dict[str, int]
    ramp: dict[str, int]
    nonland_producers: dict[str, int]


def parse_pips_from_cost(mana_cost: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for color in COLORED_MANA.findall(mana_cost or ""):
        counts[color] = counts.get(color, 0) + 1
    return counts


def compute_pip_weights(
    cards: list,
    identity: list[str],
) -> dict[str, int]:
    """Colored mana pip demand across the maindeck nonlands."""

    def is_nonland(card: object) -> bool:
        return "Land" not in getattr(card, "type_line", "")

    weights = {color: 1 for color in identity}
    for card in cards:
        if not is_nonland(card):
            continue
        qty = getattr(card, "quantity", 1)
        for color, count in parse_pips_from_cost(getattr(card, "mana_cost", "")).items():
            if color in weights:
                weights[color] += count * qty
    return weights


def _avg_cmc_nonland(cards: list) -> float:
    nonlands = [c for c in cards if "Land" not in getattr(c, "type_line", "")]
    if not nonlands:
        return 3.0
    total = sum(getattr(c, "cmc", 0) * getattr(c, "quantity", 1) for c in nonlands)
    count = sum(getattr(c, "quantity", 1) for c in nonlands)
    return total / count if count else 3.0


def analyze_ramp_cards(cards: list) -> RampBreakdown:
    """Classify ramp pieces already in the deck (typically ramp slot)."""
    ramp_cards = [c for c in cards if getattr(c, "slot", None) == "ramp"]
    mana_rocks = 0
    land_ramp = 0
    other = 0

    for card in ramp_cards:
        qty = getattr(card, "quantity", 1)
        type_line = getattr(card, "type_line", "")
        oracle_text = getattr(card, "oracle_text", "")
        tags = set(getattr(card, "mechanic_tags", []) or [])

        if "ramp" not in tags and "Land" not in type_line:
            other += qty
            continue

        per_card = qty
        if any(t in type_line for t in MANA_ROCK_TYPES) and "Land" not in type_line:
            mana_rocks += per_card
        elif LAND_RAMP_ORACLE.search(oracle_text):
            land_ramp += per_card
        else:
            other += per_card

    total = mana_rocks + land_ramp + other
    effective_reduction = (
        0.5 * mana_rocks + 0.75 * land_ramp + 0.4 * other
    )
    return RampBreakdown(
        total=total,
        mana_rocks=mana_rocks,
        land_ramp=land_ramp,
        other=other,
        effective_reduction=effective_reduction,
    )


def compute_suggested_land_count(
    *,
    nonland_count: int,
    ramp: RampBreakdown,
    avg_cmc_nonland: float,
    num_colors: int,
    min_lands: int = DEFAULT_MIN_LANDS,
    max_lands: int = DEFAULT_MAX_LANDS,
) -> int:
    """
    Heuristic from planning doc §6.

    Starts at 37, adjusts for ramp, curve, and multicolor density.
    """
    base_lands = 37.0
    adjustment = -ramp.effective_reduction
    adjustment += 0.5 * (avg_cmc_nonland - 3.0)
    adjustment += 2.0 * max(0, num_colors - 2)
    suggested = round(base_lands + adjustment)
    return max(min_lands, min(max_lands, suggested))


def nonbasic_share(num_colors: int, land_count: int) -> float:
    """More colors → higher nonbasic ratio (capped)."""
    if num_colors <= 1:
        return 0.25
    if num_colors == 2:
        return 0.45
    return min(0.72, 0.35 + 0.12 * (num_colors - 1))


def split_land_mix(
    land_count: int,
    *,
    num_colors: int,
    pip_weights: dict[str, int],
) -> tuple[int, int]:
    """Return (nonbasic_target, basic_target)."""
    if land_count <= 0:
        return 0, 0
    nb_share = nonbasic_share(num_colors, land_count)
    nonbasic_target = round(land_count * nb_share)
    nonbasic_target = max(0, min(land_count, nonbasic_target))
    if num_colors >= 2 and land_count >= 4:
        nonbasic_target = max(nonbasic_target, min(num_colors, land_count - 1))
    basic_target = land_count - nonbasic_target
    return nonbasic_target, basic_target


def allocate_basics(
    basic_target: int,
    pip_weights: dict[str, int],
    identity: list[str],
) -> list[str]:
    """Distribute basic land names by pip weights."""
    if basic_target <= 0 or not identity:
        return []

    from mtg_deck_tools.builder.filler import BASIC_NAME_BY_COLOR

    active = {c: pip_weights.get(c, 1) for c in identity}
    total_pips = sum(active.values()) or 1
    names: list[str] = []
    for color in identity:
        name = BASIC_NAME_BY_COLOR[color]
        share = max(1, round(basic_target * active[color] / total_pips))
        names.extend([name] * share)

    while len(names) < basic_target:
        color = max(identity, key=lambda c: active.get(c, 0))
        names.append(BASIC_NAME_BY_COLOR[color])
    return names[:basic_target]


def score_land_candidate(
    candidate: CardCandidate,
    *,
    pip_weights: dict[str, int],
    identity: list[str],
) -> float:
    """Prefer lands that produce colors the deck needs."""
    if candidate.is_basic_land:
        return 0.0

    produced = set(candidate.produced_mana or [])
    if not produced:
        return 0.5

    score = 0.0
    for color, weight in pip_weights.items():
        if color in produced:
            score += weight * 1.5
    if len(produced.intersection(identity)) >= 2:
        score += 2.0
    return score


def tally_mana_sources(
    *,
    identity: list[str],
    basics: list[str],
    nonbasic_candidates: list[CardCandidate],
    ramp_cards: list,
    nonland_cards: list,
) -> ManaSourceCounts:
    color_by_basic = {name: color for color, name in BASIC_NAME_BY_COLOR.items()}
    basic_counts: dict[str, int] = {c: 0 for c in identity}
    for name in basics:
        color = color_by_basic.get(name)
        if color in basic_counts:
            basic_counts[color] += 1

    nonbasic_counts: dict[str, int] = {c: 0 for c in identity}
    for land in nonbasic_candidates:
        for color in land.produced_mana or []:
            if color in nonbasic_counts:
                nonbasic_counts[color] += 1

    ramp_counts: dict[str, int] = {c: 0 for c in identity}
    for card in ramp_cards:
        text = getattr(card, "oracle_text", "") or ""
        for match in COLORED_MANA.findall(text):
            if match in ramp_counts:
                ramp_counts[match] += getattr(card, "quantity", 1)

    producer_counts: dict[str, int] = {c: 0 for c in identity}
    for card in nonland_cards:
        if "Land" in getattr(card, "type_line", ""):
            continue
        produced = getattr(card, "produced_mana", None) or []
        for color in produced:
            if color in producer_counts:
                producer_counts[color] += getattr(card, "quantity", 1)

    return ManaSourceCounts(
        basics=basic_counts,
        nonbasic_lands=nonbasic_counts,
        ramp=ramp_counts,
        nonland_producers=producer_counts,
    )


def validate_mana_sources(
    sources: ManaSourceCounts,
    identity: list[str],
    *,
    num_colors: int,
) -> list[str]:
    """Simplified checklist: enough sources per color for early turns."""
    warnings: list[str] = []
    min_sources = 3 if num_colors <= 2 else 4

    for color in identity:
        total = (
            sources.basics.get(color, 0)
            + sources.nonbasic_lands.get(color, 0)
            + sources.ramp.get(color, 0)
            + sources.nonland_producers.get(color, 0)
        )
        if total < min_sources:
            warnings.append(
                f"Mana base: {color} has ~{total} sources (target {min_sources}+ by turn 4–5)."
            )
    return warnings


def plan_mana_base(
    cards: list,
    *,
    identity: list[str],
    template_lands: int,
    min_lands: int = DEFAULT_MIN_LANDS,
    max_lands: int = DEFAULT_MAX_LANDS,
) -> ManaBasePlan:
    """Build mana base plan from filled nonland cards."""
    nonland_cards = [c for c in cards if getattr(c, "slot", None) != "lands"]
    nonland_count = sum(getattr(c, "quantity", 1) for c in nonland_cards)
    if nonland_count + template_lands == COMMANDER_DECK_SIZE:
        actual_lands = COMMANDER_DECK_SIZE - nonland_count
    else:
        actual_lands = template_lands

    ramp = analyze_ramp_cards(cards)
    avg_cmc = _avg_cmc_nonland(cards)
    num_colors = len(identity) or 1
    pip_weights = compute_pip_weights(cards, identity)
    suggested = compute_suggested_land_count(
        nonland_count=nonland_count,
        ramp=ramp,
        avg_cmc_nonland=avg_cmc,
        num_colors=num_colors,
        min_lands=min_lands,
        max_lands=max_lands,
    )

    warnings: list[str] = []
    if actual_lands < min_lands or actual_lands > max_lands:
        warnings.append(
            f"Land count {actual_lands} is outside allowed range ({min_lands}–{max_lands})."
        )
    if suggested != actual_lands:
        warnings.append(
            f"Mana base suggested {suggested} lands based on ramp/curve/colors; "
            f"using {actual_lands} to complete the 99-card maindeck."
        )

    nonbasic_target, basic_target = split_land_mix(
        actual_lands,
        num_colors=num_colors,
        pip_weights=pip_weights,
    )

    return ManaBasePlan(
        template_lands=template_lands,
        suggested_lands=suggested,
        actual_lands=actual_lands,
        nonland_count=nonland_count,
        ramp=ramp,
        avg_cmc_nonland=round(avg_cmc, 2),
        num_colors=num_colors,
        pip_weights=pip_weights,
        nonbasic_target=nonbasic_target,
        basic_target=basic_target,
        warnings=tuple(warnings),
    )
