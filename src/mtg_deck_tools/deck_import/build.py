"""Build .deck.json documents from resolved import lists."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from mtg_deck_tools.builder.budget_backfill import _deck_budget_spent
from mtg_deck_tools.builder.commander_resolve import fetch_commanders
from mtg_deck_tools.builder.deck import DeckBuildResult, DeckCard
from mtg_deck_tools.builder.output import build_deck_document
from mtg_deck_tools.builder.pool import CardCandidate, fetch_card_tags
from mtg_deck_tools.deck_import.resolve import ResolvedDeckList
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.rules.dependencies import dependency_messages, validate_dependencies
from mtg_deck_tools.rules.validate import validate_commander_deck, validation_messages
from mtg_deck_tools.wizard.commanders import CommanderRow, combined_color_identity
from mtg_deck_tools.wizard.slots import load_slot_template_config


def _deck_card_from_candidate(
    candidate: CardCandidate,
    *,
    slot: str,
    tags: list[str],
    quantity: int,
) -> DeckCard:
    return DeckCard(
        oracle_id=candidate.oracle_id,
        name=candidate.name,
        slot=slot,
        quantity=quantity,
        cmc=candidate.cmc,
        mana_cost=candidate.mana_cost,
        type_line=candidate.type_line,
        price_usd=candidate.price_usd,
        price_known=candidate.price_known,
        scryfall_uri=candidate.scryfall_uri,
        image_uri=candidate.image_uri,
        mechanic_tags=tags,
        oracle_text=candidate.oracle_text,
        color_identity=list(candidate.color_identity),
        produced_mana=list(candidate.produced_mana),
        released_at=candidate.released_at,
        rarity=candidate.rarity,
        power=candidate.power,
        toughness=candidate.toughness,
    )


def _slot_for_candidate(candidate: CardCandidate) -> str:
    return "lands" if candidate.is_basic_land else "imported"


def _commander_dicts(
    conn: sqlite3.Connection,
    commander_candidates: list[CardCandidate],
) -> tuple[list[dict[str, Any]], list[str]]:
    oracle_ids = [c.oracle_id for c in commander_candidates]
    rows = fetch_commanders(conn, oracle_ids)
    if len(rows) != len(oracle_ids):
        raise RuntimeError("Resolved commander(s) not found in database.")

    identity_rows = [
        {
            "oracle_id": row["oracle_id"],
            "name": row["name"],
            "type_line": row["type_line"] or "",
            "color_identity": json.loads(row["color_identity"] or "[]"),
            "partner_kind": row["partner_kind"],
            "scryfall_uri": row["scryfall_uri"],
            "image_uri": row["image_uri"],
            "price_usd": row["price_usd"],
            "price_known": bool(row["price_known"]),
            "released_at": row["released_at"],
            "mana_cost": row["mana_cost"] or "",
            "cmc": float(row["cmc"] or 0),
            "oracle_text": row["oracle_text"] or "",
            "rarity": row["rarity"],
            "power": row["power"],
            "toughness": row["toughness"],
        }
        for row in rows
    ]
    identity = combined_color_identity(
        [
            CommanderRow(
                oracle_id=row["oracle_id"],
                name=row["name"],
                color_identity=row["color_identity"],
                partner_kind=row["partner_kind"],
                edhrec_rank=None,
            )
            for row in identity_rows
        ],
    )
    return identity_rows, identity


def build_imported_deck_document(
    conn: sqlite3.Connection,
    resolved: ResolvedDeckList,
) -> dict[str, Any]:
    """Build a library-ready .deck.json from a resolved import list."""
    identity_rows, identity = _commander_dicts(conn, resolved.commanders)
    commander_ids = [row["oracle_id"] for row in identity_rows]

    oracle_ids = [line.candidate.oracle_id for line in resolved.maindeck]
    tag_map = fetch_card_tags(conn, oracle_ids)

    cards: list[DeckCard] = []
    warnings: list[str] = []
    unpriced_names: list[str] = []

    for line in resolved.maindeck:
        if line.quantity > 1 and not line.candidate.is_basic_land:
            warnings.append(
                f"[import] {line.candidate.name} has quantity {line.quantity}; "
                "only basic lands may exceed 1 in Commander.",
            )
        tags = tag_map.get(line.candidate.oracle_id, [])
        cards.append(
            _deck_card_from_candidate(
                line.candidate,
                slot=_slot_for_candidate(line.candidate),
                tags=tags,
                quantity=line.quantity,
            ),
        )
        if not line.candidate.price_known:
            unpriced_names.append(line.candidate.name)

    slot_config = load_slot_template_config()
    criteria = DeckCriteria(
        commander_oracle_ids=commander_ids,
        colors=identity,
        slot_template=dict(slot_config.default),
    )

    maindeck = DeckBuildResult(
        cards=cards,
        warnings=warnings,
        budget_spent=_deck_budget_spent(cards),
        unpriced_names=unpriced_names,
    )

    validation = validate_commander_deck(
        conn,
        commanders=identity_rows,
        maindeck=cards,
        identity=identity,
        budget_usd=criteria.budget_usd,
        budget_spent=maindeck.budget_spent,
        unpriced_count=len(unpriced_names),
    )
    maindeck.validation = validation
    maindeck.warnings.extend(validation_messages(validation))

    maindeck.dependency_report = validate_dependencies(
        conn,
        maindeck=cards,
        commanders=identity_rows,
        criteria=criteria,
        strict=False,
    )
    maindeck.warnings.extend(dependency_messages(maindeck.dependency_report))

    return build_deck_document(
        criteria=criteria,
        commanders=identity_rows,
        maindeck=maindeck,
        identity=identity,
    )
