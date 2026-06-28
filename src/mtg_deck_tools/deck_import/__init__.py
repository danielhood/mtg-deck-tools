"""Import existing deck lists from text and other formats (UX13)."""

from mtg_deck_tools.deck_import.normalize import normalize_card_name
from mtg_deck_tools.deck_import.parse_text import ParsedCardLine, ParsedDeckList, parse_text_deck_list
from mtg_deck_tools.deck_import.resolve import (
    PreviewDeckResolveResult,
    PreviewLineResult,
    ResolveCandidate,
    ResolveError,
    build_resolution_map,
    preview_resolve_parsed_deck,
    resolve_parsed_deck,
)

__all__ = [
    "ParsedCardLine",
    "ParsedDeckList",
    "PreviewDeckResolveResult",
    "PreviewLineResult",
    "ResolveCandidate",
    "ResolveError",
    "build_resolution_map",
    "normalize_card_name",
    "parse_text_deck_list",
    "preview_resolve_parsed_deck",
    "resolve_parsed_deck",
]
