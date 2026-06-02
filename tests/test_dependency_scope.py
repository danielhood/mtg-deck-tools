"""Dependency profile scoping and calibration (post-D5)."""

from __future__ import annotations

import json
import sqlite3

import pytest

from mtg_deck_tools.builder.deck import DeckCard
from mtg_deck_tools.db.schema import apply_schema
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.rules.dependencies import validate_dependencies
from mtg_deck_tools.rules.dependency_scope import build_dependency_scope


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
        slot="synergy",
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
def scope_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    apply_schema(conn)
    conn.execute(
        """
        INSERT INTO cards (
            oracle_id, name, type_line, oracle_text, mana_cost, cmc, color_identity,
            keywords, commander_legal, commander_eligible, is_basic_land, price_known
        ) VALUES ('aura1', 'Ethereal Armor', 'Enchantment — Aura', '', '{W}', 1, '["W"]', '[]', 1, 0, 0, 1)
        """
    )
    conn.execute(
        """
        INSERT INTO cards (
            oracle_id, name, type_line, oracle_text, mana_cost, cmc, color_identity,
            keywords, commander_legal, commander_eligible, is_basic_land, price_known
        ) VALUES ('payoff', 'Enchantress', 'Creature', '', '{2}{G}', 3, '["G"]', '[]', 1, 0, 0, 1)
        """
    )
    _insert_effect(
        conn,
        "payoff",
        "whenever_cast_enchantment",
        {"types": ["enchantment"]},
        "whenever_cast_enchantment",
    )
    conn.execute(
        """
        INSERT INTO cards (
            oracle_id, name, type_line, oracle_text, mana_cost, cmc, color_identity,
            keywords, commander_legal, commander_eligible, is_basic_land, price_known
        ) VALUES ('hub', 'Aether Hub', 'Land', '', '', 0, '["G"]', '[]', 1, 0, 0, 1)
        """
    )
    _insert_effect(conn, "hub", "energy_produce", {"resource": "energy"}, "energy_produce")
    conn.execute(
        """
        INSERT INTO cards (
            oracle_id, name, type_line, oracle_text, mana_cost, cmc, color_identity,
            keywords, commander_legal, commander_eligible, is_basic_land, price_known
        ) VALUES ('ramp', 'Rampant Growth', 'Sorcery', '', '{1}{G}', 2, '["G"]', '[]', 1, 0, 0, 1)
        """
    )
    _insert_effect(
        conn,
        "ramp",
        "search_library",
        {"types": ["land"], "supertypes": ["basic"]},
        "search_library_basic_land",
    )
    conn.execute(
        """
        INSERT INTO cards (
            oracle_id, name, type_line, oracle_text, mana_cost, cmc, color_identity,
            keywords, commander_legal, commander_eligible, is_basic_land, price_known
        ) VALUES ('forest', 'Forest', 'Basic Land — Forest', '', '', 0, '[]', '[]', 1, 0, 1, 1)
        """
    )
    conn.commit()
    return conn


def test_build_dependency_scope_voltron_enables_aura() -> None:
    scope = build_dependency_scope(DeckCriteria(themes=["tokens"]))
    assert not scope.aura_support_min
    scope_v = build_dependency_scope(DeckCriteria(themes=["voltron"]))
    assert scope_v.aura_support_min


def test_build_dependency_scope_vehicles_include() -> None:
    scope = build_dependency_scope(DeckCriteria(include_mechanics=["vehicles"]))
    assert scope.vehicles_user_intent
    scope_off = build_dependency_scope(DeckCriteria(themes=["tokens"]))
    assert not scope_off.vehicles_user_intent


def test_incidental_aura_does_not_trigger_support_min(scope_db: sqlite3.Connection) -> None:
    maindeck = [_deck_card(oracle_id="aura1", name="Ethereal Armor", type_line="Enchantment — Aura")]
    report = validate_dependencies(
        scope_db,
        maindeck=maindeck,
        commanders=[],
        criteria=DeckCriteria(themes=["tokens"]),
    )
    assert not any(i.rule_id == "AURA_SUPPORT_MIN" for i in report.issues)


def test_enchantment_cast_payoff_does_not_trigger_aura_support_min(
    scope_db: sqlite3.Connection,
) -> None:
    """Generic enchantment payoffs are not voltron aura support (see whenever_cast_aura)."""
    maindeck = [
        _deck_card(oracle_id="aura1", name="Ethereal Armor", type_line="Enchantment — Aura"),
        _deck_card(oracle_id="payoff", name="Enchantress", type_line="Creature"),
    ]
    report = validate_dependencies(
        scope_db,
        maindeck=maindeck,
        commanders=[],
        criteria=DeckCriteria(themes=["tokens"]),
    )
    assert not any(i.rule_id == "AURA_SUPPORT_MIN" for i in report.issues)


