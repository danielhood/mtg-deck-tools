"""Score card candidates within a deck slot."""

from __future__ import annotations

import re
from dataclasses import dataclass

from mtg_deck_tools.builder.pool import CardCandidate
from mtg_deck_tools.builder.slot_quality import WINCON_ORACLE, slot_oracle_score

COMMANDER_REFERENCE = re.compile(r"(?i)(your commander|command zone|legendary)")

SLOT_TARGET_CMC: dict[str, float] = {
    "ramp": 2.0,
    "draw": 3.0,
    "removal": 2.5,
    "board_wipe": 4.5,
    "synergy": 3.5,
    "wincon": 5.0,
    "flex": 3.0,
    "lands": 0.0,
}


@dataclass(frozen=True)
class ScoreWeights:
    commander_synergy: float = 3.0
    theme_overlap: float = 2.5
    include_mechanic: float = 2.0
    edhrec: float = 1.5
    curve: float = 1.0
    wincon_signal: float = 2.0
    budget: float = 1.0
    redundancy: float = 0.8


def _edhrec_score(rank: int | None) -> float:
    if rank is None:
        return 0.0
    if rank <= 500:
        return 3.0
    if rank <= 2000:
        return 2.0
    if rank <= 8000:
        return 1.0
    return 0.3


def _curve_score(cmc: float, slot: str) -> float:
    target = SLOT_TARGET_CMC.get(slot, 3.0)
    distance = abs(cmc - target)
    return max(0.0, 2.5 - distance)


def _budget_score(
    candidate: CardCandidate,
    *,
    budget_remaining: float | None,
) -> float:
    if budget_remaining is None:
        return 0.5
    if not candidate.price_known or candidate.price_usd is None:
        return 0.2
    if candidate.price_usd <= budget_remaining * 0.15:
        return 1.5
    if candidate.price_usd <= budget_remaining * 0.5:
        return 1.0
    if candidate.price_usd <= budget_remaining:
        return 0.5
    return -15.0


def score_land_budget(
    candidate: CardCandidate,
    *,
    budget_remaining: float | None,
    budget_total: float | None = None,
) -> float:
    """Strong preference for cheap nonbasic lands when a budget cap is set."""
    if candidate.is_basic_land:
        return 0.0
    if not candidate.price_known or candidate.price_usd is None:
        return -0.5

    price = candidate.price_usd
    score = 0.0

    if price <= 0.5:
        score += 3.0
    elif price <= 2.0:
        score += 2.0
    elif price <= 5.0:
        score += 0.5
    elif price <= 10.0:
        score -= 1.5
    elif price <= 25.0:
        score -= 4.0
    else:
        score -= 8.0

    if budget_remaining is not None:
        if price > budget_remaining:
            score -= 12.0
        elif budget_total and budget_total > 0:
            share = price / budget_total
            if share > 0.08:
                score -= 6.0 * share
            elif share > 0.04:
                score -= 3.0 * share

    return score


def score_candidate(
    candidate: CardCandidate,
    *,
    slot: str,
    archetype_themes: list[str],
    include_mechanics: list[str],
    commander_theme_tags: set[str],
    card_tags: list[str],
    type_counts: dict[str, int],
    budget_remaining: float | None,
    budget_usd: float | None = None,
    weights: ScoreWeights | None = None,
) -> float:
    w = weights or ScoreWeights()
    score = 0.0
    tag_set = set(card_tags)

    if archetype_themes and tag_set.intersection(archetype_themes):
        overlap = w.theme_overlap * 1.5
        if slot == "flex":
            overlap *= 1.5
        score += overlap

    if commander_theme_tags and tag_set.intersection(commander_theme_tags):
        score += w.commander_synergy

    if include_mechanics and tag_set.intersection(include_mechanics):
        score += w.include_mechanic

    if COMMANDER_REFERENCE.search(candidate.oracle_text):
        score += w.commander_synergy * 0.5

    score += w.edhrec * _edhrec_score(candidate.edhrec_rank)
    score += w.curve * _curve_score(candidate.cmc, slot)
    score += slot_oracle_score(candidate, slot, card_tags)

    if slot == "wincon" and WINCON_ORACLE.search(candidate.oracle_text):
        score += w.wincon_signal

    if slot == "wincon" and budget_usd is not None:
        if not candidate.price_known or candidate.price_usd is None:
            score -= 8.0

    score += w.budget * _budget_score(candidate, budget_remaining=budget_remaining)

    primary_type = (candidate.type_line.split("—")[0].strip().split()[-1] if candidate.type_line else "")
    if primary_type and type_counts.get(primary_type, 0) >= 8:
        score -= w.redundancy

    return score
