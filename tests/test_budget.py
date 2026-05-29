"""Budget enforcement and land price scoring tests."""

from __future__ import annotations

import json
import sqlite3

import pytest

from mtg_deck_tools.builder.budget_backfill import (
    _replacement_price_cap,
    trim_deck_to_budget,
)
from mtg_deck_tools.builder.deck import DeckCard
from mtg_deck_tools.builder.filler import _filter_budget, fill_deck
from mtg_deck_tools.builder.pool import CardCandidate
from mtg_deck_tools.builder.scorer import score_land_budget
from mtg_deck_tools.db.schema import apply_schema
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.paths import TAXONOMY_PATH
from mtg_deck_tools.tags.tagger import Tagger, load_taxonomy


def _candidate(
    *,
    price_usd: float | None,
    price_known: bool = True,
    is_basic_land: bool = False,
) -> CardCandidate:
    return CardCandidate(
        oracle_id="x",
        name="Test",
        cmc=0.0,
        type_line="Land" if is_basic_land else "Creature",
        mana_cost="",
        color_identity=["G"],
        price_usd=price_usd,
        price_known=price_known,
        edhrec_rank=1000,
        oracle_text="",
        keywords=[],
        is_basic_land=is_basic_land,
        produced_mana=["G"],
        scryfall_uri=None,
        image_uri=None,
    )


def test_filter_budget_excludes_over_remaining() -> None:
    pool = [
        _candidate(price_usd=5.0),
        _candidate(price_usd=25.0),
        _candidate(price_usd=None, price_known=False),
    ]
    filtered = _filter_budget(pool, budget_remaining=10.0, strict=False)
    assert len(filtered) == 2
    assert all(c.price_usd is None or c.price_usd <= 10.0 for c in filtered)


def test_filter_budget_strict_excludes_unpriced() -> None:
    pool = [
        _candidate(price_usd=5.0),
        _candidate(price_usd=None, price_known=False),
    ]
    filtered = _filter_budget(pool, budget_remaining=10.0, strict=True)
    assert len(filtered) == 1
    assert filtered[0].price_usd == 5.0


def test_score_land_budget_prefers_cheap() -> None:
    cheap = _candidate(price_usd=0.50)
    expensive = _candidate(price_usd=53.0)
    assert score_land_budget(
        cheap, budget_remaining=200.0, budget_total=200.0
    ) > score_land_budget(expensive, budget_remaining=200.0, budget_total=200.0)