def test_enchantment_cast_payoff_triggers_enchantment_support_min(
    scope_db: sqlite3.Connection,
) -> None:
    maindeck = [
        _deck_card(oracle_id="payoff", name="Enchantress", type_line="Creature"),
    ]
    report = validate_dependencies(
        scope_db,
        maindeck=maindeck,
        commanders=[],
        criteria=DeckCriteria(themes=["tokens"]),
    )
    assert any(i.rule_id == "ENCHANTMENT_SUPPORT_MIN" for i in report.issues)
    assert not any(i.rule_id == "AURA_SUPPORT_MIN" for i in report.issues)


def test_enchantress_theme_triggers_enchantment_support_min(
    scope_db: sqlite3.Connection,
) -> None:
    maindeck = [
        _deck_card(
            oracle_id="enc1",
            name="Sterling Grove",
            type_line="Enchantment",
        ),
    ]
    report = validate_dependencies(
        scope_db,
        maindeck=maindeck,
        commanders=[],
        criteria=DeckCriteria(themes=["enchantress"]),
    )
    assert any(i.rule_id == "ENCHANTMENT_SUPPORT_MIN" for i in report.issues)
    assert not any(i.rule_id == "AURA_SUPPORT_MIN" for i in report.issues)


def test_build_dependency_scope_enchantress_enables_enchantments() -> None:
    scope = build_dependency_scope(DeckCriteria(themes=["enchantress"]))
    assert scope.enchantments_user_intent
    assert scope.enchantment_support_min
    scope_off = build_dependency_scope(DeckCriteria(themes=["tokens"]))
    assert not scope_off.enchantments_user_intent


def test_aura_cast_payoff_triggers_aura_support_min(scope_db: sqlite3.Connection) -> None:
    _insert_effect(
        scope_db,
        "payoff",
        "whenever_cast_aura",
        {"types": ["enchantment"], "subtypes": ["Aura"]},
        "whenever_cast_aura",
    )
    scope_db.commit()
    maindeck = [
        _deck_card(oracle_id="aura1", name="Ethereal Armor", type_line="Enchantment — Aura"),
        _deck_card(oracle_id="payoff", name="Aura Sage", type_line="Creature"),
    ]
    report = validate_dependencies(
        scope_db,
        maindeck=maindeck,
        commanders=[],
        criteria=DeckCriteria(themes=["tokens"]),
    )
    assert any(i.rule_id == "AURA_SUPPORT_MIN" for i in report.issues)


def test_voltron_theme_triggers_aura_support_min(scope_db: sqlite3.Connection) -> None:
    maindeck = [_deck_card(oracle_id="aura1", name="Ethereal Armor", type_line="Enchantment — Aura")]
    report = validate_dependencies(
        scope_db,
        maindeck=maindeck,
        commanders=[],
        criteria=DeckCriteria(themes=["voltron"]),
    )
    assert any(i.rule_id == "AURA_SUPPORT_MIN" for i in report.issues)


def test_single_energy_producer_silent_without_intent(scope_db: sqlite3.Connection) -> None:
    maindeck = [_deck_card(oracle_id="hub", name="Aether Hub", type_line="Land", cmc=0.0)]
    report = validate_dependencies(
        scope_db,
        maindeck=maindeck,
        commanders=[],
        criteria=DeckCriteria(themes=["tokens"]),
    )
    assert not any(i.rule_id == "ENERGY_BALANCE" for i in report.issues)


def test_energy_include_triggers_balance_warn(scope_db: sqlite3.Connection) -> None:
    maindeck = [_deck_card(oracle_id="hub", name="Aether Hub", type_line="Land", cmc=0.0)]
    report = validate_dependencies(
        scope_db,
        maindeck=maindeck,
        commanders=[],
        criteria=DeckCriteria(include_mechanics=["energy"]),
    )
    assert any(i.rule_id == "ENERGY_BALANCE" for i in report.issues)


def test_land_tutor_with_basics_passes(scope_db: sqlite3.Connection) -> None:
    maindeck = [
        _deck_card(oracle_id="ramp", name="Rampant Growth", type_line="Sorcery"),
        _deck_card(oracle_id="forest", name="Forest", type_line="Basic Land — Forest", cmc=0.0),
    ]
    report = validate_dependencies(scope_db, maindeck=maindeck, commanders=[])
    tutor_issues = [i for i in report.issues if i.rule_id == "TUTOR_TARGET_EXISTS"]
    assert not tutor_issues
