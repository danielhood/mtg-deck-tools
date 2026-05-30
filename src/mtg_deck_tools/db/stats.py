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
        effect_rows = 0
        effect_kinds = 0
        tables = {
            row[0] for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        if "card_effects" in tables:
            effect_rows = conn.execute("SELECT COUNT(*) AS c FROM card_effects").fetchone()["c"]
            effect_kinds = conn.execute(
                "SELECT COUNT(DISTINCT effect_kind) AS c FROM card_effects"
            ).fetchone()["c"]
        return {
            "metadata": meta,
            "total_cards": total,
            "commander_eligible": commanders,
            "with_partner": partners,
            "tag_assignments": tag_count,
            "distinct_tags": distinct_tags,
            "effect_rows": effect_rows,
            "distinct_effect_kinds": effect_kinds,
            "top_tags": [dict(r) for r in top_tags],
        }
    finally:
        conn.close()
