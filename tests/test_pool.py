"""Candidate pool legality filter tests (Phase 3 §1)."""

from __future__ import annotations

import json
import sqlite3

import pytest

from mtg_deck_tools.builder.pool import fetch_candidates
from mtg_deck_tools.db.schema import apply_schema
from mtg_deck_tools.rules.commander import is_land_card, land_produces_only_identity


def _insert(
    conn: sqlite3.Connection,
    *,
    oracle_id: str,
    name: str,
    type_line: str,
    color_identity: list[str] | None = None,
    is_basic_land: int = 0,
    produced_mana: list[str] | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO cards (
            oracle_id, name, type_line, mana_cost, cmc, color_identity,
            keywords, commander_legal, commander_eligible, is_basic_land,
            produced_mana, price_usd, price_known
        ) VALUES (?, ?, ?, '', 0, ?, '[]', 1, 0, ?, ?, 1.0, 1)
        """,
        (
            oracle_id,
            name,
            type_line,
            json.dumps(color_identity or []),
            is_basic_land,
            json.dumps(produced_mana or []),
        ),
    )


@pytest.fixture
def pool_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    apply_schema(conn)

    _insert(
        conn,
        oracle_id="tower",
        name="Command Tower",
        type_line="Land",
        produced_mana=["W", "U", "B", "R", "G"],
    )
    _insert(
        conn,
        oracle_id="grove",
        name="Grove of the Burnwillows",
        type_line="Land",
        produced_mana=["R", "G"],
    )
    _insert(
        conn,
        oracle_id="temple",
        name="Temple Garden",
        type_line="Land — Forest Plains",
        produced_mana=["W", "G"],
    )
    _insert(
        conn,
        oracle_id="rock",
        name="Sol Ring",
        type_line="Artifact",
    )
    _insert(
        conn,
        oracle_id="enchant",
        name="Utopia Sprawl",
        type_line="Enchantment — Aura",
    )
    _insert(
        conn,
        oracle_id="enchant-land",
        name="Wild Growth",
        type_line="Enchant Land — Aura",
    )
    _insert(
        conn,
        oracle_id="forest",
        name="Forest",
        type_line="Basic Land — Forest",
        is_basic_land=1,
    )
    conn.commit()
    return conn


def test_is_land_card_type_line_variants() -> None:
    assert is_land_card(type_line="Land")
    assert is_land_card(type_line="Land — Gate")
    assert is_land_card(type_line="Basic Land — Forest", is_basic_land=True)
    assert is_land_card(type_line="Artifact Land")
    assert not is_land_card(type_line="Artifact")
    assert not is_land_card(type_line="Enchant Land — Aura")
    assert not is_land_card(type_line="Creature — Elf")


def test_land_produces_only_identity() -> None:
    assert land_produces_only_identity(produced_mana=["W", "G"], identity=["W", "G"])
    assert not land_produces_only_identity(
        produced_mana=["W", "U", "B", "R", "G"], identity=["W", "G"]
    )
    assert land_produces_only_identity(produced_mana=[], identity=["W", "G"])
    assert not land_produces_only_identity(
        produced_mana=["R", "G"], identity=["W", "G"], is_basic_land=False
    )


def test_nonlands_only_excludes_type_line_land(pool_db: sqlite3.Connection) -> None:
    pool = fetch_candidates(
        pool_db,
        identity=["W", "G"],
        exclude_oracle_ids=set(),
        exclude_names=set(),
        avoid_mechanics=[],
        require_theme_tags=None,
        nonlands_only=True,
    )
    names = {c.name for c in pool}
    assert "Command Tower" not in names
    assert "Temple Garden" not in names
    assert "Sol Ring" in names
    assert "Utopia Sprawl" in names


def test_lands_only_excludes_off_color_production(pool_db: sqlite3.Connection) -> None:
    pool = fetch_candidates(
        pool_db,
        identity=["W", "G"],
        exclude_oracle_ids=set(),
        exclude_names=set(),
        avoid_mechanics=[],
        require_theme_tags=None,
        lands_only=True,
    )
    names = {c.name for c in pool}
    assert "Command Tower" not in names
    assert "Grove of the Burnwillows" not in names
    assert "Temple Garden" in names
    assert "Forest" in names
    assert "Wild Growth" not in names
