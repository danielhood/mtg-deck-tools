"""search_library payload matching for TUTOR_TARGET_EXISTS (D2/D3)."""

from __future__ import annotations

from typing import Any

COLOR_WORD_TO_SYMBOL = {
    "white": "W",
    "blue": "U",
    "black": "B",
    "red": "R",
    "green": "G",
}


def _type_match_mode(payload: dict[str, Any]) -> str:
    explicit = payload.get("type_match")
    if explicit in ("any", "all"):
        return explicit
    types = payload.get("types") or []
    return "any" if len(types) > 1 else "all"


def _type_line_has_type(type_line: str, card_type: str) -> bool:
    tl = type_line or ""
    ct = card_type.lower()
    if ct == "land":
        return "Land" in tl
    if ct == "creature":
        return "Creature" in tl
    if ct == "artifact":
        return "Artifact" in tl
    if ct == "enchantment":
        return "Enchantment" in tl
    if ct == "planeswalker":
        return "Planeswalker" in tl
    if ct == "instant":
        return "Instant" in tl
    if ct == "sorcery":
        return "Sorcery" in tl
    return ct.capitalize() in tl


def _matches_types(type_line: str, types: list[str], mode: str) -> bool:
    if not types:
        return True
    checks = [_type_line_has_type(type_line, card_type) for card_type in types]
    return any(checks) if mode == "any" else all(checks)


def _cmc_subject_in_type_line(type_line: str, types: list[str]) -> bool:
    tl = type_line or ""
    if not types:
        return "Creature" in tl or "Planeswalker" in tl
    mode = "any" if len(types) > 1 else "all"
    return _matches_types(tl, types, mode)


def payload_matches_card(
    type_line: str,
    cmc: float,
    payload: dict[str, Any],
    *,
    colors: list[str] | None = None,
    name: str | None = None,
) -> bool:
    """Whether a card satisfies a search_library payload."""
    tl = type_line or ""
    types = payload.get("types") or []
    type_mode = _type_match_mode(payload)

    for supertype in payload.get("supertypes") or []:
        if supertype.lower() == "basic" and "Basic" in tl and "Land" in tl:
            continue
        if supertype not in tl:
            return False

    if types and not _matches_types(tl, types, type_mode):
        return False

    for subtype in payload.get("subtypes") or []:
        if subtype not in tl:
            return False

    required_colors = payload.get("colors") or []
    if required_colors:
        card_colors = list(colors or [])
        if not card_colors:
            return False
        card_set = set(card_colors)
        if not all(color in card_set for color in required_colors):
            return False

    required_name = payload.get("card_name")
    if required_name and (name or "").lower() != required_name.lower():
        return False

    if _cmc_subject_in_type_line(tl, types):
        max_cmc = payload.get("max_cmc")
        if max_cmc is not None and cmc > float(max_cmc):
            return False
        min_cmc = payload.get("min_cmc")
        if min_cmc is not None and cmc < float(min_cmc):
            return False

    return True


def describe_payload(payload: dict[str, Any]) -> str:
    if payload.get("any_card"):
        return "any card"
    parts: list[str] = []
    for supertype in payload.get("supertypes") or []:
        parts.append(supertype)
    types = payload.get("types") or []
    if types:
        joiner = " or " if _type_match_mode(payload) == "any" and len(types) > 1 else " / "
        parts.append(joiner.join(types))
    for subtype in payload.get("subtypes") or []:
        parts.append(subtype)
    for color in payload.get("colors") or []:
        parts.append(color)
    if payload.get("card_name"):
        parts.append(f"named {payload['card_name']}")
    if payload.get("max_cmc") is not None:
        parts.append(f"mana value {payload['max_cmc']} or less")
    if payload.get("min_cmc") is not None:
        parts.append(f"mana value {payload['min_cmc']} or greater")
    return " / ".join(parts) if parts else "the search criteria"
