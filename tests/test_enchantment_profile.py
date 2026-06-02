"""Enchantment matters dependency profile."""

from __future__ import annotations

import json
import sqlite3

import pytest

from mtg_deck_tools.builder.deck import DeckCard
from mtg_deck_tools.builder.mechanic_packages import ensure_enchantment_package
from mtg_deck_tools.db.schema import apply_schema
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.rules.dependency_profiles import enchantment_spell_min


def _deck_card(*, oracle_id: str, name: str, type_line: str) -> DeckCard:
    return DeckCard(
        oracle_id=oracle_id,
        name=name,
        slot="flex",
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


@pytest.fixture
def enchantment_pkg_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    apply_schema(conn)
    for i in range(8):
        _insert_card(conn, oracle_id=f"f{i}", name=f"Filler {i}", type_line="Instant")
    _insert_card(conn, oracle_id="payoff", name="Sythis Payoff", type_line="Enchantment")
    conn.execute(
        """
        INSERT INTO card_effects (
            oracle_id, face_index, effect_kind, payload, confidence, source
        ) VALUES (?, 0, 'whenever_cast_enchantment', ?, 1.0, 'whenever_cast_enchantment')
        """,
        ("payoff", json.dumps({"types": ["enchantment"]})),
    )
    for i in range(12):
        oid = f"e{i}"
        _insert_card(
            conn,
            oracle_id=oid,
            name=f"Enchantment {i}",
            type_line="Enchantment",
        )
    conn.commit()
    return conn


def test_enchantment_spell_min_default() -> None:
    assert enchantment_spell_min() == 8


def test_ensure_enchantment_package_adds_support(
    enchantment_pkg_db: sqlite3.Connection, monkeypatch
) -> None:
    monkeypatch.setattr(
        "mtg_deck_tools.rules.dependency_profiles.enchantment_spell_min",
        lambda profiles=None: 3,
    )
    cards = [
        _deck_card(oracle_id="payoff", name="Sythis Payoff", type_line="Enchantment"),
        _deck_card(oracle_id="f0", name="Filler 0", type_line="Instant"),
        _deck_card(oracle_id="f1", name="Filler 1", type_line="Instant"),
        _deck_card(oracle_id="f2", name="Filler 2", type_line="Instant"),
    ]
    result = ensure_enchantment_package(
        enchantment_pkg_db,
        cards,
        criteria=DeckCriteria(themes=["tokens"]),
        identity=["G"],
        commander_oracle_ids=set(),
        commander_theme_tags=set(),
    )
    assert result.swaps >= 1
    enchantments = sum(1 for c in result.cards if "Enchantment" in c.type_line)
    assert enchantments >= 3
