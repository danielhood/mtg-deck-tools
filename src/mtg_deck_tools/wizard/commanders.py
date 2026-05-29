"""Commander search and selection helpers."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass

from mtg_deck_tools.formatting import format_price_display, format_released_at_display


@dataclass(frozen=True)
class CommanderRow:
    oracle_id: str
    name: str
    color_identity: list[str]
    partner_kind: str | None = None
    edhrec_rank: int | None = None
    price_usd: float | None = None
    price_known: bool = False
    released_at: str | None = None


def format_commander_choice(cmd: CommanderRow) -> str:
    """Label for commander selection prompts."""
    colors = ", ".join(cmd.color_identity) or "colorless"
    price = format_price_display(price_known=cmd.price_known, price_usd=cmd.price_usd)
    released = format_released_at_display(cmd.released_at)
    rank = f" · EDHREC #{cmd.edhrec_rank}" if cmd.edhrec_rank else ""
    partner = f" · {cmd.partner_kind}" if cmd.partner_kind else ""
    return f"{cmd.name} ({colors}) · {price} · {released}{rank}{partner}"


def _row_to_commander(row: sqlite3.Row) -> CommanderRow:
    return CommanderRow(
        oracle_id=row["oracle_id"],
        name=row["name"],
        color_identity=json.loads(row["color_identity"] or "[]"),
        partner_kind=row["partner_kind"],
        edhrec_rank=row["edhrec_rank"],
        price_usd=row["price_usd"],
        price_known=bool(row["price_known"]),
        released_at=row["released_at"],
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
        SELECT oracle_id, name, color_identity, partner_kind, edhrec_rank,
               price_usd, price_known, released_at
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
        SELECT oracle_id, name, color_identity, partner_kind, edhrec_rank,
               price_usd, price_known, released_at
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
