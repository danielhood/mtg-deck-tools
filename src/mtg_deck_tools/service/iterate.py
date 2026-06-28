"""Deck iterate facades for library decks (UX11 + UX12)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mtg_deck_tools.builder.commander_resolve import require_db
from mtg_deck_tools.builder.deck_load import load_deck_data
from mtg_deck_tools.builder.filler import refill_deck_slot
from mtg_deck_tools.builder.iterate import SwapRecord, preview_swap_deck_cards, swap_deck_cards
from mtg_deck_tools.builder.output import build_deck_document
from mtg_deck_tools.builder.reload import _commander_rows_from_db
from mtg_deck_tools.builder.swap_playbooks import (
    constraints_for_strategy,
    default_strategy_for_rule,
    strategies_for_rule,
)
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.models.swap_constraints import SwapConstraints
from mtg_deck_tools.paths import resolve_db_path
from mtg_deck_tools.rules.dependencies import dependency_messages, validate_dependencies
from mtg_deck_tools.rules.validate import (
    ValidationResult,
    format_validation_failure,
    require_valid_deck,
    validate_commander_deck,
    validation_messages,
)
from mtg_deck_tools.service.dto import (
    DeckLibraryDetailResponse,
    RefillSlotRequest,
    SwapCardsRequest,
    SwapCardsResponse,
    SwapPlaybooksResponse,
    SwapPreviewResponse,
    SwapPreviewCandidateResponse,
    SwapPreviewPositionResponse,
    SwapRecordResponse,
    SwapStrategyResponse,
)
from mtg_deck_tools.service.library import (
    get_library_deck,
    save_deck_to_library,
)
from mtg_deck_tools.wizard.slots import load_slot_template_config, validate_slot_template


class DeckValidationFailure(Exception):
    """Raised when post-iterate validation fails and override is not set."""

    def __init__(self, result: ValidationResult):
        self.result = result
        self.validation_errors = [
            {"code": issue.rule, "message": issue.message} for issue in result.errors
        ]
        super().__init__(format_validation_failure(result))


def _effective_criteria(loaded_criteria: DeckCriteria, seed: int | None) -> DeckCriteria:
    slot_config = load_slot_template_config()
    working = loaded_criteria.model_copy(update={"seed": seed if seed is not None else loaded_criteria.seed})
    if not working.slot_template:
        working = working.model_copy(update={"slot_template": dict(slot_config.default)})
    slot_errors = validate_slot_template(working.slot_template, slot_config)
    if slot_errors:
        raise ValueError("Invalid slot template: " + "; ".join(slot_errors))
    return working


def _resolve_constraints(body: SwapCardsRequest) -> SwapConstraints | None:
    if body.constraints is not None:
        return body.constraints
    if body.strategy_id:
        return constraints_for_strategy(body.strategy_id, rule_id=body.rule_id)
    return None


def _finalize_maindeck(
    conn,
    *,
    working: DeckCriteria,
    identity_rows: list[dict],
    identity: list[str],
    commander_ids: list[str],
    maindeck,
    force_validation_override: bool = False,
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

    if not validation.passed:
        if force_validation_override:
            maindeck.warnings.append("Validation override: deck saved with errors.")
        else:
            raise DeckValidationFailure(validation)
    else:
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


def swap_playbooks_for_rule(rule_id: str, *, deficit: str | None = None) -> SwapPlaybooksResponse:
    default = default_strategy_for_rule(rule_id, deficit=deficit)
    default_id = default.get("id") if default else None
    strategies = [
        SwapStrategyResponse(
            id=strategy["id"],
            label=str(strategy.get("label") or strategy["id"]),
            default=strategy.get("id") == default_id,
        )
        for strategy in strategies_for_rule(rule_id, deficit=deficit)
    ]
    return SwapPlaybooksResponse(rule_id=rule_id, strategies=strategies)


def preview_library_deck_swap(
    deck_id: str,
    body: SwapCardsRequest,
    *,
    db_path: Path | None = None,
    decks_path: Path | None = None,
) -> SwapPreviewResponse | None:
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
        constraints = _resolve_constraints(body)
        limit = body.preview_limit or 8
        positions = preview_swap_deck_cards(
            conn,
            working,
            identity=identity,
            commander_oracle_ids=commander_ids,
            fixed_cards=loaded.cards,
            oracle_ids=body.oracle_ids,
            constraints=constraints,
            preview_limit=limit,
            seed=working.seed,
        )
    finally:
        conn.close()

    return SwapPreviewResponse(
        candidates_by_position=[
            SwapPreviewPositionResponse(
                from_oracle_id=position.from_oracle_id,
                from_name=position.from_name,
                slot=position.slot,
                candidates=[
                    SwapPreviewCandidateResponse(
                        oracle_id=candidate.oracle_id,
                        name=candidate.name,
                        mana_cost=candidate.mana_cost,
                        price_usd=candidate.price_usd,
                        rarity=candidate.rarity,
                    )
                    for candidate in position.candidates
                ],
            )
            for position in positions
        ]
    )


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
            force_validation_override=body.force_validation_override,
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
        constraints = _resolve_constraints(body)

        maindeck, swaps = swap_deck_cards(
            conn,
            working,
            identity=identity,
            commander_oracle_ids=commander_ids,
            fixed_cards=loaded.cards,
            oracle_ids=body.oracle_ids,
            seed=working.seed,
            constraints=constraints,
            preferred_replacements=body.preferred_replacements or None,
        )
        deck_doc = _finalize_maindeck(
            conn,
            working=working,
            identity_rows=identity_rows,
            identity=identity,
            commander_ids=commander_ids,
            maindeck=maindeck,
            force_validation_override=body.force_validation_override,
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
