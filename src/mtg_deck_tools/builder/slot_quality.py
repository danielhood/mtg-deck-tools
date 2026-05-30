"""Slot pool quality: graduated tag relaxation and oracle guards."""

from __future__ import annotations

import re

from mtg_deck_tools.builder.deck import slot_theme_tags
from mtg_deck_tools.builder.pool import CardCandidate
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.rules.commander import is_land_card

# Slots where an untagged pool needs oracle validation before picking.
GUARDED_SLOTS = frozenset({"ramp", "draw", "removal", "board_wipe", "wincon"})

THEMED_RELAX_SLOTS = frozenset({"draw", "removal", "wincon"})

BOARD_WIPE_ORACLE = re.compile(
    r"(?im)^(?:destroy all (?:creatures|permanents|nonland permanents|artifacts|enchantments)"
    r"|exile all (?:creatures|permanents|artifacts|enchantments)"
    r"|sacrifice all (?:creatures|permanents)"
    r"|all creatures get -[0-9]+/-[0-9]+"
    r"|deals? [0-9]+ damage to each (?:creature|player|opponent))"
)
BOARD_WIPE_FALSE_POSITIVE = re.compile(
    r"(?i)(whenever equipped|equipped creature|whenever .* deals combat damage)"
)

RAMP_ORACLE = re.compile(
    r"(?i)(\{T\}: Add \{[WUBRG]\}"
    r"|\{T\}: add \{[WUBRG]\}"
    r"|add \{[WUBRG]\}(?: to your mana pool)?"
    r"|add one mana of any color"
    r"|add two mana"
    r"|add three mana"
    r"|search your library for .{0,50} land"
    r"|put .{0,40} land .{0,30} onto the battlefield)"
)

WINCON_ORACLE = re.compile(
    r"(?i)(you win the game"
    r"|each opponent loses"
    r"|can't lose the game"
    r"|extra turns"
    r"|take an extra turn"
    r"|infect"
    r"|toxic"
    r"|deal [0-9]+ combat damage to a player"
    r"|opponents lose half their life"
    r"|each opponent mills"
    r"|loses [0-9]+ life for each"
    r"|power and toughness are each equal to)"
)

DRAW_ORACLE = re.compile(
    r"(?i)(draw a card|draw two cards|draw three cards|draw four cards|draw X cards"
    r"|draw cards equal to|draw that many cards|draw the top [0-9]+)"
)

REMOVAL_ORACLE = re.compile(
    r"(?i)((?:destroy|exile|sacrifice) target"
    r"|deals? [0-9]+ damage to (?:any )?target"
    r"|fight target creature"
    r"|target creature gets -[0-9]+/-[0-9]+)"
)
REMOVAL_ANTIPATTERN = re.compile(
    r"(?im)^(destroy all|exile all|sacrifice all|deals? [0-9]+ damage to each)"
)


def slot_relax_steps(slot: str, criteria: DeckCriteria) -> list[list[str] | None]:
    """Graduated theme-tag requirements before falling back to any legal card."""
    steps: list[list[str] | None] = []
    primary = slot_theme_tags(slot, criteria)
    if primary is not None:
        steps.append(primary)

    if slot in THEMED_RELAX_SLOTS and criteria.themes:
        themed = list(dict.fromkeys(criteria.themes))
        if primary != themed:
            steps.append(themed)

    if slot == "flex" and criteria.themes:
        steps.append(list(dict.fromkeys(criteria.themes)))

    if None not in steps:
        steps.append(None)
    return steps


def _is_mass_removal_type(type_line: str) -> bool:
    head = type_line.split("—", 1)[0]
    return any(kind in head for kind in ("Sorcery", "Instant", "Planeswalker"))


