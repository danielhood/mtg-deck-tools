"""Slot filler tests with an in-memory card database."""

from __future__ import annotations

import json
import sqlite3

import pytest

from mtg_deck_tools.builder.filler import fill_deck
from mtg_deck_tools.builder.pool import fetch_candidates
from mtg_deck_tools.builder.scorer import score_candidate
from mtg_deck_tools.db.schema import apply_schema
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.wizard.slots import load_slot_template_config


def _insert_card(
    conn: sqlite3.Connection,
    *,
    oracle_id: str,
    name: str,
    color_identity: list[str],
    type_line: str,
    cmc: float = 2.0,
    mana_cost: str = "{1}{G}",
    is_basic_land: int = 0,
    commander_eligible: int = 0,
    edhrec_rank: int | None = 1000,
    price_usd: float | None = 1.0,
    oracle_text: str = "",
) -> None:
    conn.execute(
        """
        INSERT INTO cards (
            oracle_id, name, type_line, mana_cost, cmc, color_identity,
            keywords, commander_legal, commander_eligible, is_basic_land,
            edhrec_rank, price_usd, price_known
        ) VALUES (?, ?, ?, ?, ?, ?, '[]', 1, ?, ?, ?, ?, ?)
        """,
        (
            oracle_id,
            name,
            type_line,
            mana_cost,
            cmc,
            json.dumps(color_identity),
            commander_eligible,
            is_basic_land,
            edhrec_rank,
            price_usd,
            1 if price_usd is not None else 0,
        ),
    )
    if oracle_text:
        conn.execute(
            "UPDATE cards SET oracle_text = ? WHERE oracle_id = ?",
            (oracle_text, oracle_id),
        )


def _tag(conn: sqlite3.Connection, oracle_id: str, tag: str, layer: str = "theme") -> None:
    conn.execute(
        """
        INSERT INTO card_mechanic_tags (oracle_id, tag, layer, source)
        VALUES (?, ?, ?, 'test')
        """,
        (oracle_id, tag, layer),
    )


@pytest.fixture
def deck_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    apply_schema(conn)

    _insert_card(
        conn,
        oracle_id="cmd-1",
        name="Test Commander",
        color_identity=["G"],
        type_line="Legendary Creature — Elf",
        commander_eligible=1,
        edhrec_rank=100,
    )
    _insert_card(
        conn,
        oracle_id="ramp-1",
        name="Ramp Rock",
        color_identity=["G"],
        type_line="Artifact",
        cmc=2.0,
        oracle_text="Add {G}",
    )
    _tag(conn, "ramp-1", "ramp")
    _insert_card(
        conn,
        oracle_id="draw-1",
        name="Draw Spell",
        color_identity=["G"],
        type_line="Sorcery",
        cmc=3.0,
        oracle_text="Draw a card",
    )
    _tag(conn, "draw-1", "draw")
    _insert_card(
        conn,
        oracle_id="synergy-1",
        name="Token Maker",
        color_identity=["G"],
        type_line="Creature — Elf",
        oracle_text="Create a 1/1 token",
    )
    _tag(conn, "synergy-1", "tokens")
    _insert_card(
        conn,
        oracle_id="flyer-1",
        name="Flying Pest",
        color_identity=["G"],
        type_line="Creature — Insect",
    )
    _tag(conn, "flyer-1", "flying", layer="keyword")
    _insert_card(
        conn,
        oracle_id="land-1",
        name="Grove Land",
        color_identity=["G"],
        type_line="Land",
        cmc=0.0,
        mana_cost="",
        is_basic_land=0,
    )
    _insert_card(
        conn,
        oracle_id="forest-1",
        name="Forest",
        color_identity=[],
        type_line="Basic Land — Forest",
        cmc=0.0,
        mana_cost="",
        is_basic_land=1,
        price_usd=0.1,
    )
    conn.commit()
    return conn


def test_fetch_candidates_excludes_avoid_mechanics(deck_db: sqlite3.Connection) -> None:
    pool = fetch_candidates(
        deck_db,
        identity=["G"],
        exclude_oracle_ids=set(),
        exclude_names=set(),
        avoid_mechanics=["flying"],
        require_theme_tags=None,
        nonlands_only=True,
    )
    names = {c.name for c in pool}
    assert "Flying Pest" not in names
    assert "Ramp Rock" in names


def test_score_candidate_boosts_theme_overlap(deck_db: sqlite3.Connection) -> None:
    row = deck_db.execute(
        "SELECT * FROM cards WHERE oracle_id = 'synergy-1'"
    ).fetchone()
    from mtg_deck_tools.builder.pool import _row_to_candidate

    candidate = _row_to_candidate(row)
    score = score_candidate(
        candidate,
        slot="synergy",
        archetype_themes=["tokens"],
        include_mechanics=[],
        commander_theme_tags=set(),
        card_tags=["tokens"],
        type_counts={},
        budget_remaining=None,
    )
    assert score > 2.0


def test_fill_deck_respects_slot_counts(deck_db: sqlite3.Connection) -> None:
    slots = {
        "ramp": 1,
        "draw": 1,
        "removal": 0,
        "board_wipe": 0,
        "synergy": 1,
        "wincon": 0,
        "flex": 0,
        "lands": 2,
    }
    criteria = DeckCriteria(
        themes=["tokens"],
        colors=["G"],
        commander_oracle_ids=["cmd-1"],
        slot_template=slots,
        seed=42,
    )
    result = fill_deck(
        deck_db,
        criteria,
        identity=["G"],
        commander_oracle_ids=["cmd-1"],
        seed=42,
    )
    total = sum(c.quantity for c in result.cards)
    assert total == 5
    assert sum(1 for c in result.cards if c.slot == "ramp") == 1
    assert sum(c.quantity for c in result.cards if c.slot == "lands") == 2


def test_fill_deck_reproducible_with_seed(deck_db: sqlite3.Connection) -> None:
    slots = load_slot_template_config().default.copy()
    slots.update({"ramp": 1, "draw": 1, "removal": 0, "board_wipe": 0, "synergy": 1, "wincon": 0, "flex": 0, "lands": 1})
    criteria = DeckCriteria(
        themes=["tokens"],
        commander_oracle_ids=["cmd-1"],
        slot_template=slots,
        seed=99,
    )

    first = fill_deck(deck_db, criteria, identity=["G"], commander_oracle_ids=["cmd-1"], seed=99)
    second = fill_deck(deck_db, criteria, identity=["G"], commander_oracle_ids=["cmd-1"], seed=99)
    assert [(c.name, c.slot) for c in first.cards] == [(c.name, c.slot) for c in second.cards]
