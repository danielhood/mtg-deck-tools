"""Full deck generation entry point."""

from __future__ import annotations

import json
import random
import sqlite3
from pathlib import Path

from mtg_deck_tools.builder.budget_backfill import _deck_budget_spent
from mtg_deck_tools.builder.dependency_repair import repair_dependency_issues
from mtg_deck_tools.builder.dependency_scoring import card_effects_enabled
from mtg_deck_tools.builder.filler import fill_deck
from mtg_deck_tools.builder.output import write_deck_outputs
from mtg_deck_tools.rules.dependencies import dependency_messages, validate_dependencies
from mtg_deck_tools.rules.validate import validate_commander_deck, validation_messages
from mtg_deck_tools.db.connection import connect
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.paths import DEFAULT_DB_PATH, OUTPUT_DIR
from mtg_deck_tools.wizard.commanders import CommanderRow, combined_color_identity
from mtg_deck_tools.wizard.slots import load_slot_template_config, validate_slot_template


def _require_db(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        raise FileNotFoundError(
            f"Database not found at {db_path}. Run: mtg-deck-tools import"
        )
    return connect(db_path)


def _fetch_commanders(
    conn: sqlite3.Connection,
    oracle_ids: list[str],
) -> list[sqlite3.Row]:
    if not oracle_ids:
        return []
    placeholders = ",".join("?" * len(oracle_ids))
    rows = conn.execute(
        f"""
        SELECT oracle_id, name, type_line, color_identity, partner_kind, scryfall_uri, image_uri,
               price_usd, price_known, released_at, mana_cost, cmc, oracle_text, rarity, power,
               toughness
        FROM cards
        WHERE commander_eligible = 1 AND oracle_id IN ({placeholders})
        """,
        oracle_ids,
    ).fetchall()
    by_id = {row["oracle_id"]: row for row in rows}
    return [by_id[oid] for oid in oracle_ids if oid in by_id]


def _commander_theme_tags(
    conn: sqlite3.Connection,
    commander_oracle_ids: list[str],
) -> set[str]:
    if not commander_oracle_ids:
        return set()
    placeholders = ",".join("?" * len(commander_oracle_ids))
    rows = conn.execute(
        f"""
        SELECT tag FROM card_mechanic_tags
        WHERE oracle_id IN ({placeholders})
        """,
        commander_oracle_ids,
    ).fetchall()
    return {row["tag"] for row in rows}


def _pick_commander(
    conn: sqlite3.Connection,
    rng: random.Random,
    *,
    color_filter: list[str],
    commander_ids: list[str],
) -> list[sqlite3.Row]:
    if commander_ids:
        commanders = _fetch_commanders(conn, commander_ids)
        if not commanders:
            raise RuntimeError("Selected commander(s) not found in database. Re-run import.")
        return commanders

    commander_sql = """
        SELECT oracle_id, name, type_line, color_identity, partner_kind, scryfall_uri, image_uri,
               price_usd, price_known, released_at, mana_cost, cmc, oracle_text, rarity, power,
               toughness
        FROM cards
        WHERE commander_eligible = 1
    """
    params: list = []
    for color in color_filter:
        commander_sql += " AND color_identity LIKE ?"
        params.append(f'%"{color}"%')
    commanders = conn.execute(commander_sql, params).fetchall()
    if not commanders:
        raise RuntimeError("No commanders match the given filters. Try different colors.")
    return [rng.choice(commanders)]


def run_generate(
    *,
    db_path: Path | None = None,
    seed: int | None = None,
    colors: list[str] | None = None,
    themes: list[str] | None = None,
    slot_template: dict[str, int] | None = None,
    criteria: DeckCriteria | None = None,
    output_dir: Path | None = None,
    strict_budget: bool = False,
    strict_dependencies: bool = False,
    repair_dependencies: bool = False,
    prefer_available: bool = False,
) -> Path:
    """Build a full 99-card maindeck from criteria and write output files."""
    db = db_path or DEFAULT_DB_PATH
    conn = _require_db(db)
    slot_config = load_slot_template_config()

    try:
        if criteria is not None:
            working = criteria.model_copy()
            color_filter = working.colors
            commander_ids = working.commander_oracle_ids
            effective_seed = seed if seed is not None else working.seed
        else:
            working = DeckCriteria(
                themes=themes or [],
                colors=colors or [],
                slot_template=slot_template or dict(slot_config.default),
                seed=seed,
            )
            color_filter = working.colors
            commander_ids = working.commander_oracle_ids
            effective_seed = seed

        if not working.slot_template:
            working = working.model_copy(update={"slot_template": dict(slot_config.default)})

        slot_errors = validate_slot_template(working.slot_template, slot_config)
        if slot_errors:
            raise RuntimeError("Invalid slot template: " + "; ".join(slot_errors))

        rng = random.Random(effective_seed)
        commanders = _pick_commander(
            conn,
            rng,
            color_filter=color_filter,
            commander_ids=commander_ids,
        )

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
            for c in commanders
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

        output_criteria = working.model_copy(
            update={
                "commander_oracle_ids": [c["oracle_id"] for c in commanders],
                "colors": identity,
                "seed": effective_seed,
                "strict_budget": strict_budget or working.strict_budget,
                "strict_dependencies": strict_dependencies or working.strict_dependencies,
                "repair_dependencies": repair_dependencies or working.repair_dependencies,
                "prefer_available": prefer_available or working.prefer_available,
            }
        )

        maindeck = fill_deck(
            conn,
            output_criteria,
            identity=identity,
            commander_oracle_ids=[c["oracle_id"] for c in commanders],
            seed=effective_seed,
        )

        if output_criteria.repair_dependencies and card_effects_enabled(conn):
            repair = repair_dependency_issues(
                conn,
                maindeck.cards,
                criteria=output_criteria,
                identity=identity,
                commanders=identity_rows,
                commander_oracle_ids=set(output_criteria.commander_oracle_ids),
                commander_theme_tags=_commander_theme_tags(
                    conn, output_criteria.commander_oracle_ids
                ),
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
            strict=output_criteria.strict_dependencies,
        )
        maindeck.warnings.extend(dependency_messages(maindeck.dependency_report))

        out_dir = output_dir or OUTPUT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        placeholder = out_dir / "deck"
        json_path, _ = write_deck_outputs(
            base_path=placeholder,
            criteria=output_criteria,
            commanders=identity_rows,
            maindeck=maindeck,
            identity=identity,
        )
        return json_path
    finally:
        conn.close()
