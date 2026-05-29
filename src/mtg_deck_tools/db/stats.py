"""Database statistics queries."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from mtg_deck_tools.db.connection import connect


def fetch_stats(db_path: Path | None = None) -> dict:
    conn = connect(db_path)
    try:
        meta = {
            row["key"]: row["value"]
            for row in conn.execute("SELECT key, value FROM import_metadata")
        }
        total = conn.execute("SELECT COUNT(*) AS c FROM cards").fetchone()["c"]
        commanders = conn.execute(
            "SELECT COUNT(*) AS c FROM cards WHERE commander_eligible = 1"
        ).fetchone()["c"]
        partners = conn.execute(
            "SELECT COUNT(*) AS c FROM cards WHERE partner_kind IS NOT NULL"
        ).fetchone()["c"]
        tag_count = conn.execute("SELECT COUNT(*) AS c FROM card_mechanic_tags").fetchone()[
            "c"
        ]
        distinct_tags = conn.execute(
            "SELECT COUNT(DISTINCT tag) AS c FROM card_mechanic_tags"
        ).fetchone()["c"]
        top_tags = conn.execute(
            """
            SELECT tag, layer, COUNT(*) AS n
            FROM card_mechanic_tags
            GROUP BY tag, layer
            ORDER BY n DESC
            LIMIT 10
            """
        ).fetchall()
        return {
            "metadata": meta,
            "total_cards": total,
            "commander_eligible": commanders,
            "with_partner": partners,
            "tag_assignments": tag_count,
            "distinct_tags": distinct_tags,
            "top_tags": [dict(r) for r in top_tags],
        }
    finally:
        conn.close()
