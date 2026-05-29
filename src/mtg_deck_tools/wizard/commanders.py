"""Commander search and selection helpers."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True)
class CommanderRow:
    oracle_id: str
    name: str
    color_identity: list[str]
    partner_kind: str | None
    edhrec_rank: int | None


def _row_to_commander(row: sqlite3.Row) -> CommanderRow:
    return CommanderRow(
        oracle_id=row["oracle_id"],
        name=row["name"],
        color_identity=json.loads(row["color_identity"] or "[]"),
        partner_kind=row["partner_kind"],
        edhrec_rank=row["edhrec_rank"],
    )


def search_commanders(
    conn: sqlite3.Connection,
    *,
    colors: list[str],
    name_query: str = "",
    limit: int = 15,
) -> list[CommanderRow]:
    """Find commander-eligible cards matching color filter and optional name substring."""
    sql = """
        SELECT oracle_id, name, color_identity, partner_kind, edhrec_rank
        FROM cards
        WHERE commander_eligible = 1
    """
    params: list = []
    for color in colors:
        sql += " AND color_identity LIKE ?"
        params.append(f'%"{color}"%')
    if name_query.strip():
        sql += " AND name LIKE ? ESCAPE '\\'"
        params.append(f"%{name_query.strip()}%")
    sql += " ORDER BY edhrec_rank ASC NULLS LAST, name ASC LIMIT ?"
    params.append(limit)
    rows = conn.execute(sql, params).fetchall()
    return [_row_to_commander(r) for r in rows]


def fetch_commander(conn: sqlite3.Connection, oracle_id: str) -> CommanderRow | None:
    row = conn.execute(
        """
        SELECT oracle_id, name, color_identity, partner_kind, edhrec_rank
        FROM cards
        WHERE oracle_id = ? AND commander_eligible = 1
        """,
        (oracle_id,),
    ).fetchone()
    return _row_to_commander(row) if row else None


def combined_color_identity(commanders: list[CommanderRow]) -> list[str]:
    combined: set[str] = set()
    for cmd in commanders:
        combined.update(cmd.color_identity)
    order = ("W", "U", "B", "R", "G")
    return [c for c in order if c in combined]
