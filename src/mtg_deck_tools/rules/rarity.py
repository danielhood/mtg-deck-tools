"""Scryfall rarity ordering and minimum-rarity filtering."""

from __future__ import annotations

RARITY_ORDER: tuple[str, ...] = ("common", "uncommon", "rare", "mythic")

RARITY_RANK: dict[str, int] = {
    "common": 1,
    "uncommon": 2,
    "rare": 3,
    "mythic": 4,
    "special": 2,
    "bonus": 1,
}

RARITY_DISPLAY: dict[str, str] = {
    "common": "Common",
    "uncommon": "Uncommon",
    "rare": "Rare",
    "mythic": "Mythic",
    "special": "Special",
    "bonus": "Bonus",
}


def normalize_min_rarity(value: str) -> str:
    """Return a supported minimum rarity id."""
    normalized = value.strip().lower()
    if normalized not in RARITY_ORDER:
        allowed = ", ".join(RARITY_ORDER)
        raise ValueError(f"min_rarity must be one of: {allowed}")
    return normalized


def rarity_rank(rarity: str | None) -> int | None:
    if not rarity:
        return None
    return RARITY_RANK.get(rarity.strip().lower())


def passes_min_rarity(
    *,
    rarity: str | None,
    min_rarity: str,
    is_basic_land: bool = False,
) -> bool:
    """True when a card meets the minimum rarity threshold (basic lands always pass)."""
    if is_basic_land:
        return True
    minimum = normalize_min_rarity(min_rarity)
    if RARITY_RANK[minimum] <= RARITY_RANK["common"]:
        return True
    card_rank = rarity_rank(rarity)
    if card_rank is None:
        return False
    return card_rank >= RARITY_RANK[minimum]


def format_rarity_display(rarity: str | None) -> str:
    if not rarity:
        return "—"
    return RARITY_DISPLAY.get(rarity.strip().lower(), rarity.strip().title())


def format_min_rarity_display(min_rarity: str) -> str:
    return format_rarity_display(normalize_min_rarity(min_rarity))
