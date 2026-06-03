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
        type_line="Legendary Creature — Human Cleric",
    )
    label = format_commander_choice(cmd)
    assert "Yawgmoth, Thran Physician - Legendary Creature — Human Cleric (B)" in label
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


@pytest.fixture
def color_match_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    apply_schema(conn)
    rows = [
        ("mono-b", "Mono B", json.dumps(["B"])),
        ("golgari", "Golgari", json.dumps(["B", "G"])),
        ("naya", "Naya", json.dumps(["R", "G", "W"])),
        ("colorless", "Colorless", json.dumps([])),
    ]
    for oracle_id, name, color_identity in rows:
        conn.execute(
            """
            INSERT INTO cards (
                oracle_id, name, type_line, color_identity, commander_legal,
                commander_eligible
            ) VALUES (?, ?, 'Legendary Creature', ?, 1, 1)
            """,
            (oracle_id, name, color_identity),
        )
    conn.commit()
    return conn


def test_search_commanders_exact_color_identity(color_match_db: sqlite3.Connection) -> None:
    exact = search_commanders(color_match_db, colors=["B"], color_match="exact")
    assert {c.oracle_id for c in exact} == {"mono-b"}

    exact_bg = search_commanders(color_match_db, colors=["B", "G"], color_match="exact")
    assert {c.oracle_id for c in exact_bg} == {"golgari"}

    exact_empty = search_commanders(color_match_db, colors=[], color_match="exact")
    assert {c.oracle_id for c in exact_empty} == {"colorless"}


def test_search_commanders_includes_extra_colors(color_match_db: sqlite3.Connection) -> None:
    includes = search_commanders(color_match_db, colors=["B"], color_match="includes")
    assert {c.oracle_id for c in includes} == {"mono-b", "golgari"}

    includes_bg = search_commanders(color_match_db, colors=["B", "G"], color_match="includes")
    assert {c.oracle_id for c in includes_bg} == {"golgari"}


def test_search_commanders_filters_per_card_price_range(
    commander_db: sqlite3.Connection,
) -> None:
    conn = commander_db
    conn.execute(
        """
        INSERT INTO cards (
            oracle_id, name, type_line, color_identity, commander_legal,
            commander_eligible, price_usd, price_known
        ) VALUES ('expensive', 'Expensive', 'Legendary Creature', '[]', 1, 1, 50.0, 1)
        """
    )
    conn.commit()

    in_range = search_commanders(
        conn,
        colors=["B"],
        card_price_max_usd=10.0,
        strict_budget=True,
    )
    assert {c.oracle_id for c in in_range} == {"cmd-1"}

    out_of_range = search_commanders(
        conn,
        colors=[],
        card_price_max_usd=10.0,
        strict_budget=True,
        name_query="Expensive",
    )
    assert out_of_range == []


def test_search_commanders_loads_price_and_date(commander_db: sqlite3.Connection) -> None:
    results = search_commanders(commander_db, colors=["B"], name_query="Test")
    assert len(results) == 1
    assert results[0].price_usd == 3.25
    assert results[0].price_known is True
    assert results[0].released_at == "2020-03-15"
    assert results[0].type_line == "Legendary Creature"
    assert "$3.25" in format_commander_choice(results[0])
    assert "Test Commander - Legendary Creature" in format_commander_choice(results[0])
    assert "March 15, 2020" in format_commander_choice(results[0])
