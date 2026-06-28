"""Plain-text deck list parser (IN-DECK-TEXT)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_SECTION_HEADERS = frozenset({"commander", "deck", "sideboard"})

_SUFFIX_QTY = re.compile(r"^(.+?)\s+x\s*(\d+)$", re.IGNORECASE)
_PREFIX_QTY_X = re.compile(r"^(\d+)x\s+(.+)$", re.IGNORECASE)
_PREFIX_QTY = re.compile(r"^(\d+)\s+(.+)$")


@dataclass(frozen=True)
class ParsedCardLine:
    name: str
    quantity: int
    line_number: int


@dataclass
class ParsedDeckList:
    commanders: list[str] = field(default_factory=list)
    maindeck: list[ParsedCardLine] = field(default_factory=list)


def parse_card_line(line: str) -> tuple[str, int]:
    """Parse a maindeck line into card name and quantity."""
    text = line.strip()
    if not text:
        raise ValueError("empty card line")

    match = _SUFFIX_QTY.match(text)
    if match:
        return match.group(1).strip(), int(match.group(2))

    match = _PREFIX_QTY_X.match(text)
    if match:
        return match.group(2).strip(), int(match.group(1))

    match = _PREFIX_QTY.match(text)
    if match:
        return match.group(2).strip(), int(match.group(1))

    return text, 1


def parse_text_deck_list(text: str) -> ParsedDeckList:
    """Parse a plain-text deck list into commander names and maindeck lines."""
    section = "deck"
    commanders: list[str] = []
    maindeck: list[ParsedCardLine] = []

    for line_number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        if line.lower() in _SECTION_HEADERS:
            section = line.lower()
            continue

        if section == "sideboard":
            continue

        if section == "commander":
            commanders.append(line)
            continue

        name, quantity = parse_card_line(line)
        if quantity < 1:
            raise ValueError(f"line {line_number}: quantity must be positive")
        maindeck.append(
            ParsedCardLine(name=name, quantity=quantity, line_number=line_number),
        )

    return ParsedDeckList(commanders=commanders, maindeck=maindeck)
