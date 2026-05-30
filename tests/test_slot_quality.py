"""Slot pool quality: oracle guards, relaxation, and scoring."""

from __future__ import annotations

import json
import sqlite3

import pytest

from mtg_deck_tools.builder.filler import fill_deck
from mtg_deck_tools.builder.pool import CardCandidate
from mtg_deck_tools.builder.scorer import score_candidate
from mtg_deck_tools.builder.slot_quality import (
    passes_slot_oracle_guard,
    refine_slot_candidates,
    slot_relax_steps,
)
from mtg_deck_tools.db.schema import apply_schema
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.paths import TAXONOMY_PATH
from mtg_deck_tools.tags.tagger import Tagger, load_taxonomy


def _candidate(
    *,
    oracle_id: str = "x",
    name: str = "Test",
    type_line: str = "Sorcery",
    oracle_text: str = "",
    cmc: float = 4.0,
    is_basic_land: bool = False,
    price_usd: float | None = 5.0,
) -> CardCandidate:
    return CardCandidate(
        oracle_id=oracle_id,
        name=name,
        cmc=cmc,
        type_line=type_line,
        mana_cost="{2}{G}",
        color_identity=["G"],
        price_usd=price_usd,
        price_known=price_usd is not None,
        edhrec_rank=1000,
        oracle_text=oracle_text,
        keywords=[],
        is_basic_land=is_basic_land,
        produced_mana=[],
        scryfall_uri=None,
        image_uri=None,
    )


def test_board_wipe_tag_not_worldslayer() -> None:
    tagger = Tagger(load_taxonomy(TAXONOMY_PATH))
    result = tagger.tag_card(
        {
            "oracle_id": "x",
            "type_line": "Artifact — Equipment",
            "oracle_text": (
                "Whenever equipped creature deals combat damage to a player, "
                "destroy all permanents."
            ),
            "keywords": ["Equip"],
        }
    )
    assert not any(a.tag == "board_wipe" for a in result)


def test_board_wipe_tag_matches_wrath() -> None:
    tagger = Tagger(load_taxonomy(TAXONOMY_PATH))
    result = tagger.tag_card(
        {
            "oracle_id": "x",
            "type_line": "Sorcery",
            "oracle_text": "Destroy all creatures. They can't be regenerated.",
            "keywords": [],
        }
    )
    assert any(a.tag == "board_wipe" for a in result)


def test_passes_slot_oracle_guard_rejects_worldslayer() -> None:
    worldslayer = _candidate(
        oracle_id="ws",
        name="Worldslayer",
        type_line="Artifact — Equipment",
        oracle_text=(
            "Whenever equipped creature deals combat damage to a player, "
            "destroy all permanents."
        ),
    )
    assert not passes_slot_oracle_guard(worldslayer, "board_wipe", ["board_wipe"])


def test_passes_slot_oracle_guard_accepts_wrath() -> None:
    wrath = _candidate(
        oracle_id="wr",
        name="Wrath of God",
        type_line="Sorcery",
        oracle_text="Destroy all creatures. They can't be regenerated.",
    )
    assert passes_slot_oracle_guard(wrath, "board_wipe", ["board_wipe"])


def test_slot_relax_steps_flex_uses_themes_before_untagged() -> None:
    criteria = DeckCriteria(themes=["voltron", "landfall"], colors=["G"])
    steps = slot_relax_steps("flex", criteria)
    assert steps == [["voltron", "landfall"], None]


def test_slot_relax_steps_wincon_includes_themed_fallback() -> None:
    criteria = DeckCriteria(themes=["voltron"], colors=["G"])
    steps = slot_relax_steps("wincon", criteria)
    assert steps[0] == ["wincon"]
    assert steps[1] == ["voltron"]
    assert steps[-1] is None


def test_refine_slot_candidates_drops_equipment_board_wipes() -> None:
    wrath = _candidate(
        oracle_id="wr",
        name="Wrath of God",
        type_line="Sorcery",
        oracle_text="Destroy all creatures. They can't be regenerated.",
    )
    worldslayer = _candidate(
        oracle_id="ws",
        name="Worldslayer",
        type_line="Artifact — Equipment",
        oracle_text=(
            "Whenever equipped creature deals combat damage to a player, "
            "destroy all permanents."
        ),
    )
    tag_map = {"wr": ["board_wipe"], "ws": ["board_wipe"]}
    criteria = DeckCriteria(colors=["G"])
    refined = refine_slot_candidates(
        "board_wipe",
        [worldslayer, wrath],
        tag_map,
        criteria=criteria,
        require_theme_tags=["board_wipe"],
    )
    assert [c.name for c in refined] == ["Wrath of God"]


