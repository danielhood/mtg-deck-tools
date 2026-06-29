"""Deck list import facades (UX13-MVP, UX13c preview, resolver v2)."""

from __future__ import annotations

from pathlib import Path

from mtg_deck_tools.builder.commander_resolve import require_db
from mtg_deck_tools.deck_import.build import build_imported_deck_document
from mtg_deck_tools.deck_import.parse_text import parse_text_deck_list
from mtg_deck_tools.deck_import.resolve import (
    PreviewLineResult,
    ResolveCandidate,
    build_resolution_map,
    preview_resolve_parsed_deck,
    resolve_parsed_deck,
)
from mtg_deck_tools.service.dto import (
    DeckLibraryDetailResponse,
    ImportDeckPreviewCandidate,
    ImportDeckPreviewLineItem,
    ImportDeckPreviewResponse,
    ImportDeckPreviewSummary,
    ImportDeckResolution,
)
from mtg_deck_tools.service.library import require_cards_db, save_deck_to_library


def _resolution_tuples(
    resolutions: list[ImportDeckResolution] | None,
) -> list[tuple[str, int, str]]:
    return [(item.section, item.index, item.oracle_id) for item in resolutions or []]


def _preview_candidate(candidate: ResolveCandidate) -> ImportDeckPreviewCandidate:
    return ImportDeckPreviewCandidate(
        oracle_id=candidate.oracle_id,
        name=candidate.name,
        type_line=candidate.type_line or None,
        score=candidate.score,
    )


def _preview_line_item(line: PreviewLineResult) -> ImportDeckPreviewLineItem:
    return ImportDeckPreviewLineItem(
        input_name=line.input_name,
        status=line.status,
        line_number=line.line_number,
        quantity=line.quantity,
        name=line.name,
        oracle_id=line.oracle_id,
        match_method=line.match_method,
        candidates=[_preview_candidate(candidate) for candidate in line.candidates],
    )


def _preview_summary(
    commanders: list[PreviewLineResult],
    maindeck: list[PreviewLineResult],
) -> ImportDeckPreviewSummary:
    lines = [*commanders, *maindeck]
    unknown_count = sum(1 for line in lines if line.status == "unknown")
    ambiguous_count = sum(1 for line in lines if line.status == "ambiguous")
    resolved_count = sum(1 for line in lines if line.status == "resolved")
    return ImportDeckPreviewSummary(
        commander_count=len(commanders),
        maindeck_line_count=len(maindeck),
        resolved_count=resolved_count,
        unknown_count=unknown_count,
        ambiguous_count=ambiguous_count,
        ready=unknown_count == 0 and ambiguous_count == 0,
    )


def preview_deck_import(
    text: str,
    *,
    commander_names: list[str] | None = None,
    resolutions: list[ImportDeckResolution] | None = None,
    db_path: Path | None = None,
) -> ImportDeckPreviewResponse:
    """Parse and resolve a plain-text deck list without saving."""
    require_cards_db(db_path)
    parsed = parse_text_deck_list(text)
    commanders = parsed.commanders or list(commander_names or [])
    if not commanders:
        raise ValueError("Commander required: add a Commander section or pass --commander.")

    conn = require_db(require_cards_db(db_path))
    try:
        preview = preview_resolve_parsed_deck(
            conn,
            parsed,
            commander_names=commanders,
            resolutions=build_resolution_map(_resolution_tuples(resolutions)),
        )
    finally:
        conn.close()

    return ImportDeckPreviewResponse(
        commanders=[_preview_line_item(line) for line in preview.commanders],
        maindeck=[_preview_line_item(line) for line in preview.maindeck],
        summary=_preview_summary(preview.commanders, preview.maindeck),
    )


def import_deck_from_text(
    text: str,
    *,
    name: str | None = None,
    commander_names: list[str] | None = None,
    resolutions: list[ImportDeckResolution] | None = None,
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
        resolved = resolve_parsed_deck(
            conn,
            parsed,
            commander_names=commanders,
            resolutions=build_resolution_map(_resolution_tuples(resolutions)),
        )
        deck = build_imported_deck_document(conn, resolved)
    finally:
        conn.close()

    return save_deck_to_library(deck, name=name, decks_path=decks_path)
