"""Human-readable labels for mechanic taxonomy tag ids."""

from __future__ import annotations

from functools import lru_cache

from mtg_deck_tools.paths import TAXONOMY_PATH
from mtg_deck_tools.tags.tagger import TagDefinition, load_taxonomy


@lru_cache
def _taxonomy_tags() -> tuple[TagDefinition, ...]:
    return tuple(load_taxonomy(TAXONOMY_PATH))


@lru_cache
def tag_description_by_id() -> dict[str, str]:
    return {tag.id: tag.description for tag in _taxonomy_tags()}


def format_tag_display_name(tag_id: str) -> str:
    """Pretty name for a theme or mechanic tag (taxonomy description or title case)."""
    description = tag_description_by_id().get(tag_id, "").strip()
    if description:
        return description
    return tag_id.replace("_", " ").title()


def format_tag_list(tag_ids: list[str]) -> str:
    return ", ".join(format_tag_display_name(tag_id) for tag_id in tag_ids)
