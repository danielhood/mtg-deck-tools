"""Equipment depth validation and packages."""

from __future__ import annotations

import sqlite3

import pytest

from mtg_deck_tools.builder.deck import DeckCard
from mtg_deck_tools.db.schema import apply_schema
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.rules.dependencies import validate_dependencies
from mtg_deck_tools.rules.dependency_scope import build_dependency_scope
from mtg_deck_tools.rules.equipment_depth import RULE_EQUIPMENT_BALANCE


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


@pytest.fixture
def dep_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    apply_schema(conn)
    return conn


def test_build_dependency_scope_equip_include() -> None:
    scope = build_dependency_scope(DeckCriteria(include_mechanics=["equip"]))
    assert scope.equipment_user_intent
    assert not build_dependency_scope(DeckCriteria(themes=["ramp"])).equipment_user_intent


def test_build_dependency_scope_voltron_theme() -> None:
    scope = build_dependency_scope(DeckCriteria(themes=["voltron"]))
    assert scope.equipment_user_intent


def test_equipment_balance_warns_with_equip_intent(dep_db: sqlite3.Connection) -> None:
    maindeck = [
        _deck_card(oracle_id="sword", name="Sword", type_line="Artifact — Equipment"),
        _deck_card(oracle_id="bear", name="Bear", type_line="Creature — Bear"),
    ]
    report = validate_dependencies(
        dep_db,
        maindeck=maindeck,
        commanders=[],
        criteria=DeckCriteria(include_mechanics=["equip"]),
    )
    issues = [i for i in report.issues if i.rule_id == RULE_EQUIPMENT_BALANCE]
    assert issues
    assert issues[0].detail.get("deficit") == "equipment"


def test_equipment_carrier_warns_when_many_pieces_no_carriers(
    dep_db: sqlite3.Connection,
) -> None:
    maindeck = [
        _deck_card(oracle_id=f"eq{i}", name=f"Eq {i}", type_line="Artifact — Equipment")
        for i in range(5)
    ] + [
        _deck_card(oracle_id=f"c{i}", name=f"Cr {i}", type_line="Creature")
        for i in range(8)
    ]
    report = validate_dependencies(
        dep_db,
        maindeck=maindeck,
        commanders=[],
        criteria=DeckCriteria(themes=["ramp"]),
    )
    issues = [i for i in report.issues if i.rule_id == RULE_EQUIPMENT_BALANCE]
    assert len(issues) == 1
    assert issues[0].detail.get("deficit") == "carriers"


def test_equip_payoff_without_equipment_warns(dep_db: sqlite3.Connection) -> None:
    dep_db.execute(
        """
        INSERT INTO cards (
            oracle_id, name, type_line, oracle_text, mana_cost, cmc, color_identity,
            keywords, commander_legal, commander_eligible, is_basic_land, price_known
        ) VALUES (
            'duelist', 'Kor Duelist', 'Creature — Kor', '', '{W}', 1, '["W"]',
            '[]', 1, 0, 0, 1
        )
        """
    )
    dep_db.execute(
        """
        INSERT INTO card_effects (
            oracle_id, face_index, effect_kind, payload, confidence, source
        ) VALUES ('duelist', 0, 'whenever_equipped', '{}', 1.0, 'whenever_equipped_payoff')
        """
    )
    dep_db.commit()
    maindeck = [
        _deck_card(oracle_id="duelist", name="Kor Duelist", type_line="Creature — Kor"),
    ]
    report = validate_dependencies(
        dep_db,
        maindeck=maindeck,
        commanders=[],
        criteria=DeckCriteria(include_mechanics=["equip"]),
    )
    issues = [i for i in report.issues if i.rule_id == RULE_EQUIPMENT_BALANCE]
    assert issues
    assert issues[0].detail.get("deficit") == "equipment"


def test_single_equipment_silent_without_intent(dep_db: sqlite3.Connection) -> None:
    maindeck = [
        _deck_card(oracle_id="sword", name="Sword", type_line="Artifact — Equipment"),
    ]
    report = validate_dependencies(
        dep_db,
        maindeck=maindeck,
        commanders=[],
        criteria=DeckCriteria(themes=["ramp"]),
    )
    assert not any(i.rule_id == RULE_EQUIPMENT_BALANCE for i in report.issues)
