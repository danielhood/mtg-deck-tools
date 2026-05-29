"""Dynamic mana base calculation tests."""

from __future__ import annotations

from mtg_deck_tools.builder.filler import DeckCard
from mtg_deck_tools.builder.mana_base import (
    analyze_ramp_cards,
    allocate_basics,
    compute_pip_weights,
    compute_suggested_land_count,
    plan_mana_base,
    score_land_candidate,
    split_land_mix,
)
from mtg_deck_tools.builder.pool import CardCandidate


def _card(
    *,
    slot: str = "synergy",
    mana_cost: str = "{1}{G}{G}",
    type_line: str = "Creature",
    quantity: int = 1,
    mechanic_tags: list[str] | None = None,
    oracle_text: str = "",
) -> DeckCard:
    return DeckCard(
        oracle_id="x",
        name="Test",
        slot=slot,
        quantity=quantity,
        cmc=3.0,
        mana_cost=mana_cost,
        type_line=type_line,
        price_usd=1.0,
        price_known=True,
        scryfall_uri=None,
        image_uri=None,
        mechanic_tags=mechanic_tags or [],
        oracle_text=oracle_text,
    )


def test_compute_pip_weights():
    cards = [
        _card(mana_cost="{G}", quantity=2),
        _card(mana_cost="{W}{G}", quantity=1),
    ]
    weights = compute_pip_weights(cards, ["W", "G"])
    assert weights["G"] >= 3
    assert weights["W"] >= 2


def test_suggested_land_count_decreases_with_ramp():
    ramp = analyze_ramp_cards(
        [
            _card(slot="ramp", type_line="Artifact", mechanic_tags=["ramp"]),
            _card(slot="ramp", type_line="Sorcery", mechanic_tags=["ramp"], oracle_text="search your library for a land card"),
        ]
    )
    high = compute_suggested_land_count(
        nonland_count=68,
        ramp=ramp,
        avg_cmc_nonland=3.0,
        num_colors=2,
    )
    low_ramp = analyze_ramp_cards([])
    low = compute_suggested_land_count(
        nonland_count=68,
        ramp=low_ramp,
        avg_cmc_nonland=3.0,
        num_colors=2,
    )
    assert high < low


def test_split_land_mix_more_nonbasics_for_three_colors():
    nb2, _ = split_land_mix(36, num_colors=2, pip_weights={"W": 5, "G": 5})
    nb3, _ = split_land_mix(36, num_colors=3, pip_weights={"W": 4, "U": 4, "G": 4})
    assert nb3 > nb2


def test_allocate_basics_respects_pips():
    names = allocate_basics(10, {"W": 8, "G": 2}, ["W", "G"])
    assert names.count("Plains") > names.count("Forest")


def test_score_land_prefers_produced_colors():
    land = CardCandidate(
        oracle_id="l1",
        name="Overgrown Tomb",
        cmc=0.0,
        type_line="Land",
        mana_cost="",
        color_identity=["B", "G"],
        price_usd=10.0,
        price_known=True,
        edhrec_rank=100,
        oracle_text="",
        keywords=[],
        is_basic_land=False,
        produced_mana=["B", "G"],
        scryfall_uri=None,
        image_uri=None,
    )
    score = score_land_candidate(land, pip_weights={"B": 10, "G": 2}, identity=["B", "G"])
    mono = CardCandidate(
        oracle_id="l2",
        name="Forest",
        cmc=0.0,
        type_line="Basic Land",
        mana_cost="",
        color_identity=[],
        price_usd=0.1,
        price_known=True,
        edhrec_rank=None,
        oracle_text="",
        keywords=[],
        is_basic_land=True,
        produced_mana=[],
        scryfall_uri=None,
        image_uri=None,
    )
    mono_score = score_land_candidate(mono, pip_weights={"B": 10, "G": 2}, identity=["B", "G"])
    assert score > mono_score


def test_plan_mana_base_full_deck_uses_ninety_nine_minus_nonlands():
    cards = [_card(slot="ramp", type_line="Artifact", mechanic_tags=["ramp"])] * 10
    cards += [_card(slot="synergy")] * 58
    plan = plan_mana_base(cards, identity=["G"], template_lands=31)
    assert plan.nonland_count == 68
    assert plan.actual_lands == 31
    assert plan.suggested_lands >= 30
