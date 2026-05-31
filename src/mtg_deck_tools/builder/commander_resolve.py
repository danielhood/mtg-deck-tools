"""Commander lookup and selection for deck generation."""

from __future__ import annotations

import random
import sqlite3
from pathlib import Path

from mtg_deck_tools.db.connection import connect
def require_db(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        raise FileNotFoundError(
            f"Database not found at {db_path}. Run: mtg-deck-tools import"
        )
    return connect(db_path)


def fetch_commanders(
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


def pick_commander(
    conn: sqlite3.Connection,
    rng: random.Random,
    *,
    color_filter: list[str],
    commander_ids: list[str],
) -> list[sqlite3.Row]:
    if commander_ids:
        commanders = fetch_commanders(conn, commander_ids)
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


def commander_theme_tags(
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


def resolve_commander_oracle_ids(
    conn: sqlite3.Connection,
    names: list[str],
) -> list[str]:
    """Resolve commander display names to oracle_ids (exact match)."""
    ids: list[str] = []
    for name in names:
        row = conn.execute(
            """
            SELECT oracle_id FROM cards
            WHERE commander_eligible = 1 AND name = ?
            """,
            (name.strip(),),
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Commander not found in database: {name!r}")
        ids.append(row["oracle_id"])
    return ids
