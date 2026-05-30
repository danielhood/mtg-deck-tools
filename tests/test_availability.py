"""Availability score, classification, and pool filters."""

from __future__ import annotations

import json
import sqlite3

import pytest

from mtg_deck_tools.availability.score import (
    classify_unpriced_card,
    compute_availability_score,
    format_unpriced_warning,
    get_availability_p25,
    record_availability_percentile,
)
from mtg_deck_tools.builder.availability_filters import filter_candidates_by_availability
from mtg_deck_tools.builder.pool import CardCandidate
from mtg_deck_tools.db.schema import apply_schema
from mtg_deck_tools.import_.normalize import normalize_card
from mtg_deck_tools.models.criteria import DeckCriteria


def test_compute_availability_score_priced_popular() -> None:
    score = compute_availability_score(
        price_known=True,
        edhrec_rank=200,
        released_at="2015-01-01",
        set_type="commander",
        reprint=True,
    )
    assert score >= 80.0


def test_compute_availability_score_obscure_unpriced() -> None:
    score = compute_availability_score(
        price_known=False,
        edhrec_rank=25000,
        released_at="1994-10-01",
        set_type="promo",
        reprint=False,
    )
    assert score < 40.0


def test_classify_unpriced_new_vs_obscure() -> None:
    assert (
        classify_unpriced_card(edhrec_rank=5000, released_at="2026-03-01")
        == "price_pending"
    )
    assert (
        classify_unpriced_card(edhrec_rank=30000, released_at="1995-01-01")
        == "likely_obscure"
    )


def test_format_unpriced_warning_prefix() -> None:
    msg = format_unpriced_warning("Old Card", "likely_obscure")
    assert msg.startswith("Likely obscure:")
    msg2 = format_unpriced_warning("New Card", "price_pending")
    assert msg2.startswith("Price pending:")


def test_normalize_includes_availability_score() -> None:
    raw = {
        "oracle_id": "00000000-0000-0000-0000-000000000099",
        "name": "Scored Card",
        "lang": "en",
        "layout": "normal",
        "type_line": "Creature",
        "legalities": {"commander": "legal"},
        "prices": {"usd": "2.00"},
        "edhrec_rank": 1000,
        "released_at": "2020-01-01",
        "set_type": "commander",
        "reprint": True,
    }
    row = normalize_card(raw)
    assert row is not None
    assert row["availability_score"] is not None
    assert row["availability_score"] >= 70.0


def test_record_availability_percentile() -> None:
    conn = sqlite3.connect(":memory:")
    apply_schema(conn)
    conn.execute(
        """
        INSERT INTO cards (
            oracle_id, name, type_line, mana_cost, cmc, color_identity,
            keywords, commander_legal, commander_eligible, is_basic_land,
            availability_score
        ) VALUES
        ('a', 'A', 'Creature', '', 1, '[]', '[]', 1, 0, 0, 10),
        ('b', 'B', 'Creature', '', 1, '[]', '[]', 1, 0, 0, 30),
        ('c', 'C', 'Creature', '', 1, '[]', '[]', 1, 0, 0, 50),
        ('d', 'D', 'Creature', '', 1, '[]', '[]', 1, 0, 0, 90)
        """
    )
    p25 = record_availability_percentile(conn)
    assert p25 == 30.0
    assert get_availability_p25(conn) == 30.0


def _candidate(*, name: str, score: float | None) -> CardCandidate:
    return CardCandidate(
        oracle_id=name.lower(),
        name=name,
        cmc=2.0,
        type_line="Creature",
        mana_cost="{1}{G}",
        color_identity=["G"],
        price_usd=1.0,
        price_known=True,
        edhrec_rank=1000,
        oracle_text="",
        keywords=[],
        is_basic_land=False,
        produced_mana=[],
        scryfall_uri=None,
        image_uri=None,
        availability_score=score,
    )


def test_filter_prefer_available_excludes_bottom_quartile() -> None:
    conn = sqlite3.connect(":memory:")
    apply_schema(conn)
    conn.execute(
        "INSERT INTO import_metadata (key, value) VALUES ('availability_p25', '40')"
    )
    pool = [
        _candidate(name="Low", score=20.0),
        _candidate(name="High", score=80.0),
    ]
    criteria = DeckCriteria(prefer_available=True)
    filtered = filter_candidates_by_availability(conn, pool, criteria)
    assert [c.name for c in filtered] == ["High"]


def test_filter_prefer_available_noop_when_disabled() -> None:
    conn = sqlite3.connect(":memory:")
    apply_schema(conn)
    pool = [_candidate(name="Low", score=10.0)]
    criteria = DeckCriteria(prefer_available=False)
    assert filter_candidates_by_availability(conn, pool, criteria) == pool
