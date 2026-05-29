"""Archetype theme choices for the wizard (distinct from slot-filler tags)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mtg_deck_tools.paths import TAXONOMY_PATH
from mtg_deck_tools.tags.tagger import TagDefinition, load_taxonomy
from mtg_deck_tools.wizard.slots import SLOT_FILLER_THEME_TAGS


@dataclass(frozen=True)
class ArchetypeChoice:
    id: str
    description: str


def archetype_choices(taxonomy_path: Path | None = None) -> list[ArchetypeChoice]:
    """Theme-layer taxonomy tags offered in wizard step 1 (excludes slot-filler tags)."""
    tags = load_taxonomy(taxonomy_path or TAXONOMY_PATH)
    choices: list[ArchetypeChoice] = []
    for tag in tags:
        if tag.layer != "theme":
            continue
        if tag.id in SLOT_FILLER_THEME_TAGS:
            continue
        choices.append(ArchetypeChoice(id=tag.id, description=tag.description))
    return sorted(choices, key=lambda c: c.id)
