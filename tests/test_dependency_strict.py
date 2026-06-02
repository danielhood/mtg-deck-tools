"""Strict dependency pick-time filter and post-build severity (D4)."""

from __future__ import annotations

import json
import sqlite3

import pytest

from mtg_deck_tools.builder.dependency_scoring import (
    DeckBuildStats,
    filter_strict_dependency_candidates,
    passes_strict_dependency_filter,
)
from mtg_deck_tools.builder.pool import CardCandidate
from mtg_deck_tools.db.schema import apply_schema
from mtg_deck_tools.builder.deck import DeckCard
from mtg_deck_tools.rules.dependencies import (
    CardEffectRow,
    dependency_messages,
    validate_dependencies,
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


def _candidate(
    *,
    oracle_id: str,
    name: str,
    type_line: str,
    cmc: float = 2.0,
) -> CardCandidate:
    return CardCandidate(
        oracle_id=oracle_id,
        name=name,
        cmc=cmc,
        type_line=type_line,
        mana_cost="{2}",
        color_identity=["G"],
        price_usd=1.0,
        price_known=True,
        edhrec_rank=None,
        oracle_text="",
        keywords=[],
        is_basic_land=False,
        produced_mana=[],
        scryfall_uri=None,
        image_uri=None,
    )


def _effect(kind: str, payload: dict) -> CardEffectRow:
    return CardEffectRow(
        oracle_id="x",
        effect_kind=kind,
        payload=payload,
        confidence=1.0,
        source=kind,
    )


def test_strict_rejects_tutor_with_no_targets() -> None:
    stats = DeckBuildStats()
    assert not passes_strict_dependency_filter(
        _candidate(oracle_id="t", name="Worldly Tutor", type_line="Instant"),
        [_effect("search_library", {"types": ["creature"]})],
        stats,
        [],
    )


def test_strict_rejects_energy_consumer_without_producers() -> None:
    stats = DeckBuildStats(energy_producers=0)
    assert not passes_strict_dependency_filter(
        _candidate(oracle_id="c", name="Payoff", type_line="Artifact"),
        [_effect("energy_consume", {"resource": "energy"})],
        stats,
        [],
    )


def test_strict_rejects_elf_lord_without_support() -> None:
    stats = DeckBuildStats(subtype_lord_minimums={"Elf": 5})
    assert not passes_strict_dependency_filter(
        _candidate(oracle_id="lord", name="Archdruid", type_line="Creature — Elf Druid"),
        [_effect("buff_subtype", {"subtypes": ["Elf"]})],
        stats,
        [],
    )


def test_strict_allows_tutor_when_creature_in_pool() -> None:
    stats = DeckBuildStats()
    assert passes_strict_dependency_filter(
        _candidate(oracle_id="t", name="Worldly Tutor", type_line="Instant"),
        [_effect("search_library", {"types": ["creature"]})],
        stats,
        [("Creature — Elf", 1.0)],
    )


@pytest.fixture
def strict_db() -> sqlite3.Connection:
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
        ) VALUES ('elf', 'Llanowar Elves', 'Creature — Elf', '', '{G}', 1, '["G"]', '[]', 1, 0, 0, 1)
        """
    )
    conn.commit()
    return conn


def test_filter_strict_dependency_candidates(strict_db: sqlite3.Connection) -> None:
    tutors = [
        _candidate(oracle_id="tutor", name="Worldly Tutor", type_line="Instant"),
    ]
    filtered = filter_strict_dependency_candidates(
        tutors,
        conn=strict_db,
        partial=[],
        commander_oracle_ids=set(),
    )
    assert filtered == []

    filtered_with_target = filter_strict_dependency_candidates(
        tutors,
        conn=strict_db,
        partial=[_deck_card(oracle_id="elf", name="Llanowar Elves", type_line="Creature — Elf", cmc=1.0)],
        commander_oracle_ids=set(),
    )
    assert len(filtered_with_target) == 1


def test_validate_dependencies_strict_marks_fail(strict_db: sqlite3.Connection) -> None:
    maindeck = [_deck_card(oracle_id="tutor", name="Worldly Tutor", type_line="Instant")]
    report = validate_dependencies(
        strict_db,
        maindeck=maindeck,
        commanders=[],
        strict=True,
    )
    assert not report.passed
    assert report.failures
    msgs = dependency_messages(report)
    assert any("strict" in m.lower() for m in msgs)
