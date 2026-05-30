"""Import writes card_effects (D1)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from mtg_deck_tools.db.schema import SCHEMA_VERSION, apply_schema
from mtg_deck_tools.import_.pipeline import run_import


def _minimal_oracle_json(path: Path) -> None:
    cards = [
        {
            "oracle_id": "test-energy",
            "id": "test-energy",
            "name": "Test Energy Card",
            "layout": "normal",
            "lang": "en",
            "type_line": "Creature",
            "oracle_text": "You get {E}{E}.",
            "mana_cost": "{2}",
            "cmc": 2.0,
            "color_identity": ["G"],
            "legalities": {"commander": "legal"},
        },
        {
            "oracle_id": "test-tutor",
            "id": "test-tutor",
            "name": "Test Tutor",
            "layout": "normal",
            "lang": "en",
            "type_line": "Sorcery",
            "oracle_text": "Search your library for a creature card, reveal it, put it into your hand, then shuffle.",
            "mana_cost": "{1}{G}",
            "cmc": 2.0,
            "color_identity": ["G"],
            "legalities": {"commander": "legal"},
        },
    ]
    path.write_text(json.dumps(cards), encoding="utf-8")


def test_import_writes_card_effects(tmp_path: Path) -> None:
    json_path = tmp_path / "oracle-cards-test.json"
    db_path = tmp_path / "cards.db"
    _minimal_oracle_json(json_path)

    result = run_import(json_path=json_path, db_path=db_path)
    assert result["effect_count"] >= 2

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    apply_schema(conn)
    version = conn.execute(
        "SELECT value FROM import_metadata WHERE key = 'schema_version'"
    ).fetchone()[0]
    assert version == SCHEMA_VERSION

    kinds = {
        row[0]
        for row in conn.execute(
            "SELECT DISTINCT effect_kind FROM card_effects"
        ).fetchall()
    }
    assert "energy_produce" in kinds
    assert "search_library" in kinds
    conn.close()
