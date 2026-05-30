"""Post-build dependency repair swaps (D5)."""

from __future__ import annotations

import json
import sqlite3

import pytest

from mtg_deck_tools.builder.deck import DeckCard
from mtg_deck_tools.builder.dependency_repair import repair_dependency_issues
from mtg_deck_tools.db.schema import apply_schema
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.rules.dependencies import validate_dependencies


def _deck_card(
    *,
    oracle_id: str,
    name: str,
    type_line: str,
    slot: str = "flex",
    cmc: float = 2.0,
) -> DeckCard:
    return DeckCard(
        oracle_id=oracle_id,
        name=name,
        slot=slot,
        quantity=1,
        cmc=cmc,
        mana_cost="{2}",
        type_line=type_line,
        price_usd=1.0,
        price_known=True,
        scryfall_uri=None,
        image_uri=None,
    )


def _insert_card(
    conn: sqlite3.Connection,
    *,
    oracle_id: str,
    name: str,
    type_line: str,
    cmc: float = 2.0,
) -> None:
    conn.execute(
        """
        INSERT INTO cards (
            oracle_id, name, type_line, oracle_text, mana_cost, cmc, color_identity,
            keywords, commander_legal, commander_eligible, is_basic_land, price_known
        ) VALUES (?, ?, ?, '', '{2}', ?, '["G"]', '[]', 1, 0, 0, 1)
        """,
        (oracle_id, name, type_line, cmc),
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
def repair_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    apply_schema(conn)
    _insert_card(conn, oracle_id="tutor", name="Worldly Tutor", type_line="Instant", cmc=2.0)
    _insert_effect(
        conn,
        "tutor",
        "search_library",
        {"types": ["creature"]},
        "search_library_creature",
    )
    _insert_card(conn, oracle_id="filler", name="Cancel", type_line="Instant", cmc=2.0)
    _insert_card(conn, oracle_id="elf", name="Llanowar Elves", type_line="Creature — Elf", cmc=1.0)
    _insert_card(conn, oracle_id="hub", name="Aether Hub", type_line="Land", cmc=0.0)
    _insert_effect(conn, "hub", "energy_produce", {"resource": "energy"}, "energy_produce")
    _insert_card(conn, oracle_id="payoff", name="Attune with Aether", type_line="Sorcery", cmc=2.0)
    _insert_effect(conn, "payoff", "energy_consume", {"resource": "energy"}, "energy_consume")
    conn.commit()
    return conn


def test_repair_adds_tutor_target(repair_db: sqlite3.Connection) -> None:
    cards = [
        _deck_card(oracle_id="tutor", name="Worldly Tutor", type_line="Instant", slot="removal"),
        _deck_card(oracle_id="filler", name="Cancel", type_line="Instant", slot="flex"),
    ]
    criteria = DeckCriteria(colors=["G"], repair_dependencies=True)
    result = repair_dependency_issues(
        repair_db,
        cards,
        criteria=criteria,
        identity=["G"],
        commanders=[],
        commander_oracle_ids=set(),
        commander_theme_tags=set(),
    )
    assert result.swaps >= 1
    report = validate_dependencies(repair_db, maindeck=result.cards, commanders=[])
    tutor_issues = [i for i in report.issues if i.rule_id == "TUTOR_TARGET_EXISTS"]
    assert not tutor_issues
    assert any(c.oracle_id == "elf" for c in result.cards)


def test_repair_adds_energy_consumer(repair_db: sqlite3.Connection) -> None:
    cards = [
        _deck_card(oracle_id="hub", name="Aether Hub", type_line="Land", slot="lands", cmc=0.0),
        _deck_card(oracle_id="filler", name="Cancel", type_line="Instant", slot="flex"),
    ]
    criteria = DeckCriteria(colors=["G"], repair_dependencies=True)
    result = repair_dependency_issues(
        repair_db,
        cards,
        criteria=criteria,
        identity=["G"],
        commanders=[],
        commander_oracle_ids=set(),
        commander_theme_tags=set(),
    )
    assert result.swaps >= 1
    assert any(c.oracle_id == "payoff" for c in result.cards)


def test_repair_noop_when_passing(repair_db: sqlite3.Connection) -> None:
    cards = [
        _deck_card(oracle_id="tutor", name="Worldly Tutor", type_line="Instant", slot="removal"),
        _deck_card(oracle_id="elf", name="Llanowar Elves", type_line="Creature — Elf", slot="flex"),
    ]
    criteria = DeckCriteria(colors=["G"], repair_dependencies=True)
    result = repair_dependency_issues(
        repair_db,
        cards,
        criteria=criteria,
        identity=["G"],
        commanders=[],
        commander_oracle_ids=set(),
        commander_theme_tags=set(),
    )
    assert result.swaps == 0
