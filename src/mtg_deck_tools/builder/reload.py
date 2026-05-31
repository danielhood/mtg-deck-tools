"""Regenerate decks from saved .deck.json files."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from mtg_deck_tools.builder.deck_load import load_deck_json
from mtg_deck_tools.builder.budget_backfill import _deck_budget_spent
from mtg_deck_tools.builder.dependency_repair import repair_dependency_issues
from mtg_deck_tools.builder.dependency_scoring import card_effects_enabled
from mtg_deck_tools.builder.filler import fill_deck, refill_deck_slot
from mtg_deck_tools.builder.commander_resolve import (
    commander_theme_tags,
    fetch_commanders,
    require_db,
)
from mtg_deck_tools.builder.output import write_deck_outputs
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.paths import DEFAULT_DB_PATH, OUTPUT_DIR
from mtg_deck_tools.rules.dependencies import dependency_messages, validate_dependencies
from mtg_deck_tools.rules.validate import validate_commander_deck, validation_messages
from mtg_deck_tools.wizard.commanders import CommanderRow, combined_color_identity
from mtg_deck_tools.wizard.slots import load_slot_template_config, validate_slot_template


def _commander_rows_from_db(
    conn: sqlite3.Connection,
    *,
    criteria: DeckCriteria,
    saved_commanders: list[dict],
) -> tuple[list[dict], list[str]]:
    oracle_ids = criteria.commander_oracle_ids
    if not oracle_ids:
        oracle_ids = [c["oracle_id"] for c in saved_commanders if c.get("oracle_id")]
    if not oracle_ids:
        raise ValueError("Deck file has no commander_oracle_ids.")

    rows = fetch_commanders(conn, oracle_ids)
    if len(rows) != len(oracle_ids):
        raise RuntimeError("Commander(s) from deck file not found in database. Re-run import.")

    identity_rows = [
        {
            "oracle_id": c["oracle_id"],
            "name": c["name"],
            "type_line": c["type_line"] or "",
            "color_identity": json.loads(c["color_identity"] or "[]"),
            "partner_kind": c["partner_kind"],
            "scryfall_uri": c["scryfall_uri"],
            "image_uri": c["image_uri"],
            "price_usd": c["price_usd"],
            "price_known": bool(c["price_known"]),
            "released_at": c["released_at"],
            "mana_cost": c["mana_cost"] or "",
            "cmc": float(c["cmc"] or 0),
            "oracle_text": c["oracle_text"] or "",
            "rarity": c["rarity"],
            "power": c["power"],
            "toughness": c["toughness"],
        }
        for c in rows
    ]
    identity = combined_color_identity(
        [
            CommanderRow(
                oracle_id=r["oracle_id"],
                name=r["name"],
                color_identity=r["color_identity"],
                partner_kind=r["partner_kind"],
                edhrec_rank=None,
            )
            for r in identity_rows
        ]
    )
    return identity_rows, identity


def run_generate_from_deck(
    deck_path: Path,
    *,
    db_path: Path | None = None,
    seed: int | None = None,
    output_dir: Path | None = None,
    refill_slot: str | None = None,
    strict_budget: bool = False,
    strict_dependencies: bool = False,
    repair_dependencies: bool = False,
    prefer_available: bool = False,
) -> Path:
    """Regenerate a deck from a .deck.json file (full rebuild or single-slot refill)."""
    loaded = load_deck_json(deck_path)
    db = db_path or DEFAULT_DB_PATH
    conn = require_db(db)
    slot_config = load_slot_template_config()

    try:
        effective_seed = seed if seed is not None else loaded.criteria.seed
        working = loaded.criteria.model_copy(
            update={
                "seed": effective_seed,
                "strict_budget": strict_budget or loaded.criteria.strict_budget,
                "strict_dependencies": strict_dependencies or loaded.criteria.strict_dependencies,
                "repair_dependencies": repair_dependencies or loaded.criteria.repair_dependencies,
                "prefer_available": prefer_available or loaded.criteria.prefer_available,
            }
        )
        if not working.slot_template:
            working = working.model_copy(update={"slot_template": dict(slot_config.default)})

        slot_errors = validate_slot_template(working.slot_template, slot_config)
        if slot_errors:
            raise RuntimeError("Invalid slot template: " + "; ".join(slot_errors))

        identity_rows, identity = _commander_rows_from_db(
            conn,
            criteria=working,
            saved_commanders=loaded.commanders,
        )
        commander_ids = [r["oracle_id"] for r in identity_rows]

        output_criteria = working.model_copy(
            update={
                "commander_oracle_ids": commander_ids,
                "colors": identity,
                "seed": effective_seed,
            }
        )

        if refill_slot:
            maindeck = refill_deck_slot(
                conn,
                output_criteria,
                identity=identity,
                commander_oracle_ids=commander_ids,
                fixed_cards=loaded.cards,
                refill_slot=refill_slot,
                seed=effective_seed,
            )
        else:
            maindeck = fill_deck(
                conn,
                output_criteria,
                identity=identity,
                commander_oracle_ids=commander_ids,
                seed=effective_seed,
            )

        if output_criteria.repair_dependencies and card_effects_enabled(conn):
            repair = repair_dependency_issues(
                conn,
                maindeck.cards,
                criteria=output_criteria,
                identity=identity,
                commanders=identity_rows,
                commander_oracle_ids=set(commander_ids),
                commander_theme_tags=commander_theme_tags(conn, commander_ids),
                strict=output_criteria.strict_dependencies,
            )
            if repair.swaps:
                maindeck.cards = repair.cards
                maindeck.warnings.extend(repair.messages)
                maindeck.budget_spent = _deck_budget_spent(maindeck.cards)

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

        out_dir = output_dir or OUTPUT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        json_path, _ = write_deck_outputs(
            base_path=out_dir / "deck",
            criteria=output_criteria,
            commanders=identity_rows,
            maindeck=maindeck,
            identity=identity,
        )
        return json_path
    finally:
        conn.close()
