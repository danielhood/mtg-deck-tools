"""Sacrifice / token axis refinements (Priority 4)."""

from __future__ import annotations

import sqlite3

import pytest

from mtg_deck_tools.builder.deck import DeckCard
from mtg_deck_tools.db.schema import apply_schema
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.rules.dependencies import CardEffectRow, validate_dependencies
from mtg_deck_tools.rules.sacrifice_roles import (
    card_is_sacrifice_fodder,
    sacrifice_roles_balanced,
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


def _effect(kind: str, source: str = "test") -> CardEffectRow:
    return CardEffectRow(
        oracle_id="x",
        face_index=0,
        effect_kind=kind,
        payload={},
        confidence=1.0,
        source=source,
    )


def test_token_produce_counts_as_aristocrats_fodder() -> None:
    effects = [_effect("token_produce")]
    assert card_is_sacrifice_fodder(effects)
    assert not card_is_sacrifice_fodder([_effect("token_payoff")])


def test_sacrifice_roles_balanced_with_opponent_sacrifice() -> None:
    assert sacrifice_roles_balanced(
        outlet_count=0,
        payoff_count=2,
        opponent_sacrifice_count=1,
    )


def test_sacrifice_roles_balanced_with_death_recursion() -> None:
    assert sacrifice_roles_balanced(
        outlet_count=0,
        payoff_count=1,
        death_recursion_count=2,
    )
    assert not sacrifice_roles_balanced(
        outlet_count=0,
        payoff_count=1,
        death_recursion_count=1,
    )


@pytest.fixture
def sac_refine_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    apply_schema(conn)
    conn.execute(
        """
        INSERT INTO cards (
            oracle_id, name, type_line, oracle_text, mana_cost, cmc, color_identity,
            keywords, commander_legal, commander_eligible, is_basic_land, price_known
        ) VALUES ('artist', 'Blood Artist', 'Creature', '', '{2}', 2, '[]', '[]', 1, 0, 0, 1)
        """
    )
    _insert_effect(conn, "artist", "sacrifice_payoff", "sacrifice_creature_dies_payoff")
    conn.commit()
    return conn


def test_payoffs_without_outlet_silent_with_two_death_recursion(
    sac_refine_db: sqlite3.Connection,
) -> None:
    conn = sac_refine_db
    for i in range(2):
        oid = f"rec{i}"
        conn.execute(
            """
            INSERT INTO cards (
                oracle_id, name, type_line, oracle_text, mana_cost, cmc, color_identity,
                keywords, commander_legal, commander_eligible, is_basic_land, price_known
            ) VALUES (?, ?, 'Creature', '', '{2}', 2, '[]', '[]', 1, 0, 0, 1)
            """,
            (oid, f"Rec {i}"),
        )
        _insert_effect(conn, oid, "death_recursion", "death_recursion_persist")
    conn.commit()
    maindeck = [
        _deck_card(oracle_id="artist", name="Blood Artist", type_line="Creature"),
        _deck_card(oracle_id="rec0", name="Rec 0", type_line="Creature"),
        _deck_card(oracle_id="rec1", name="Rec 1", type_line="Creature"),
    ]
    report = validate_dependencies(
        conn,
        maindeck=maindeck,
        commanders=[],
        criteria=DeckCriteria(themes=["aristocrats"]),
    )
    assert not any(i.rule_id == "SACRIFICE_BALANCE" for i in report.warnings)


def test_grave_pact_style_opponent_sacrifice_suppresses_outlet_warn(
    sac_refine_db: sqlite3.Connection,
) -> None:
    conn = sac_refine_db
    conn.execute(
        """
        INSERT INTO cards (
            oracle_id, name, type_line, oracle_text, mana_cost, cmc, color_identity,
            keywords, commander_legal, commander_eligible, is_basic_land, price_known
        ) VALUES ('pact', 'Grave Pact', 'Enchantment', '', '{4}', 4, '[]', '[]', 1, 0, 0, 1)
        """
    )
    _insert_effect(conn, "pact", "sacrifice_payoff", "sacrifice_creature_dies_payoff")
    _insert_effect(conn, "pact", "sacrifice_opponent", "sacrifice_opponent_forced")
    conn.commit()
    maindeck = [
        _deck_card(oracle_id="artist", name="Blood Artist", type_line="Creature"),
        _deck_card(oracle_id="pact", name="Grave Pact", type_line="Enchantment"),
    ]
    report = validate_dependencies(
        conn,
        maindeck=maindeck,
        commanders=[],
        criteria=DeckCriteria(themes=["aristocrats"]),
    )
    assert not any(i.rule_id == "SACRIFICE_BALANCE" for i in report.warnings)
