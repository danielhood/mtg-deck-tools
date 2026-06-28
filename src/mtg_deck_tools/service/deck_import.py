"""Deck list import facades (UX13-MVP)."""

from __future__ import annotations

from pathlib import Path

from mtg_deck_tools.builder.commander_resolve import require_db
from mtg_deck_tools.deck_import.build import build_imported_deck_document
from mtg_deck_tools.deck_import.parse_text import parse_text_deck_list
from mtg_deck_tools.deck_import.resolve import resolve_parsed_deck
from mtg_deck_tools.service.dto import DeckLibraryDetailResponse
from mtg_deck_tools.service.library import require_cards_db, save_deck_to_library


def import_deck_from_text(
    text: str,
    *,
    name: str | None = None,
    commander_names: list[str] | None = None,
    db_path: Path | None = None,
    decks_path: Path | None = None,
) -> DeckLibraryDetailResponse:
    """Parse, resolve, and save a plain-text deck list to the library."""
    require_cards_db(db_path)
    parsed = parse_text_deck_list(text)
    commanders = parsed.commanders or list(commander_names or [])
    if not commanders:
        raise ValueError("Commander required: add a Commander section or pass --commander.")

    conn = require_db(require_cards_db(db_path))
    try:
        resolved = resolve_parsed_deck(conn, parsed, commander_names=commanders)
        deck = build_imported_deck_document(conn, resolved)
    finally:
        conn.close()

    return save_deck_to_library(deck, name=name, decks_path=decks_path)
