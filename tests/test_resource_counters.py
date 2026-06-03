"""Resource counter balance (experience, blood, +1/+1)."""

from __future__ import annotations

import json
import sqlite3

import pytest

from mtg_deck_tools.builder.deck import DeckCard
from mtg_deck_tools.db.schema import apply_schema
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.rules.dependencies import validate_dependencies
from mtg_deck_tools.rules.dependency_scope import build_dependency_scope


def _deck_card(*, oracle_id: str, name: str, type_line: str) -> DeckCard:
    return DeckCard(
        oracle_id=oracle_id,
        name=name,
        slot="synergy",
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
def resource_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    apply_schema(conn)
    for oid, name in (("prod", "Producer"), ("cons", "Consumer"), ("solo", "Solo")):
        conn.execute(
            """
            INSERT INTO cards (
                oracle_id, name, type_line, oracle_text, mana_cost, cmc, color_identity,
                keywords, commander_legal, commander_eligible, is_basic_land, price_known
            ) VALUES (?, ?, 'Creature', '', '{2}', 2, '[]', '[]', 1, 0, 0, 1)
            """,
            (oid, name),
        )
    conn.commit()
    return conn


def test_experience_imbalance_with_intent(resource_db: sqlite3.Connection) -> None:
    _insert_effect(
        resource_db,
        "solo",
        "experience_produce",
        {"resource": "experience"},
        "experience_produce",
    )
    resource_db.commit()
    report = validate_dependencies(
        resource_db,
        maindeck=[_deck_card(oracle_id="solo", name="Solo", type_line="Creature")],
        commanders=[],
        criteria=DeckCriteria(include_mechanics=["experience"]),
    )
    assert any(i.rule_id == "EXPERIENCE_BALANCE" for i in report.warnings)


def test_experience_imbalance_silent_without_intent(resource_db: sqlite3.Connection) -> None:
    _insert_effect(
        resource_db,
        "solo",
        "experience_produce",
        {"resource": "experience"},
        "experience_produce",
    )
    resource_db.commit()
    report = validate_dependencies(
        resource_db,
        maindeck=[_deck_card(oracle_id="solo", name="Solo", type_line="Creature")],
        commanders=[],
    )
    assert not any(i.rule_id == "EXPERIENCE_BALANCE" for i in report.warnings)


def test_experience_scope_intent() -> None:
    scope = build_dependency_scope(DeckCriteria(include_mechanics=["experience"]))
    assert scope.resource_user_intent("experience")
    assert not scope.resource_user_intent("blood")


def test_balanced_experience_passes(resource_db: sqlite3.Connection) -> None:
    _insert_effect(
        resource_db,
        "prod",
        "experience_produce",
        {"resource": "experience"},
        "experience_produce",
    )
    _insert_effect(
        resource_db,
        "cons",
        "experience_consume",
        {"resource": "experience"},
        "experience_consume",
    )
    resource_db.commit()
    report = validate_dependencies(
        resource_db,
        maindeck=[
            _deck_card(oracle_id="prod", name="Producer", type_line="Creature"),
            _deck_card(oracle_id="cons", name="Consumer", type_line="Creature"),
        ],
        commanders=[],
        criteria=DeckCriteria(include_mechanics=["experience"]),
    )
    assert not any(i.rule_id == "EXPERIENCE_BALANCE" for i in report.issues)


def test_plus_one_four_producers_silent_without_counters_intent(
    resource_db: sqlite3.Connection,
) -> None:
    for i in range(4):
        oid = f"p{i}"
        resource_db.execute(
            """
            INSERT INTO cards (
                oracle_id, name, type_line, oracle_text, mana_cost, cmc, color_identity,
                keywords, commander_legal, commander_eligible, is_basic_land, price_known
            ) VALUES (?, ?, 'Creature', '', '{2}', 2, '[]', '[]', 1, 0, 0, 1)
            """,
            (oid, f"Producer {i}"),
        )
        _insert_effect(
            resource_db,
            oid,
            "plus_one_produce",
            {"resource": "plus_one"},
            "plus_one_produce",
        )
    resource_db.commit()
    maindeck = [
        _deck_card(oracle_id=f"p{i}", name=f"Producer {i}", type_line="Creature")
        for i in range(4)
    ]
    report = validate_dependencies(
        resource_db,
        maindeck=maindeck,
        commanders=[],
        criteria=DeckCriteria(themes=["tokens"]),
    )
    assert not any(i.rule_id == "PLUS_ONE_BALANCE" for i in report.issues)


def test_blood_produce_and_consume_on_same_card(resource_db: sqlite3.Connection) -> None:
    _insert_effect(
        resource_db,
        "solo",
        "blood_produce",
        {"resource": "blood"},
        "blood_produce",
    )
    _insert_effect(
        resource_db,
        "solo",
        "blood_consume",
        {"resource": "blood"},
        "blood_consume",
    )
    resource_db.commit()
    report = validate_dependencies(
        resource_db,
        maindeck=[_deck_card(oracle_id="solo", name="Font of Agonies", type_line="Enchantment")],
        commanders=[],
        criteria=DeckCriteria(include_mechanics=["blood"]),
    )
    assert not any(i.rule_id == "BLOOD_BALANCE" for i in report.issues)