def passes_slot_oracle_guard(
    candidate: CardCandidate,
    slot: str,
    card_tags: list[str],
    *,
    archetype_themes: list[str] | None = None,
    themed_threat_fallback: bool = False,
) -> bool:
    """Return True when a candidate plausibly belongs in the slot."""
    text = candidate.oracle_text or ""
    tag_set = set(card_tags)
    type_line = candidate.type_line or ""

    if slot == "board_wipe":
        if BOARD_WIPE_FALSE_POSITIVE.search(text):
            return False
        if BOARD_WIPE_ORACLE.search(text):
            return True
        return "board_wipe" in tag_set and _is_mass_removal_type(type_line)

    if slot == "ramp":
        if is_land_card(type_line=type_line, is_basic_land=candidate.is_basic_land):
            return False
        if RAMP_ORACLE.search(text):
            return True
        return "ramp" in tag_set and not BOARD_WIPE_FALSE_POSITIVE.search(text)

    if slot == "draw":
        if RAMP_ORACLE.search(text) and not DRAW_ORACLE.search(text):
            return False
        if DRAW_ORACLE.search(text):
            return True
        return "draw" in tag_set

    if slot == "removal":
        if REMOVAL_ANTIPATTERN.search(text):
            return False
        if REMOVAL_ORACLE.search(text):
            return True
        return "removal" in tag_set

    if slot == "wincon":
        if WINCON_ORACLE.search(text):
            return True
        if "wincon" in tag_set:
            return True
        if themed_threat_fallback and archetype_themes:
            if tag_set.intersection(archetype_themes) and "Creature" in type_line:
                return candidate.cmc >= 4.0
        return False

    return True


def refine_slot_candidates(
    slot: str,
    candidates: list[CardCandidate],
    tag_map: dict[str, list[str]],
    *,
    criteria: DeckCriteria,
    require_theme_tags: list[str] | None,
) -> list[CardCandidate]:
    """Drop oracle misfits; keep pool if filtering would leave nothing."""
    if slot not in GUARDED_SLOTS or not candidates:
        return candidates

    themed_fallback = (
        slot == "wincon"
        and require_theme_tags is not None
        and require_theme_tags != [slot]
        and bool(criteria.themes)
        and criteria.themes != require_theme_tags
    )
    refined = [
        c
        for c in candidates
        if passes_slot_oracle_guard(
            c,
            slot,
            tag_map.get(c.oracle_id, []),
            archetype_themes=criteria.themes,
            themed_threat_fallback=themed_fallback,
        )
    ]
    if refined:
        return refined
    if require_theme_tags is not None:
        return []
    return candidates


def slot_oracle_score(
    candidate: CardCandidate,
    slot: str,
    card_tags: list[str],
    *,
    archetype_themes: list[str] | None = None,
) -> float:
    """Score adjustment for slot-oracle fit (used during candidate ranking)."""
    text = candidate.oracle_text or ""
    tag_set = set(card_tags)
    type_line = candidate.type_line or ""
    score = 0.0

    if slot == "board_wipe":
        if BOARD_WIPE_FALSE_POSITIVE.search(text) or "Equipment" in type_line:
            score -= 15.0
        elif BOARD_WIPE_ORACLE.search(text):
            score += 6.0
        elif "board_wipe" in tag_set and _is_mass_removal_type(type_line):
            score += 2.0
        else:
            score -= 8.0

    elif slot == "ramp":
        if is_land_card(type_line=type_line, is_basic_land=candidate.is_basic_land):
            score -= 20.0
        elif RAMP_ORACLE.search(text):
            score += 5.0
        elif "ramp" in tag_set:
            score += 1.5
        else:
            score -= 4.0

    elif slot == "draw":
        if RAMP_ORACLE.search(text) and not DRAW_ORACLE.search(text):
            score -= 8.0
        elif DRAW_ORACLE.search(text):
            score += 5.0
        elif "draw" in tag_set:
            score += 2.0
        else:
            score -= 6.0

    elif slot == "removal":
        if REMOVAL_ANTIPATTERN.search(text):
            score -= 12.0
        elif REMOVAL_ORACLE.search(text):
            score += 5.0
        elif "removal" in tag_set:
            score += 2.0
        else:
            score -= 6.0

    elif slot == "wincon":
        if WINCON_ORACLE.search(text):
            score += 6.0
        elif "wincon" in tag_set:
            score += 3.0
        elif archetype_themes and tag_set.intersection(archetype_themes) and "Creature" in type_line:
            score += 2.5 if candidate.cmc >= 4.0 else 0.5
        elif tag_set.intersection({"tokens", "aristocrats", "voltron", "landfall"}):
            score += 1.0

    elif slot == "flex" and tag_set:
        score += 1.5

    return score
