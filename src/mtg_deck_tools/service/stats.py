"""Database statistics facade."""

from __future__ import annotations

from pathlib import Path

from mtg_deck_tools.db.stats import fetch_stats
from mtg_deck_tools.paths import resolve_db_path
from mtg_deck_tools.service.dto import DatabaseStatsResponse, TopTagRow


def get_database_stats(db_path: Path | None = None) -> DatabaseStatsResponse:
    path = resolve_db_path(db_path)
    if not path.exists():
        raise FileNotFoundError(f"Database not found: {path}")

    raw = fetch_stats(path)
    return DatabaseStatsResponse(
        db_path=str(path.resolve()),
        metadata=raw["metadata"],
        total_cards=raw["total_cards"],
        commander_eligible=raw["commander_eligible"],
        with_partner=raw["with_partner"],
        tag_assignments=raw["tag_assignments"],
        distinct_tags=raw["distinct_tags"],
        effect_rows=raw.get("effect_rows") or 0,
        distinct_effect_kinds=raw.get("distinct_effect_kinds") or 0,
        top_tags=[TopTagRow(**row) for row in raw["top_tags"]],
    )
