"""Dependency validation rules (D2)."""

from __future__ import annotations

import json
import sqlite3

import pytest

from mtg_deck_tools.builder.deck import DeckCard
from mtg_deck_tools.db.schema import apply_schema
from mtg_deck_tools.rules.dependencies import validate_dependencies


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
def dep_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    apply_schema(conn)
    conn.execute(
        """
        INSERT INTO cards (
            oracle_id, name, type_line, oracle_text, mana_cost, cmc, color_identity,
            keywords, commander_legal, commander_eligible, is_basic_land, price_known
        ) VALUES ('tutor', 'Worldly Tutor', 'Instant', '', '{1}{G}', 2, '["G"]', '[]', 1, 0, 0, 1)
        """
    )
    _insert_effect(
        conn,
        "tutor",
        "search_library",
        {"types": ["creature"]},
        "search_library_creature",
    )
    conn.execute(
        """
        INSERT INTO cards (
            oracle_id, name, type_line, oracle_text, mana_cost, cmc, color_identity,
            keywords, commander_legal, commander_eligible, is_basic_land, price_known
        ) VALUES ('lord', 'Elvish Archdruid', 'Creature — Elf Druid', '', '{1}{G}{G}', 3, '["G"]', '[]', 1, 0, 0, 1)
        """
    )
    _insert_effect(
        conn,
        "lord",
        "buff_subtype",
        {"subtypes": ["Elf"]},
        "buff_subtype_other",
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
    conn.commit()
    return conn


def test_tutor_without_targets_warns(dep_db: sqlite3.Connection) -> None:
    maindeck = [_deck_card(oracle_id="tutor", name="Worldly Tutor", type_line="Instant")]
    report = validate_dependencies(
        dep_db,
        maindeck=maindeck,
        commanders=[],
    )
    assert not report.passed
    assert any(i.rule_id == "TUTOR_TARGET_EXISTS" for i in report.warnings)


def test_tutor_with_creature_target_passes(dep_db: sqlite3.Connection) -> None:
    maindeck = [
        _deck_card(oracle_id="tutor", name="Worldly Tutor", type_line="Instant"),
        _deck_card(oracle_id="elf1", name="Llanowar Elves", type_line="Creature — Elf"),
    ]
    report = validate_dependencies(dep_db, maindeck=maindeck, commanders=[])
    tutor_issues = [i for i in report.issues if i.rule_id == "TUTOR_TARGET_EXISTS"]
    assert not tutor_issues


def test_elf_lord_low_count_warns(dep_db: sqlite3.Connection) -> None:
    maindeck = [
        _deck_card(oracle_id="lord", name="Elvish Archdruid", type_line="Creature — Elf Druid"),
        _deck_card(oracle_id="e1", name="Llanowar Elves", type_line="Creature — Elf"),
    ]
    report = validate_dependencies(dep_db, maindeck=maindeck, commanders=[])
    assert any(i.rule_id == "TYPE_SYNERGY_MIN" for i in report.warnings)


def test_energy_one_sided_warns(dep_db: sqlite3.Connection) -> None:
    maindeck = [_deck_card(oracle_id="hub", name="Aether Hub", type_line="Land", cmc=0.0)]
    report = validate_dependencies(dep_db, maindeck=maindeck, commanders=[])
    assert any(i.rule_id == "ENERGY_BALANCE" for i in report.warnings)
