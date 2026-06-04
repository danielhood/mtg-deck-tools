"""Token subtype produce/buff pairing (Priority 8)."""

from __future__ import annotations

import json
import sqlite3

import pytest

from mtg_deck_tools.builder.deck import DeckCard
from mtg_deck_tools.db.schema import apply_schema
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.rules.dependencies import fetch_card_effects, validate_dependencies
from mtg_deck_tools.rules.token_subtype import (
    RULE_TOKEN_SUBTYPE_BUFF_SUPPORT,
    aggregate_token_produce_subtypes,
    deck_has_generic_token_payoff,
)


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


def _insert_card(conn: sqlite3.Connection, oracle_id: str, name: str) -> None:
    conn.execute(
        """
        INSERT INTO cards (
            oracle_id, name, type_line, oracle_text, mana_cost, cmc, color_identity,
            keywords, commander_legal, commander_eligible, is_basic_land, price_known
        ) VALUES (?, ?, 'Enchantment', '', '{2}', 2, '[]', '[]', 1, 0, 0, 1)
        """,
        (oracle_id, name),
    )


def _insert_effect(
    conn: sqlite3.Connection,
    oracle_id: str,
    effect_kind: str,
    payload: dict,
    source: str,
) -> None:
    conn.execute(
        """
        INSERT INTO card_effects (
            oracle_id, face_index, effect_kind, payload, confidence, source
        ) VALUES (?, 0, ?, ?, 1.0, ?)
        """,
        (oracle_id, effect_kind, json.dumps(payload), source),
    )


@pytest.fixture
def token_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    apply_schema(conn)
    conn.commit()
    return conn


def test_aggregate_token_produce_subtypes(token_db: sqlite3.Connection) -> None:
    conn = token_db
    for i in range(3):
        oid = f"t{i}"
        _insert_card(conn, oid, f"Treasure {i}")
        _insert_effect(
            conn,
            oid,
            "token_produce",
            {"subtypes": ["Treasure"]},
            "token_produce",
        )
    conn.commit()
    cards = [_deck_card(oracle_id=f"t{i}", name=f"T{i}", type_line="Enchantment") for i in range(3)]
    effects = fetch_card_effects(conn, [c.oracle_id for c in cards])
    counts = aggregate_token_produce_subtypes(effects, cards)
    assert counts["Treasure"] == 3


def test_generic_token_payoff_suppresses_subtype_warn(token_db: sqlite3.Connection) -> None:
    conn = token_db
    for i in range(3):
        oid = f"t{i}"
        _insert_card(conn, oid, f"Treasure {i}")
        _insert_effect(
            conn,
            oid,
            "token_produce",
            {"subtypes": ["Treasure"]},
            "token_produce",
        )
    _insert_card(conn, "virtue", "Intangible Virtue")
    _insert_effect(
        conn,
        "virtue",
        "token_payoff",
        {"trigger": "control"},
        "token_payoff_tokens_you_control",
    )
    conn.commit()
    cards = [_deck_card(oracle_id=f"t{i}", name=f"T{i}", type_line="Enchantment") for i in range(3)]
    cards.append(_deck_card(oracle_id="virtue", name="Intangible Virtue", type_line="Enchantment"))
    effects = fetch_card_effects(conn, [c.oracle_id for c in cards])
    assert deck_has_generic_token_payoff(effects, cards)
    report = validate_dependencies(
        conn,
        maindeck=cards,
        commanders=[],
        criteria=DeckCriteria(themes=["tokens"]),
    )
    assert not any(i.rule_id == RULE_TOKEN_SUBTYPE_BUFF_SUPPORT for i in report.issues)


def test_token_subtype_buff_warns_with_tokens_intent(token_db: sqlite3.Connection) -> None:
    conn = token_db
    for i in range(3):
        oid = f"t{i}"
        _insert_card(conn, oid, f"Treasure {i}")
        _insert_effect(
            conn,
            oid,
            "token_produce",
            {"subtypes": ["Treasure"]},
            "token_produce",
        )
    conn.commit()
    maindeck = [
        _deck_card(oracle_id=f"t{i}", name=f"Treasure {i}", type_line="Enchantment")
        for i in range(3)
    ]
    report = validate_dependencies(
        conn,
        maindeck=maindeck,
        commanders=[],
        criteria=DeckCriteria(themes=["tokens"]),
    )
    assert any(i.rule_id == RULE_TOKEN_SUBTYPE_BUFF_SUPPORT for i in report.warnings)


def test_token_subtype_buff_silent_without_intent(token_db: sqlite3.Connection) -> None:
    conn = token_db
    for i in range(2):
        oid = f"t{i}"
        _insert_card(conn, oid, f"Treasure {i}")
        _insert_effect(
            conn,
            oid,
            "token_produce",
            {"subtypes": ["Treasure"]},
            "token_produce",
        )
    conn.commit()
    maindeck = [
        _deck_card(oracle_id=f"t{i}", name=f"Treasure {i}", type_line="Enchantment")
        for i in range(2)
    ]
    report = validate_dependencies(
        conn,
        maindeck=maindeck,
        commanders=[],
        criteria=DeckCriteria(themes=["aristocrats"]),
    )
    assert not any(i.rule_id == RULE_TOKEN_SUBTYPE_BUFF_SUPPORT for i in report.issues)
