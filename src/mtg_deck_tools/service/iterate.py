"""Deck iterate facades for library decks (UX11)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mtg_deck_tools.builder.commander_resolve import require_db
from mtg_deck_tools.builder.deck_load import load_deck_data
from mtg_deck_tools.builder.filler import refill_deck_slot
from mtg_deck_tools.builder.iterate import SwapRecord, swap_deck_cards
from mtg_deck_tools.builder.output import build_deck_document
from mtg_deck_tools.builder.reload import _commander_rows_from_db
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.paths import resolve_db_path
from mtg_deck_tools.rules.dependencies import dependency_messages, validate_dependencies
from mtg_deck_tools.rules.validate import require_valid_deck, validate_commander_deck, validation_messages
from mtg_deck_tools.service.dto import (
    DeckLibraryDetailResponse,
    RefillSlotRequest,
    SwapCardsRequest,
    SwapCardsResponse,
    SwapRecordResponse,
)
from mtg_deck_tools.service.library import (
    get_library_deck,
    save_deck_to_library,
)
from mtg_deck_tools.wizard.slots import load_slot_template_config, validate_slot_template


def _effective_criteria(loaded_criteria: DeckCriteria, seed: int | None) -> DeckCriteria:
    slot_config = load_slot_template_config()
    working = loaded_criteria.model_copy(update={"seed": seed if seed is not None else loaded_criteria.seed})
    if not working.slot_template:
        working = working.model_copy(update={"slot_template": dict(slot_config.default)})
    slot_errors = validate_slot_template(working.slot_template, slot_config)
    if slot_errors:
        raise ValueError("Invalid slot template: " + "; ".join(slot_errors))
    return working


def _finalize_maindeck(
    conn,
    *,
    working: DeckCriteria,
    identity_rows: list[dict],
    identity: list[str],
    commander_ids: list[str],
    maindeck,
) -> dict[str, Any]:
    output_criteria = working.model_copy(
        update={
            "commander_oracle_ids": commander_ids,
            "colors": identity,
        }
    )

    validation = validate_commander_deck(
        conn,
        commanders=identity_rows,
        maindeck=maindeck.cards,
        identity=identity,
        budget_usd=output_criteria.budget_usd,
        budget_spent=maindeck.budget_spent,
        unpriced_count=len(maindeck.unpriced_names),
    )
    maindeck.validation = validation
    maindeck.warnings.extend(validation_messages(validation))

    maindeck.dependency_report = validate_dependencies(
        conn,
        maindeck=maindeck.cards,
        commanders=identity_rows,
        criteria=output_criteria,
        strict=output_criteria.strict_dependencies,
    )
    maindeck.warnings.extend(dependency_messages(maindeck.dependency_report))

    require_valid_deck(validation)

    return build_deck_document(
        criteria=output_criteria,
        commanders=identity_rows,
        maindeck=maindeck,
        identity=identity,
    )


def _swap_records_to_response(records: list[SwapRecord]) -> list[SwapRecordResponse]:
    return [
        SwapRecordResponse(
            slot=r.slot,
            from_oracle_id=r.from_oracle_id,
            from_name=r.from_name,
            to_oracle_id=r.to_oracle_id,
            to_name=r.to_name,
        )
        for r in records
    ]


def refill_library_deck_slot(
    deck_id: str,
    body: RefillSlotRequest,
    *,
    db_path: Path | None = None,
    decks_path: Path | None = None,
) -> DeckLibraryDetailResponse | None:
    record = get_library_deck(deck_id, decks_path=decks_path)
    if record is None:
        return None

    loaded = load_deck_data(record.deck)
    db = resolve_db_path(db_path)
    conn = require_db(db)

    try:
        working = _effective_criteria(loaded.criteria, body.seed)
        identity_rows, identity = _commander_rows_from_db(
            conn,
            criteria=working,
            saved_commanders=loaded.commanders,
        )
        commander_ids = [r["oracle_id"] for r in identity_rows]

        maindeck = refill_deck_slot(
            conn,
            working,
            identity=identity,
            commander_oracle_ids=commander_ids,
            fixed_cards=loaded.cards,
            refill_slot=body.slot,
            seed=working.seed,
        )
        deck_doc = _finalize_maindeck(
            conn,
            working=working,
            identity_rows=identity_rows,
            identity=identity,
            commander_ids=commander_ids,
            maindeck=maindeck,
        )
    finally:
        conn.close()

    return save_deck_to_library(
        deck_doc,
        deck_id=deck_id,
        name=record.name,
        decks_path=decks_path,
    )


def swap_library_deck_cards(
    deck_id: str,
    body: SwapCardsRequest,
    *,
    db_path: Path | None = None,
    decks_path: Path | None = None,
) -> SwapCardsResponse | None:
    record = get_library_deck(deck_id, decks_path=decks_path)
    if record is None:
        return None

    loaded = load_deck_data(record.deck)
    db = resolve_db_path(db_path)
    conn = require_db(db)

    try:
        working = _effective_criteria(loaded.criteria, body.seed)
        identity_rows, identity = _commander_rows_from_db(
            conn,
            criteria=working,
            saved_commanders=loaded.commanders,
        )
        commander_ids = [r["oracle_id"] for r in identity_rows]

        maindeck, swaps = swap_deck_cards(
            conn,
            working,
            identity=identity,
            commander_oracle_ids=commander_ids,
            fixed_cards=loaded.cards,
            oracle_ids=body.oracle_ids,
            seed=working.seed,
        )
        deck_doc = _finalize_maindeck(
            conn,
            working=working,
            identity_rows=identity_rows,
            identity=identity,
            commander_ids=commander_ids,
            maindeck=maindeck,
        )
    finally:
        conn.close()

    saved = save_deck_to_library(
        deck_doc,
        deck_id=deck_id,
        name=record.name,
        decks_path=decks_path,
    )
    return SwapCardsResponse(
        id=saved.id,
        deck=saved.deck,
        swaps=_swap_records_to_response(swaps),
    )
