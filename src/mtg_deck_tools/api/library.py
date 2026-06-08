"""Saved deck library HTTP routes (UX7f)."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from mtg_deck_tools.service.dto import (
    DeckLibraryDetailResponse,
    DeckLibraryEntry,
    PatchDeckRequest,
)
from mtg_deck_tools.service.library import (
    delete_library_deck,
    get_library_deck,
    list_library_decks,
    patch_library_deck,
    require_cards_db,
)

router = APIRouter(prefix="/api/v1/decks", tags=["library"])


def _db_gate(db: Path | None) -> None:
    try:
        require_cards_db(db)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("", response_model=list[DeckLibraryEntry])
def list_decks(
    q: Annotated[str | None, Query(description="Search name, commander, or themes")] = None,
    sort: Annotated[str, Query(description="saved_at, name, or commander")] = "saved_at",
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    db: Annotated[str | None, Query(description="SQLite database path")] = None,
    decks: Annotated[str | None, Query(description="Saved deck library path")] = None,
) -> list[DeckLibraryEntry]:
    _db_gate(Path(db) if db else None)
    if sort not in {"saved_at", "name", "commander"}:
        raise HTTPException(status_code=400, detail=f"Unsupported sort: {sort}")
    return list_library_decks(
        q=q,
        sort=sort,
        limit=limit,
        decks_path=Path(decks) if decks else None,
    )


@router.get("/{deck_id}", response_model=DeckLibraryDetailResponse)
def get_deck(
    deck_id: str,
    db: Annotated[str | None, Query(description="SQLite database path")] = None,
    decks: Annotated[str | None, Query(description="Saved deck library path")] = None,
) -> DeckLibraryDetailResponse:
    _db_gate(Path(db) if db else None)
    record = get_library_deck(deck_id, decks_path=Path(decks) if decks else None)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Deck not found: {deck_id}")
    return record


@router.patch("/{deck_id}", response_model=DeckLibraryDetailResponse)
def patch_deck(
    deck_id: str,
    body: PatchDeckRequest,
    db: Annotated[str | None, Query(description="SQLite database path")] = None,
    decks: Annotated[str | None, Query(description="Saved deck library path")] = None,
) -> DeckLibraryDetailResponse:
    _db_gate(Path(db) if db else None)
    try:
        record = patch_library_deck(
            deck_id,
            body,
            decks_path=Path(decks) if decks else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if record is None:
        raise HTTPException(status_code=404, detail=f"Deck not found: {deck_id}")
    return record


@router.delete("/{deck_id}", status_code=204)
def delete_deck(
    deck_id: str,
    db: Annotated[str | None, Query(description="SQLite database path")] = None,
    decks: Annotated[str | None, Query(description="Saved deck library path")] = None,
) -> None:
    _db_gate(Path(db) if db else None)
    deleted = delete_library_deck(deck_id, decks_path=Path(decks) if decks else None)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Deck not found: {deck_id}")
