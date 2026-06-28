"""Candidate pool queries for slot filling."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass

from mtg_deck_tools.pricing import resolve_card_price
from mtg_deck_tools.rules.commander import (
    COLOR_ORDER,
    is_land_card,
    land_produces_only_identity,
)

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
    produced_mana: list[str]
    scryfall_uri: str | None
    image_uri: str | None
    released_at: str | None = None
    power: str | None = None
    toughness: str | None = None
    rarity: str | None = None
    availability_score: float | None = None


def _row_to_candidate(row: sqlite3.Row) -> CardCandidate:
    price_usd, price_known = resolve_card_price(
        price_usd=row["price_usd"],
        price_known=bool(row["price_known"]),
        is_basic_land=bool(row["is_basic_land"]),
        type_line=row["type_line"] or "",
    )
    return CardCandidate(
        oracle_id=row["oracle_id"],
        name=row["name"],
        cmc=float(row["cmc"] or 0),
        type_line=row["type_line"] or "",
        mana_cost=row["mana_cost"] or "",
        color_identity=json.loads(row["color_identity"] or "[]"),
        price_usd=price_usd,
        price_known=price_known,
        edhrec_rank=row["edhrec_rank"],
        oracle_text=row["oracle_text"] or "",
        keywords=json.loads(row["keywords"] or "[]"),
        is_basic_land=bool(row["is_basic_land"]),
        produced_mana=json.loads(row["produced_mana"] or "[]"),
        scryfall_uri=row["scryfall_uri"],
        image_uri=row["image_uri"],
        released_at=row["released_at"],
        power=row["power"],
        toughness=row["toughness"],
        rarity=row["rarity"],
        availability_score=row["availability_score"],
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
               c.oracle_text, c.keywords, c.is_basic_land, c.produced_mana,
               c.scryfall_uri, c.image_uri, c.released_at, c.power, c.toughness,
               c.rarity, c.availability_score
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
        sql += """
          AND (
            c.is_basic_land = 1
            OR c.type_line = 'Land'
            OR c.type_line LIKE '% Land%'
            OR c.type_line LIKE 'Land —%'
          )
        """
    elif nonlands_only:
        sql += """
          AND c.is_basic_land = 0
          AND c.type_line != 'Land'
          AND c.type_line NOT LIKE '% Land%'
          AND c.type_line NOT LIKE 'Land —%'
        """

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
    candidates = [_row_to_candidate(r) for r in rows]

    if lands_only:
        candidates = [
            c
            for c in candidates
            if is_land_card(type_line=c.type_line, is_basic_land=c.is_basic_land)
            and land_produces_only_identity(
                produced_mana=c.produced_mana,
                identity=identity,
                is_basic_land=c.is_basic_land,
            )
        ]
    elif nonlands_only:
        candidates = [
            c
            for c in candidates
            if not is_land_card(type_line=c.type_line, is_basic_land=c.is_basic_land)
        ]

    return candidates


def search_cards_by_name(
    conn: sqlite3.Connection,
    *,
    name_query: str,
    colors: list[str] | None = None,
    limit: int = 15,
) -> list[CardCandidate]:
    """Commander-legal cards matching a name substring and optional color identity."""
    sql = """
        SELECT oracle_id, name, type_line, mana_cost, cmc, color_identity,
               keywords, price_usd, price_known, edhrec_rank, oracle_text,
               is_basic_land, produced_mana, scryfall_uri, image_uri,
               released_at, power, toughness, rarity, availability_score
        FROM cards
        WHERE commander_legal = 1
    """
    params: list = []
    if name_query.strip():
        sql += " AND name LIKE ? ESCAPE '\\'"
        params.append(f"%{name_query.strip()}%")
    if colors:
        for color in colors:
            sql += " AND color_identity LIKE ?"
            params.append(f'%"{color}"%')
    sql += " ORDER BY edhrec_rank ASC NULLS LAST, name ASC LIMIT ?"
    params.append(limit)
    rows = conn.execute(sql, params).fetchall()
    return [_row_to_candidate(row) for row in rows]


def fetch_card_by_oracle_id(conn: sqlite3.Connection, oracle_id: str) -> sqlite3.Row | None:
    return conn.execute(
        """
        SELECT oracle_id, name, type_line, mana_cost, cmc, color_identity,
               keywords, price_usd, price_known, edhrec_rank, oracle_text,
               is_basic_land, produced_mana, scryfall_uri, image_uri,
               released_at, power, toughness, rarity, availability_score
        FROM cards
        WHERE oracle_id = ?
        """,
        (oracle_id,),
    ).fetchone()


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
