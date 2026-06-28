"""Saved deck library HTTP routes (UX7f)."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from mtg_deck_tools.service.dto import (
    DeckLibraryDetailResponse,
    DeckLibraryEntry,
    ImportDeckPreviewResponse,
    ImportDeckRequest,
    PatchDeckRequest,
    RefillSlotRequest,
    SwapCardsRequest,
    SwapCardsResponse,
    SwapPlaybooksResponse,
    SwapPreviewResponse,
)
from mtg_deck_tools.service.deck_import import import_deck_from_text, preview_deck_import
from mtg_deck_tools.service.iterate import (
    DeckValidationFailure,
    preview_library_deck_swap,
    refill_library_deck_slot,
    swap_library_deck_cards,
    swap_playbooks_for_rule,
)
from mtg_deck_tools.service.library import (
    delete_library_deck,
    get_library_deck,
    list_library_decks,
    patch_library_deck,
    require_cards_db,
)

router = APIRouter(prefix="/api/v1/decks", tags=["library"])


def _validation_http_error(exc: DeckValidationFailure) -> HTTPException:
    return HTTPException(
        status_code=400,
        detail={
            "message": str(exc),
            "validation_errors": exc.validation_errors,
        },
    )


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


@router.post("/import", response_model=DeckLibraryDetailResponse)
def import_deck(
    body: ImportDeckRequest,
    db: Annotated[str | None, Query(description="SQLite database path")] = None,
    decks: Annotated[str | None, Query(description="Saved deck library path")] = None,
) -> DeckLibraryDetailResponse:
    _db_gate(Path(db) if db else None)
    if not body.text.strip():
        raise HTTPException(status_code=400, detail="text must not be empty")
    try:
        return import_deck_from_text(
            body.text,
            name=body.name,
            commander_names=body.commanders,
            db_path=Path(db) if db else None,
            decks_path=Path(decks) if decks else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/import/preview", response_model=ImportDeckPreviewResponse)
def preview_deck_import_route(
    body: ImportDeckRequest,
    db: Annotated[str | None, Query(description="SQLite database path")] = None,
) -> ImportDeckPreviewResponse:
    _db_gate(Path(db) if db else None)
    if not body.text.strip():
        raise HTTPException(status_code=400, detail="text must not be empty")
    try:
        return preview_deck_import(
            body.text,
            commander_names=body.commanders,
            db_path=Path(db) if db else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


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


@router.post("/{deck_id}/refill-slot", response_model=DeckLibraryDetailResponse)
def refill_deck_slot(
    deck_id: str,
    body: RefillSlotRequest,
    db: Annotated[str | None, Query(description="SQLite database path")] = None,
    decks: Annotated[str | None, Query(description="Saved deck library path")] = None,
) -> DeckLibraryDetailResponse:
    _db_gate(Path(db) if db else None)
    try:
        record = refill_library_deck_slot(
            deck_id,
            body,
            db_path=Path(db) if db else None,
            decks_path=Path(decks) if decks else None,
        )
    except DeckValidationFailure as exc:
        raise _validation_http_error(exc) from exc
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if record is None:
        raise HTTPException(status_code=404, detail=f"Deck not found: {deck_id}")
    return record


@router.post("/{deck_id}/swap", response_model=SwapCardsResponse)
def swap_deck_cards_route(
    deck_id: str,
    body: SwapCardsRequest,
    db: Annotated[str | None, Query(description="SQLite database path")] = None,
    decks: Annotated[str | None, Query(description="Saved deck library path")] = None,
) -> SwapCardsResponse:
    _db_gate(Path(db) if db else None)
    if not body.oracle_ids:
        raise HTTPException(status_code=400, detail="oracle_ids must not be empty.")
    try:
        record = swap_library_deck_cards(
            deck_id,
            body,
            db_path=Path(db) if db else None,
            decks_path=Path(decks) if decks else None,
        )
    except DeckValidationFailure as exc:
        raise _validation_http_error(exc) from exc
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if record is None:
        raise HTTPException(status_code=404, detail=f"Deck not found: {deck_id}")
    return record


@router.post("/{deck_id}/swap/preview", response_model=SwapPreviewResponse)
def preview_deck_swap(
    deck_id: str,
    body: SwapCardsRequest,
    db: Annotated[str | None, Query(description="SQLite database path")] = None,
    decks: Annotated[str | None, Query(description="Saved deck library path")] = None,
) -> SwapPreviewResponse:
    _db_gate(Path(db) if db else None)
    if not body.oracle_ids:
        raise HTTPException(status_code=400, detail="oracle_ids must not be empty.")
    try:
        record = preview_library_deck_swap(
            deck_id,
            body,
            db_path=Path(db) if db else None,
            decks_path=Path(decks) if decks else None,
        )
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if record is None:
        raise HTTPException(status_code=404, detail=f"Deck not found: {deck_id}")
    return record


@router.get("/swap-playbooks/{rule_id}", response_model=SwapPlaybooksResponse)
def get_swap_playbooks(
    rule_id: str,
    deficit: Annotated[str | None, Query(description="Issue detail.deficit filter")] = None,
) -> SwapPlaybooksResponse:
    return swap_playbooks_for_rule(rule_id, deficit=deficit)
