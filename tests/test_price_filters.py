"""Per-card price range filter tests."""

from __future__ import annotations

from mtg_deck_tools.builder.pool import CardCandidate
from mtg_deck_tools.builder.price_filters import (
    filter_card_price_range,
    filter_candidates_by_price,
)
from mtg_deck_tools.formatting import format_card_price_range_display
from mtg_deck_tools.models.criteria import DeckCriteria


def _candidate(*, price_usd: float | None, price_known: bool = True) -> CardCandidate:
    return CardCandidate(
        oracle_id="x",
        name="Test",
        cmc=1.0,
        type_line="Creature",
        mana_cost="{1}",
        color_identity=["G"],
        price_usd=price_usd,
        price_known=price_known,
        edhrec_rank=1000,
        oracle_text="",
        keywords=[],
        is_basic_land=False,
        produced_mana=[],
        scryfall_uri=None,
        image_uri=None,
    )


def test_filter_card_price_range_min_max() -> None:
    pool = [
        _candidate(price_usd=0.25),
        _candidate(price_usd=5.0),
        _candidate(price_usd=50.0),
    ]
    criteria = DeckCriteria(card_price_min_usd=1.0, card_price_max_usd=10.0)
    filtered = filter_card_price_range(pool, criteria)
    assert len(filtered) == 1
    assert filtered[0].price_usd == 5.0


def test_filter_card_price_range_min_excludes_unpriced() -> None:
    pool = [_candidate(price_usd=5.0), _candidate(price_usd=None, price_known=False)]
    criteria = DeckCriteria(card_price_min_usd=1.0)
    filtered = filter_card_price_range(pool, criteria)
    assert len(filtered) == 1


def test_filter_candidates_by_price_then_budget() -> None:
    pool = [
        _candidate(price_usd=2.0),
        _candidate(price_usd=8.0),
        _candidate(price_usd=20.0),
    ]
    criteria = DeckCriteria(card_price_max_usd=15.0, budget_usd=100.0)
    filtered = filter_candidates_by_price(pool, criteria, budget_remaining=10.0)
    assert [c.price_usd for c in filtered] == [2.0, 8.0]


def test_format_card_price_range_display() -> None:
    assert format_card_price_range_display(min_usd=1.0, max_usd=25.0) == (
        "$1.00 – $25.00 per card"
    )
    assert format_card_price_range_display(min_usd=2.0, max_usd=None) == (
        "$2.00 minimum per card"
    )


def test_criteria_rejects_invalid_range() -> None:
    try:
        DeckCriteria(card_price_min_usd=10.0, card_price_max_usd=5.0)
        assert False, "expected validation error"
    except ValueError:
        pass
