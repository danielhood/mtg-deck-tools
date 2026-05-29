"""Keyword mechanic choices for wizard step 2."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mtg_deck_tools.paths import TAXONOMY_PATH
from mtg_deck_tools.tags.tagger import load_taxonomy

# Partner is a commander-selection concern, not an include/avoid deck filter.
WIZARD_EXCLUDED_KEYWORDS = frozenset({"partner"})


@dataclass(frozen=True)
class MechanicChoice:
    id: str
    description: str


def keyword_mechanic_choices(taxonomy_path: Path | None = None) -> list[MechanicChoice]:
    """Keyword-layer tags offered for include/avoid in wizard step 2."""
    tags = load_taxonomy(taxonomy_path or TAXONOMY_PATH)
    choices: list[MechanicChoice] = []
    for tag in tags:
        if tag.layer != "keyword":
            continue
        if tag.id in WIZARD_EXCLUDED_KEYWORDS:
            continue
        choices.append(MechanicChoice(id=tag.id, description=tag.description))
    return sorted(choices, key=lambda c: c.id)


def validate_mechanic_lists(
    include: list[str],
    avoid: list[str],
) -> list[str]:
    overlap = sorted(set(include) & set(avoid))
    if overlap:
        return [f"Cannot both include and avoid: {', '.join(overlap)}"]
    return []
