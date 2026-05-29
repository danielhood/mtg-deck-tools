"""Commander helper tests."""

import json
import sqlite3

import pytest

from mtg_deck_tools.db.schema import apply_schema
from mtg_deck_tools.wizard.commanders import (
    CommanderRow,
    combined_color_identity,
    format_commander_choice,
    search_commanders,
)


def test_combined_color_identity():
    a = CommanderRow("1", "A", ["B", "G"], None, None)
    b = CommanderRow("2", "B", ["U", "G"], "partner", None)
    assert combined_color_identity([a, b]) == ["U", "B", "G"]


def test_format_commander_choice_includes_price_and_date() -> None:
    cmd = CommanderRow(
        oracle_id="yawg",
        name="Yawgmoth, Thran Physician",
        color_identity=["B"],
        edhrec_rank=42,
        price_usd=8.5,
        price_known=True,
        released_at="2019-06-14",
    )
    label = format_commander_choice(cmd)
    assert "Yawgmoth, Thran Physician (B)" in label
    assert "$8.50" in label
    assert "June 14, 2019" in label
    assert "EDHREC #42" in label


@pytest.fixture
def commander_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    apply_schema(conn)
    conn.execute(
        """
        INSERT INTO cards (
            oracle_id, name, type_line, color_identity, commander_legal,
            commander_eligible, price_usd, price_known, released_at, edhrec_rank
        ) VALUES (?, ?, ?, ?, 1, 1, ?, 1, ?, ?)
        """,
        (
            "cmd-1",
            "Test Commander",
            "Legendary Creature",
            json.dumps(["B"]),
            3.25,
            "2020-03-15",
            500,
        ),
    )
    conn.commit()
    return conn


def test_search_commanders_loads_price_and_date(commander_db: sqlite3.Connection) -> None:
    results = search_commanders(commander_db, colors=["B"], name_query="Test")
    assert len(results) == 1
    assert results[0].price_usd == 3.25
    assert results[0].price_known is True
    assert results[0].released_at == "2020-03-15"
    assert "$3.25" in format_commander_choice(results[0])
    assert "March 15, 2020" in format_commander_choice(results[0])
