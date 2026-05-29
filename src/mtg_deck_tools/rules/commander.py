"""Commander deck construction helpers (CR 903, 702.124)."""

from __future__ import annotations

import re

from mtg_deck_tools.paths import NON_DECKABLE_LAYOUTS

COLOR_ORDER = ("W", "U", "B", "R", "G")


def parse_color_identity(raw: list[str] | None) -> frozenset[str]:
    if not raw:
        return frozenset()
    return frozenset(c for c in raw if c in COLOR_ORDER)


def color_identity_subset(card_identity: frozenset[str], commander_identity: frozenset[str]) -> bool:
    """True if every color in card_identity is in commander_identity (903.5c)."""
    return card_identity <= commander_identity


def is_playable_card(
    *,
    layout: str,
    lang: str,
    commander_legal: bool,
) -> bool:
    if lang != "en":
        return False
    if layout in NON_DECKABLE_LAYOUTS:
        return False
    return commander_legal


def is_commander_eligible(type_line: str, oracle_text: str) -> bool:
    """903.3 — legendary creature, vehicle, spacecraft, or explicit commander text."""
    if "Legendary" not in type_line:
        return False
    if re.search(r"\bCreature\b", type_line):
        return True
    if "Vehicle" in type_line:
        return True
    if "Spacecraft" in type_line and re.search(r"\bCreature\b", type_line):
        return True
    if oracle_text and "can be your commander" in oracle_text.lower():
        return True
    return False


def detect_partner_kind(oracle_text: str, keywords: list[str]) -> str | None:
    """Return partner variant kind if present."""
    text = (oracle_text or "").lower()
    kw_text = " ".join(keywords).lower()
    combined = f"{text} {kw_text}"
    if "choose a background" in combined:
        return "choose_a_background"
    if "doctor's companion" in combined or "doctors companion" in combined:
        return "doctors_companion"
    if re.search(r"partner with ", combined):
        return "partner_with"
    if re.search(r"partner —|partner -", combined):
        return "partner_variant"
    if re.search(r"\bpartner\b", combined):
        return "partner"
    return None
