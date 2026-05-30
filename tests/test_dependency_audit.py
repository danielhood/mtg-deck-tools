"""Dependency inventory audit tests."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from mtg_deck_tools.db.schema import apply_schema
from mtg_deck_tools.effects.audit import run_dependency_audit, write_audit_reports
from mtg_deck_tools.effects.extract import EffectExtractor
from mtg_deck_tools.paths import EFFECT_PATTERNS_PATH


def _insert(
    conn: sqlite3.Connection,
    *,
    oracle_id: str,
    name: str,
    oracle_text: str,
    type_line: str = "Instant",
    color_identity: list[str] | None = None,
) -> None:
    ci = color_identity or ["G"]
    conn.execute(
        """
        INSERT INTO cards (
            oracle_id, name, type_line, oracle_text, mana_cost, cmc, color_identity,
            keywords, commander_legal, commander_eligible, is_basic_land, price_known
        ) VALUES (?, ?, ?, ?, '{1}{G}', 2, ?, '[]', 1, 0, 0, 1)
        """,
        (oracle_id, name, type_line, oracle_text, json.dumps(ci)),
    )


@pytest.fixture
def audit_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    apply_schema(conn)
    _insert(
        conn,
        oracle_id="a",
        name="Aether Hub",
        oracle_text="Whenever a land enters, you get {E}.",
        color_identity=["G"],
    )
    _insert(
        conn,
        oracle_id="b",
        name="Worldly Tutor",
        oracle_text="Search your library for a creature card, reveal it, put it into your hand, then shuffle.",
    )
    _insert(
        conn,
        oracle_id="c",
        name="Demonic Tutor",
        oracle_text="Search your library for a card, put that card into your hand, then shuffle.",
        color_identity=["B"],
    )
    conn.execute(
        "INSERT INTO card_mechanic_tags (oracle_id, tag, layer, source) VALUES ('a', 'energy', 'keyword', 'test')"
    )
    conn.commit()
    return conn


def test_run_dependency_audit_counts(audit_db: sqlite3.Connection) -> None:
    ext = EffectExtractor.from_yaml(EFFECT_PATTERNS_PATH)
    audit = run_dependency_audit(audit_db, extractor=ext)
    assert audit["commander_legal_cards"] == 3
    assert audit["effect_kind_hits"].get("energy_produce", 0) >= 1
    assert audit["effect_kind_hits"].get("search_library", 0) >= 2
    assert audit["profile_summary"]["global"]["energy"]["producer"] >= 1
    assert audit["energy_tag_gap"]["producers_tagged"] >= 1


def test_write_audit_reports(tmp_path: Path, audit_db: sqlite3.Connection) -> None:
    ext = EffectExtractor.from_yaml(EFFECT_PATTERNS_PATH)
    audit = run_dependency_audit(audit_db, extractor=ext)
    paths = write_audit_reports(audit, tmp_path)
    assert paths["pattern_hits"].exists()
    assert paths["tutor_predicates"].exists()
    data = json.loads(paths["profile_summary"].read_text(encoding="utf-8"))
    assert "profile_summary" in data
