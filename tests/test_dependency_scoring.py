"""Pick-time dependency scoring during slot fill (D3)."""

from __future__ import annotations

import json
import sqlite3

import pytest

from mtg_deck_tools.builder.dependency_scoring import (
    DeckBuildStats,
    build_deck_build_stats,
    count_search_targets,
    dependency_pick_score,
)
from mtg_deck_tools.builder.deck import DeckCard
from mtg_deck_tools.builder.pool import CardCandidate
from mtg_deck_tools.builder.scorer import score_candidate
from mtg_deck_tools.db.schema import apply_schema
from mtg_deck_tools.rules.dependencies import CardEffectRow


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


def _effect(kind: str, payload: dict, *, confidence: float = 1.0) -> CardEffectRow:
    return CardEffectRow(
        oracle_id="x",
        effect_kind=kind,
        payload=payload,
        confidence=confidence,
        source=kind,
    )


def test_energy_consumer_boosted_when_producers_present() -> None:
    stats = DeckBuildStats(energy_producers=2, needs_energy_consumer=True)
    effects = [_effect("energy_consume", {"resource": "energy"})]
    score = dependency_pick_score(
        _candidate(oracle_id="c", name="Attune", type_line="Sorcery"),
        effects,
        stats,
        [],
    )
    assert score >= 5.0


def test_energy_producer_boosted_when_consumers_present() -> None:
    stats = DeckBuildStats(energy_consumers=1, needs_energy_producer=True)
    effects = [_effect("energy_produce", {"resource": "energy"})]
    score = dependency_pick_score(
        _candidate(oracle_id="p", name="Hub", type_line="Land"),
        effects,
        stats,
        [],
    )
    assert score >= 3.5


def test_tutor_penalized_without_search_targets() -> None:
    stats = DeckBuildStats()
    effects = [_effect("search_library", {"types": ["creature"]})]
    score = dependency_pick_score(
        _candidate(oracle_id="t", name="Worldly Tutor", type_line="Instant"),
        effects,
        stats,
        [],
    )
    assert score <= -10.0


def test_elf_candidate_boosted_when_lord_needs_support() -> None:
    stats = DeckBuildStats(needs_subtype_support={"Elf": True})
    score = dependency_pick_score(
        _candidate(oracle_id="e", name="Llanowar Elves", type_line="Creature — Elf"),
        [],
        stats,
        [],
    )
    assert score >= 2.5


def test_count_search_targets_creature() -> None:
    pool = [
        ("Creature — Elf", 1.0, ("G",), "Llanowar Elves"),
        ("Instant", 2.0, (), "Lightning Bolt"),
    ]
    assert count_search_targets(pool, {"types": ["creature"]}) == 1


@pytest.fixture
def scoring_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    apply_schema(conn)
    conn.execute(
        """
        INSERT INTO cards (
            oracle_id, name, type_line, oracle_text, mana_cost, cmc, color_identity,
            keywords, commander_legal, commander_eligible, is_basic_land, price_known
        ) VALUES ('hub', 'Aether Hub', 'Land', '', '', 0, '["G"]', '[]', 1, 0, 0, 1)
        """
    )
    conn.execute(
        """
        INSERT INTO card_effects (
            oracle_id, face_index, effect_kind, payload, confidence, source
        ) VALUES ('hub', 0, 'energy_produce', ?, 1.0, 'energy_produce')
        """,
        (json.dumps({"resource": "energy"}),),
    )
    conn.execute(
        """
        INSERT INTO cards (
            oracle_id, name, type_line, oracle_text, mana_cost, cmc, color_identity,
            keywords, commander_legal, commander_eligible, is_basic_land, price_known
        ) VALUES ('payoff', 'Aetherworks Marvel', 'Artifact', '', '{4}', 4, '["G"]', '[]', 1, 0, 0, 1)
        """
    )
    conn.execute(
        """
        INSERT INTO card_effects (
            oracle_id, face_index, effect_kind, payload, confidence, source
        ) VALUES ('payoff', 0, 'energy_consume', ?, 1.0, 'energy_consume')
        """,
        (json.dumps({"resource": "energy"}),),
    )
    conn.commit()
    return conn


def test_build_deck_build_stats_energy_gap(scoring_db: sqlite3.Connection) -> None:
    partial = [_deck_card(oracle_id="hub", name="Aether Hub", type_line="Land", cmc=0.0)]
    stats = build_deck_build_stats(scoring_db, partial)
    assert stats.energy_producers == 1
    assert stats.needs_energy_consumer


def test_build_deck_build_stats_energy_floors_when_included(
    scoring_db: sqlite3.Connection,
) -> None:
    from mtg_deck_tools.models.criteria import DeckCriteria

    partial = [_deck_card(oracle_id="hub", name="Aether Hub", type_line="Land", cmc=0.0)]
    stats = build_deck_build_stats(
        scoring_db,
        partial,
        criteria=DeckCriteria(include_mechanics=["energy"]),
    )
    assert stats.energy_package_requested
    assert stats.energy_producer_floor == 2
    assert stats.needs_energy_producer


def test_score_candidate_prefers_energy_payoff_after_producer(
    scoring_db: sqlite3.Connection,
) -> None:
    partial = [_deck_card(oracle_id="hub", name="Aether Hub", type_line="Land", cmc=0.0)]
    stats = build_deck_build_stats(scoring_db, partial)
    payoff = _candidate(oracle_id="payoff", name="Aetherworks Marvel", type_line="Artifact", cmc=4.0)
    filler = _candidate(oracle_id="filler", name="Grizzly Bears", type_line="Creature — Bear", cmc=2.0)
    payoff_effects = [
        CardEffectRow(
            oracle_id="payoff",
            effect_kind="energy_consume",
            payload={"resource": "energy"},
            confidence=1.0,
            source="energy_consume",
        )
    ]
    kwargs = dict(
        slot="synergy",
        archetype_themes=[],
        include_mechanics=[],
        commander_theme_tags=set(),
        card_tags=[],
        type_counts={},
        budget_remaining=None,
        deck_stats=stats,
        search_pool=[("Land", 0.0)],
    )
    assert score_candidate(
        payoff,
        candidate_effects=payoff_effects,
        **kwargs,
    ) > score_candidate(filler, candidate_effects=[], **kwargs)