def test_score_candidate_penalizes_unpriced_wincon_when_budget_set() -> None:
    priced = _candidate(
        oracle_id="p",
        name="Priced Threat",
        type_line="Creature — Beast",
        oracle_text="Trample",
        price_usd=3.0,
    )
    unpriced = _candidate(
        oracle_id="u",
        name="Unpriced Threat",
        type_line="Creature — Beast",
        oracle_text="Trample",
        price_usd=None,
    )
    kwargs = dict(
        slot="wincon",
        archetype_themes=["voltron"],
        include_mechanics=[],
        commander_theme_tags=set(),
        card_tags=["voltron"],
        type_counts={},
        budget_remaining=50.0,
        budget_usd=150.0,
    )
    assert score_candidate(priced, **kwargs) > score_candidate(unpriced, **kwargs)


def _insert_card(
    conn: sqlite3.Connection,
    *,
    oracle_id: str,
    name: str,
    type_line: str,
    oracle_text: str,
    tag: str,
    price_usd: float,
) -> None:
    conn.execute(
        """
        INSERT INTO cards (
            oracle_id, name, type_line, mana_cost, cmc, color_identity,
            keywords, commander_legal, commander_eligible, is_basic_land,
            edhrec_rank, price_usd, price_known, oracle_text
        ) VALUES (?, ?, ?, '{2}{G}', 4.0, ?, '[]', 1, 0, 0, 500, ?, 1, ?)
        """,
        (oracle_id, name, type_line, json.dumps(["G"]), price_usd, oracle_text),
    )
    conn.execute(
        """
        INSERT INTO card_mechanic_tags (oracle_id, tag, layer, source)
        VALUES (?, ?, 'theme', 'test')
        """,
        (oracle_id, tag),
    )


@pytest.fixture
def wipe_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    apply_schema(conn)
    _insert_card(
        conn,
        oracle_id="cmd",
        name="Commander",
        type_line="Legendary Creature — Human",
        oracle_text="",
        tag="voltron",
        price_usd=2.0,
    )
    conn.execute("UPDATE cards SET commander_eligible = 1 WHERE oracle_id = 'cmd'")
    _insert_card(
        conn,
        oracle_id="wrath",
        name="Wrath of God",
        type_line="Sorcery",
        oracle_text="Destroy all creatures. They can't be regenerated.",
        tag="board_wipe",
        price_usd=4.0,
    )
    _insert_card(
        conn,
        oracle_id="worldslayer",
        name="Worldslayer",
        type_line="Artifact — Equipment",
        oracle_text=(
            "Whenever equipped creature deals combat damage to a player, "
            "destroy all permanents."
        ),
        tag="board_wipe",
        price_usd=3.0,
    )
    _insert_card(
        conn,
        oracle_id="forest",
        name="Forest",
        type_line="Basic Land — Forest",
        oracle_text="",
        tag="ramp",
        price_usd=0.1,
    )
    conn.execute("UPDATE cards SET is_basic_land = 1, cmc = 0, mana_cost = '' WHERE oracle_id = 'forest'")
    conn.commit()
    return conn


def test_fill_deck_board_wipe_prefers_real_mass_removal(wipe_db: sqlite3.Connection) -> None:
    criteria = DeckCriteria(
        themes=["voltron"],
        colors=["G"],
        commander_oracle_ids=["cmd"],
        slot_template={
            "ramp": 0,
            "draw": 0,
            "removal": 0,
            "board_wipe": 1,
            "synergy": 0,
            "wincon": 0,
            "flex": 0,
            "lands": 1,
        },
        seed=1,
        budget_usd=150.0,
    )
    result = fill_deck(
        wipe_db,
        criteria,
        identity=["G"],
        commander_oracle_ids=["cmd"],
        seed=1,
    )
    wipe_cards = [c for c in result.cards if c.slot == "board_wipe"]
    assert len(wipe_cards) == 1
    assert wipe_cards[0].name == "Wrath of God"
