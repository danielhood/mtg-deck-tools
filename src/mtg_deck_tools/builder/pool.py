"""Candidate pool queries for slot filling."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass

from mtg_deck_tools.rules.commander import COLOR_ORDER

ALL_COLORS = COLOR_ORDER


@dataclass(frozen=True)
class CardCandidate:
    oracle_id: str
    name: str
    cmc: float
    type_line: str
    mana_cost: str
    color_identity: list[str]
    price_usd: float | None
    price_known: bool
    edhrec_rank: int | None
    oracle_text: str
    keywords: list[str]
    is_basic_land: bool
    scryfall_uri: str | None
    image_uri: str | None


def _row_to_candidate(row: sqlite3.Row) -> CardCandidate:
    return CardCandidate(
        oracle_id=row["oracle_id"],
        name=row["name"],
        cmc=float(row["cmc"] or 0),
        type_line=row["type_line"] or "",
        mana_cost=row["mana_cost"] or "",
        color_identity=json.loads(row["color_identity"] or "[]"),
        price_usd=row["price_usd"],
        price_known=bool(row["price_known"]),
        edhrec_rank=row["edhrec_rank"],
        oracle_text=row["oracle_text"] or "",
        keywords=json.loads(row["keywords"] or "[]"),
        is_basic_land=bool(row["is_basic_land"]),
        scryfall_uri=row["scryfall_uri"],
        image_uri=row["image_uri"],
    )


def _color_identity_clauses(identity: list[str]) -> tuple[str, list[str]]:
    """Exclude cards with colors outside commander identity."""
    sql = ""
    params: list[str] = []
    identity_set = set(identity)
    for color in ALL_COLORS:
        if color not in identity_set:
            sql += " AND c.color_identity NOT LIKE ?"
            params.append(f'%"{color}"%')
    return sql, params


def fetch_candidates(
    conn: sqlite3.Connection,
    *,
    identity: list[str],
    exclude_oracle_ids: set[str],
    exclude_names: set[str],
    avoid_mechanics: list[str],
    require_theme_tags: list[str] | None,
    lands_only: bool = False,
    nonlands_only: bool = False,
    limit: int = 500,
) -> list[CardCandidate]:
    """
    Query commander-legal cards matching hard constraints.

    require_theme_tags: when set, card must have at least one tag (theme layer).
    """
    sql = """
        SELECT DISTINCT c.oracle_id, c.name, c.cmc, c.type_line, c.mana_cost,
               c.color_identity, c.price_usd, c.price_known, c.edhrec_rank,
               c.oracle_text, c.keywords, c.is_basic_land, c.scryfall_uri, c.image_uri
        FROM cards c
    """
    params: list = []

    if require_theme_tags:
        placeholders = ",".join("?" * len(require_theme_tags))
        sql += f"""
        JOIN card_mechanic_tags t ON t.oracle_id = c.oracle_id
            AND t.layer = 'theme' AND t.tag IN ({placeholders})
        """
        params.extend(require_theme_tags)

    sql += """
        WHERE c.commander_legal = 1
          AND c.commander_eligible = 0
    """

    if lands_only:
        sql += " AND (c.is_basic_land = 1 OR c.type_line LIKE '% Land%')"
    elif nonlands_only:
        sql += " AND c.is_basic_land = 0 AND c.type_line NOT LIKE '% Land%'"

    if exclude_oracle_ids:
        placeholders = ",".join("?" * len(exclude_oracle_ids))
        sql += f" AND c.oracle_id NOT IN ({placeholders})"
        params.extend(sorted(exclude_oracle_ids))

    if exclude_names:
        placeholders = ",".join("?" * len(exclude_names))
        sql += f" AND c.name NOT IN ({placeholders})"
        params.extend(sorted(exclude_names))

    if avoid_mechanics:
        placeholders = ",".join("?" * len(avoid_mechanics))
        sql += f"""
          AND c.oracle_id NOT IN (
            SELECT oracle_id FROM card_mechanic_tags
            WHERE tag IN ({placeholders}) AND layer = 'keyword'
          )
        """
        params.extend(avoid_mechanics)

    identity_sql, identity_params = _color_identity_clauses(identity)
    sql += identity_sql
    params.extend(identity_params)

    sql += " LIMIT ?"
    params.append(limit)

    rows = conn.execute(sql, params).fetchall()
    return [_row_to_candidate(r) for r in rows]


def fetch_card_tags(conn: sqlite3.Connection, oracle_ids: list[str]) -> dict[str, list[str]]:
    if not oracle_ids:
        return {}
    placeholders = ",".join("?" * len(oracle_ids))
    rows = conn.execute(
        f"""
        SELECT oracle_id, tag FROM card_mechanic_tags
        WHERE oracle_id IN ({placeholders})
        """,
        oracle_ids,
    ).fetchall()
    result: dict[str, list[str]] = {}
    for row in rows:
        result.setdefault(row["oracle_id"], []).append(row["tag"])
    return result