def test_board_wipe_tag_not_windborn_muse() -> None:
    tagger = Tagger(load_taxonomy(TAXONOMY_PATH))
    result = tagger.tag_card(
        {
            "oracle_id": "x",
            "type_line": "Creature — Spirit",
            "oracle_text": (
                "Flying\nCreatures can't attack you or a planeswalker you control "
                "unless their controller pays {2} for each creature they control "
                "that's attacking you."
            ),
            "keywords": ["Flying"],
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


def test_wincon_tag_not_ramp_rock() -> None:
    tagger = Tagger(load_taxonomy(TAXONOMY_PATH))
    result = tagger.tag_card(
        {
            "oracle_id": "x",
            "type_line": "Artifact",
            "oracle_text": "{T}: Add one mana of any color in your commander's color identity.",
            "keywords": [],
        }
    )
    assert not any(a.tag == "wincon" for a in result)


def _insert_card(
    conn: sqlite3.Connection,
    *,
    oracle_id: str,
    name: str,
    color_identity: list[str],
    type_line: str,
    price_usd: float | None,
    slot_tag: str | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO cards (
            oracle_id, name, type_line, mana_cost, cmc, color_identity,
            keywords, commander_legal, commander_eligible, is_basic_land,
            edhrec_rank, price_usd, price_known
        ) VALUES (?, ?, ?, '', 2.0, ?, '[]', 1, 0, 0, 1000, ?, ?)
        """,
        (
            oracle_id,
            name,
            type_line,
            json.dumps(color_identity),
            price_usd,
            1 if price_usd is not None else 0,
        ),
    )
    if slot_tag:
        conn.execute(
            """
            INSERT INTO card_mechanic_tags (oracle_id, tag, layer, source)
            VALUES (?, ?, 'theme', 'test')
            """,
            (oracle_id, slot_tag),
        )


@pytest.fixture
def budget_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    apply_schema(conn)

    _insert_card(
        conn,
        oracle_id="cmd",
        name="Commander",
        color_identity=["G"],
        type_line="Legendary Creature",
        price_usd=1.0,
    )
    conn.execute("UPDATE cards SET commander_eligible = 1 WHERE oracle_id = 'cmd'")

    for i, price in enumerate((50.0, 5.0, 3.0, 2.0, 1.0)):
        _insert_card(
            conn,
            oracle_id=f"synergy-{i}",
            name=f"Synergy {i}",
            color_identity=["G"],
            type_line="Creature — Elf",
            price_usd=price,
            slot_tag="landfall",
        )

    _insert_card(
        conn,
        oracle_id="ramp-1",
        name="Cheap Ramp",
        color_identity=["G"],
        type_line="Artifact",
        price_usd=1.0,
        slot_tag="ramp",
    )
    _insert_card(
        conn,
        oracle_id="draw-1",
        name="Cheap Draw",
        color_identity=["G"],
        type_line="Sorcery",
        price_usd=1.0,
        slot_tag="draw",
    )
    _insert_card(
        conn,
        oracle_id="land-cheap",
        name="Cheap Land",
        color_identity=["G"],
        type_line="Land",
        price_usd=0.50,
    )
    conn.execute(
        "UPDATE cards SET produced_mana = ? WHERE oracle_id = 'land-cheap'",
        (json.dumps(["G"]),),
    )
    _insert_card(
        conn,
        oracle_id="land-pricey",
        name="Pricey Land",
        color_identity=["G"],
        type_line="Land",
        price_usd=40.0,
    )
    conn.execute(
        "UPDATE cards SET produced_mana = ? WHERE oracle_id = 'land-pricey'",
        (json.dumps(["G"]),),
    )
    _insert_card(
        conn,
        oracle_id="forest",
        name="Forest",
        color_identity=[],
        type_line="Basic Land — Forest",
        price_usd=0.1,
    )
    conn.execute("UPDATE cards SET is_basic_land = 1 WHERE oracle_id = 'forest'")
    conn.commit()
    return conn


def test_replacement_price_cap_when_already_over_budget() -> None:
    """Mirrors Dromoka trim failure: other_spent alone exceeds the cap."""
    cap = _replacement_price_cap(budget_cap=150.0, other_spent=179.46, card_price=32.94)
    assert cap > 0
    assert cap < 32.94


def test_trim_when_deck_already_over_cap(budget_db: sqlite3.Connection) -> None:
    """Trim must swap incrementally when priced total exceeds cap before any swap."""
    _insert_card(
        budget_db,
        oracle_id="syn-a",
        name="Synergy A",
        color_identity=["G"],
        type_line="Creature — Elf",
        price_usd=70.0,
        slot_tag="landfall",
    )
    _insert_card(
        budget_db,
        oracle_id="syn-b",
        name="Synergy B",
        color_identity=["G"],
        type_line="Creature — Elf",
        price_usd=65.0,
        slot_tag="landfall",
    )
    budget_db.commit()

    def _deck_card(oid: str, name: str, price: float) -> DeckCard:
        return DeckCard(
            oracle_id=oid,
            name=name,
            slot="synergy",
            quantity=1,
            cmc=3.0,
            mana_cost="{2}{G}",
            type_line="Creature — Elf",
            price_usd=price,
            price_known=True,
            scryfall_uri=None,
            image_uri=None,
            mechanic_tags=["landfall"],
        )

    cards = [
        _deck_card("synergy-0", "Synergy 0", 50.0),
        _deck_card("syn-a", "Synergy A", 70.0),
        _deck_card("syn-b", "Synergy B", 65.0),
    ]
    criteria = DeckCriteria(themes=["landfall"], colors=["G"], budget_usd=150.0)
    trimmed, spent, warnings = trim_deck_to_budget(
        budget_db,
        cards,
        criteria,
        identity=["G"],
        commander_oracle_ids={"cmd"},
        commander_theme_tags=set(),
        unpriced_names=[],
        warnings=[],
    )
    assert spent <= 150.0
    assert any("Budget trim: replaced" in w for w in warnings)


def test_trim_deck_to_budget_swaps_expensive_card(budget_db: sqlite3.Connection) -> None:
    cards = [
        DeckCard(
            oracle_id="synergy-0",
            name="Synergy 0",
            slot="synergy",
            quantity=1,
            cmc=3.0,
            mana_cost="{2}{G}",
            type_line="Creature — Elf",
            price_usd=50.0,
            price_known=True,
            scryfall_uri=None,
            image_uri=None,
            mechanic_tags=["landfall"],
        ),
        DeckCard(
            oracle_id="synergy-1",
            name="Synergy 1",
            slot="synergy",
            quantity=1,
            cmc=3.0,
            mana_cost="{2}{G}",
            type_line="Creature — Elf",
            price_usd=5.0,
            price_known=True,
            scryfall_uri=None,
            image_uri=None,
            mechanic_tags=["landfall"],
        ),
    ]
    criteria = DeckCriteria(
        themes=["landfall"],
        colors=["G"],
        budget_usd=10.0,
        seed=1,
    )
    trimmed, spent, warnings = trim_deck_to_budget(
        budget_db,
        cards,
        criteria,
        identity=["G"],
        commander_oracle_ids={"cmd"},
        commander_theme_tags=set(),
        unpriced_names=[],
        warnings=[],
    )
    assert spent <= 10.0
    assert any("Budget trim: replaced" in w for w in warnings)
    assert "Synergy 0" not in {c.name for c in trimmed}


def test_fill_deck_respects_budget_cap(budget_db: sqlite3.Connection) -> None:
    slots = {
        "ramp": 1,
        "draw": 1,
        "removal": 0,
        "board_wipe": 0,
        "synergy": 2,
        "wincon": 0,
        "flex": 0,
        "lands": 2,
    }
    criteria = DeckCriteria(
        themes=["landfall"],
        colors=["G"],
        commander_oracle_ids=["cmd"],
        slot_template=slots,
        budget_usd=15.0,
        seed=7,
    )
    result = fill_deck(
        budget_db,
        criteria,
        identity=["G"],
        commander_oracle_ids=["cmd"],
        seed=7,
    )
    assert result.budget_spent <= 15.0
