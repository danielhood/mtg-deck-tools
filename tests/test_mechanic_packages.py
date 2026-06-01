"""Included mechanic package enforcement (energy floors)."""

from __future__ import annotations

import json
import sqlite3

import pytest

from mtg_deck_tools.builder.deck import DeckCard
from mtg_deck_tools.builder.mechanic_packages import ensure_energy_package
from mtg_deck_tools.db.schema import apply_schema
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.rules.dependencies import validate_dependencies


def _deck_card(*, oracle_id: str, name: str, type_line: str, slot: str = "flex") -> DeckCard:
    return DeckCard(
        oracle_id=oracle_id,
        name=name,
        slot=slot,
        quantity=1,
        cmc=2.0,
        mana_cost="{2}",
        type_line=type_line,
        price_usd=1.0,
        price_known=True,
        scryfall_uri=None,
        image_uri=None,
    )


def _insert_card(conn: sqlite3.Connection, *, oracle_id: str, name: str, type_line: str) -> None:
    conn.execute(
        """
        INSERT INTO cards (
            oracle_id, name, type_line, oracle_text, mana_cost, cmc, color_identity,
            keywords, commander_legal, commander_eligible, is_basic_land, price_known
        ) VALUES (?, ?, ?, '', '{2}', 2, '["G"]', '[]', 1, 0, 0, 1)
        """,
        (oracle_id, name, type_line),
    )


def _insert_effect(
    conn: sqlite3.Connection,
    oracle_id: str,
    effect_kind: str,
    source: str,
) -> None:
    conn.execute(
        """
        INSERT INTO card_effects (
            oracle_id, face_index, effect_kind, payload, confidence, source
        ) VALUES (?, 0, ?, '{}', 1.0, ?)
        """,
        (oracle_id, effect_kind, source),
    )


@pytest.fixture
def energy_pkg_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    apply_schema(conn)
    for i in range(4):
        _insert_card(conn, oracle_id=f"f{i}", name=f"Filler {i}", type_line="Instant")
    _insert_card(conn, oracle_id="hub", name="Aether Hub", type_line="Land")
    _insert_effect(conn, "hub", "energy_produce", "energy_produce")
    _insert_card(conn, oracle_id="pay1", name="Attune with Aether", type_line="Sorcery")
    _insert_effect(conn, "pay1", "energy_consume", "energy_consume")
    _insert_card(conn, oracle_id="pay2", name="Harnessed Lightning", type_line="Instant")
    _insert_effect(conn, "pay2", "energy_consume", "energy_consume")
    _insert_card(conn, oracle_id="solo", name="Conversion Apparatus", type_line="Artifact")
    _insert_effect(conn, "solo", "energy_consume", "energy_consume")
    conn.commit()
    return conn


def test_ensure_energy_adds_producers_when_only_consumer(energy_pkg_db: sqlite3.Connection) -> None:
    cards = [
        _deck_card(oracle_id="solo", name="Conversion Apparatus", type_line="Artifact"),
        _deck_card(oracle_id="f0", name="Filler 0", type_line="Instant"),
    ]
    criteria = DeckCriteria(include_mechanics=["energy"])
    result = ensure_energy_package(
        energy_pkg_db,
        cards,
        criteria=criteria,
        identity=["G"],
        commander_oracle_ids=set(),
        commander_theme_tags=set(),
    )
    assert result.swaps >= 1
    report = validate_dependencies(
        energy_pkg_db,
        maindeck=result.cards,
        commanders=[],
        criteria=criteria,
    )
    energy_issues = [i for i in report.issues if i.rule_id == "ENERGY_BALANCE"]
    assert not energy_issues
