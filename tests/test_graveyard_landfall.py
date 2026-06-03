"""Graveyard / landfall heuristics (Priority 5)."""

from __future__ import annotations

import sqlite3

import pytest

from mtg_deck_tools.builder.deck import DeckCard
from mtg_deck_tools.db.schema import apply_schema
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.rules.dependencies import validate_dependencies
from mtg_deck_tools.rules.graveyard_landfall import (
    RULE_GRAVEYARD_COST_SUPPORT,
    RULE_LANDFALL_BALANCE,
    RULE_REANIMATION_SUPPORT,
    RULE_SELF_MILL_BALANCE,
    self_mill_balanced,
)


def _deck_card(
    *,
    oracle_id: str,
    name: str,
    type_line: str,
    cmc: float = 2.0,
) -> DeckCard:
    return DeckCard(
        oracle_id=oracle_id,
        name=name,
        slot="flex",
        quantity=1,
        cmc=cmc,
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


def _insert_card(
    conn: sqlite3.Connection,
    oracle_id: str,
    name: str,
    type_line: str,
    *,
    cmc: float = 2.0,
) -> None:
    conn.execute(
        """
        INSERT INTO cards (
            oracle_id, name, type_line, oracle_text, mana_cost, cmc, color_identity,
            keywords, commander_legal, commander_eligible, is_basic_land, price_known
        ) VALUES (?, ?, ?, '', '{2}', ?, '[]', '[]', 1, 0, 0, 1)
        """,
        (oracle_id, name, type_line, cmc),
    )


@pytest.fixture
def gy_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    apply_schema(conn)
    _insert_card(conn, "reanimate", "Reanimate", "Sorcery")
    _insert_effect(conn, "reanimate", "reanimate", "reanimate_return")
    conn.commit()
    return conn


def test_self_mill_balanced_helpers() -> None:
    assert self_mill_balanced(0, 0)
    assert self_mill_balanced(2, 1)
    assert not self_mill_balanced(2, 0)
    assert not self_mill_balanced(0, 2)


def test_reanimation_low_creature_count_warns(gy_db: sqlite3.Connection) -> None:
    maindeck = [
        _deck_card(oracle_id="reanimate", name="Reanimate", type_line="Sorcery"),
        _deck_card(oracle_id="c1", name="Bear", type_line="Creature — Bear"),
    ]
    report = validate_dependencies(gy_db, maindeck=maindeck, commanders=[])
    issues = [i for i in report.issues if i.rule_id == RULE_REANIMATION_SUPPORT]
    assert len(issues) == 1
    assert issues[0].detail.get("deficit") == "creatures"


def test_reanimation_enough_creatures_passes(gy_db: sqlite3.Connection) -> None:
    maindeck = [
        _deck_card(oracle_id="reanimate", name="Reanimate", type_line="Sorcery"),
    ] + [
        _deck_card(
            oracle_id=f"c{i}",
            name=f"Creature {i}",
            type_line="Creature",
            cmc=2.0,
        )
        for i in range(20)
    ]
    report = validate_dependencies(gy_db, maindeck=maindeck, commanders=[])
    assert not any(i.rule_id == RULE_REANIMATION_SUPPORT for i in report.issues)


def test_graveyard_cost_thin_deck_warns(gy_db: sqlite3.Connection) -> None:
    conn = gy_db
    for i in range(2):
        oid = f"delve{i}"
        _insert_card(conn, oid, f"Delve {i}", "Sorcery")
        _insert_effect(conn, oid, "graveyard_cost", "graveyard_cost_delve_flashback")
    conn.commit()
    maindeck = [
        _deck_card(oracle_id="delve0", name="Delve 0", type_line="Sorcery"),
        _deck_card(oracle_id="delve1", name="Delve 1", type_line="Sorcery"),
    ] + [
        _deck_card(oracle_id=f"n{i}", name=f"Spell {i}", type_line="Instant")
        for i in range(10)
    ]
    report = validate_dependencies(conn, maindeck=maindeck, commanders=[])
    assert any(i.rule_id == RULE_GRAVEYARD_COST_SUPPORT for i in report.warnings)


def test_graveyard_cost_single_card_silent(gy_db: sqlite3.Connection) -> None:
    conn = gy_db
    _insert_card(conn, "cruise", "Treasure Cruise", "Sorcery")
    _insert_effect(conn, "cruise", "graveyard_cost", "graveyard_cost_delve_flashback")
    conn.commit()
    maindeck = [_deck_card(oracle_id="cruise", name="Treasure Cruise", type_line="Sorcery")]
    report = validate_dependencies(conn, maindeck=maindeck, commanders=[])
    assert not any(i.rule_id == RULE_GRAVEYARD_COST_SUPPORT for i in report.issues)


def test_self_mill_imbalance_warns_with_recursion_intent(gy_db: sqlite3.Connection) -> None:
    conn = gy_db
    _insert_card(conn, "supplier", "Stitcher's Supplier", "Creature — Zombie")
    _insert_effect(conn, "supplier", "mill_enabler", "mill_enabler")
    conn.commit()
    maindeck = [
        _deck_card(oracle_id="supplier", name="Stitcher's Supplier", type_line="Creature"),
    ]
    report = validate_dependencies(
        conn,
        maindeck=maindeck,
        commanders=[],
        criteria=DeckCriteria(themes=["recursion"]),
    )
    assert any(i.rule_id == RULE_SELF_MILL_BALANCE for i in report.warnings)


def test_self_mill_single_enabler_silent_without_intent(gy_db: sqlite3.Connection) -> None:
    conn = gy_db
    _insert_card(conn, "supplier", "Stitcher's Supplier", "Creature — Zombie")
    _insert_effect(conn, "supplier", "mill_enabler", "mill_enabler")
    conn.commit()
    maindeck = [
        _deck_card(oracle_id="supplier", name="Stitcher's Supplier", type_line="Creature"),
    ]
    report = validate_dependencies(
        conn,
        maindeck=maindeck,
        commanders=[],
        criteria=DeckCriteria(themes=["tokens"]),
    )
    assert not any(i.rule_id == RULE_SELF_MILL_BALANCE for i in report.issues)


def test_landfall_balance_warns_with_landfall_theme(gy_db: sqlite3.Connection) -> None:
    conn = gy_db
    _insert_card(conn, "omnath", "Omnath, Locus of Rage", "Legendary Creature")
    _insert_effect(conn, "omnath", "landfall_payoff", "landfall_payoff")
    conn.commit()
    maindeck = [
        _deck_card(
            oracle_id="omnath",
            name="Omnath, Locus of Rage",
            type_line="Legendary Creature — Elemental",
        ),
    ]
    report = validate_dependencies(
        conn,
        maindeck=maindeck,
        commanders=[],
        criteria=DeckCriteria(themes=["landfall"]),
    )
    assert any(i.rule_id == RULE_LANDFALL_BALANCE for i in report.warnings)


def test_landfall_balance_passes_with_ramp(gy_db: sqlite3.Connection) -> None:
    conn = gy_db
    _insert_card(conn, "omnath", "Omnath, Locus of Rage", "Legendary Creature")
    _insert_effect(conn, "omnath", "landfall_payoff", "landfall_payoff")
    for i in range(8):
        oid = f"ramp{i}"
        _insert_card(conn, oid, f"Ramp {i}", "Sorcery")
        _insert_effect(conn, oid, "land_ramp", "land_ramp")
    conn.commit()
    maindeck = [
        _deck_card(
            oracle_id="omnath",
            name="Omnath, Locus of Rage",
            type_line="Legendary Creature — Elemental",
        ),
    ] + [
        _deck_card(oracle_id=f"ramp{i}", name=f"Ramp {i}", type_line="Sorcery")
        for i in range(8)
    ]
    report = validate_dependencies(
        conn,
        maindeck=maindeck,
        commanders=[],
        criteria=DeckCriteria(themes=["landfall"]),
    )
    assert not any(i.rule_id == RULE_LANDFALL_BALANCE for i in report.issues)
