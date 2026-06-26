"""UX10a deck composition metrics."""

from __future__ import annotations

from mtg_deck_tools.builder.deck import DeckBuildResult, DeckCard
from mtg_deck_tools.builder.deck_metrics import (
    compute_deck_metrics,
    cmc_histogram,
    primary_card_type,
    render_deck_metrics_section,
    type_counts,
)
from mtg_deck_tools.builder.mana_base import ManaBasePlan, RampBreakdown
from mtg_deck_tools.builder.output import build_deck_document
from mtg_deck_tools.models.criteria import DeckCriteria


def _card(
    *,
    name: str,
    slot: str,
    cmc: float,
    type_line: str,
    quantity: int = 1,
) -> DeckCard:
    return DeckCard(
        oracle_id=name.lower().replace(" ", "-"),
        name=name,
        slot=slot,
        quantity=quantity,
        cmc=cmc,
        mana_cost="",
        type_line=type_line,
        price_usd=1.0,
        price_known=True,
        scryfall_uri=None,
        image_uri=None,
    )


def test_primary_card_type_legendary_creature() -> None:
    assert primary_card_type("Legendary Creature — Human Wizard") == "Creature"
    assert primary_card_type("Basic Land — Forest") == "Land"
    assert primary_card_type("Artifact Creature — Golem") == "Creature"
    assert primary_card_type("Artifact Creature — Vehicle") == "Vehicle"
    assert primary_card_type("Artifact — Equipment") == "Equipment"


def test_cmc_histogram_quantity_weighted() -> None:
    cards = [
        _card(name="Bolt", slot="removal", cmc=1, type_line="Instant"),
        _card(name="Bear", slot="synergy", cmc=2, type_line="Creature — Bear", quantity=2),
        _card(name="Forest", slot="lands", cmc=0, type_line="Basic Land — Forest", quantity=10),
    ]
    hist = cmc_histogram(cards)
    assert hist["1"] == 1
    assert hist["2"] == 2
    assert sum(hist.values()) == 3
    assert "0" not in hist or hist["0"] == 0


def test_creature_cmc_histogram_excludes_vehicles() -> None:
    cards = [
        _card(name="Bear", slot="synergy", cmc=2, type_line="Creature — Bear"),
        _card(name="Smuggler", slot="synergy", cmc=3, type_line="Artifact — Vehicle"),
    ]
    hist = cmc_histogram(cards, creatures_only=True)
    assert hist["2"] == 1
    assert sum(hist.values()) == 1


def test_type_counts_include_lands() -> None:
    cards = [
        _card(name="Bear", slot="synergy", cmc=2, type_line="Creature — Bear", quantity=3),
        _card(name="Forest", slot="lands", cmc=0, type_line="Basic Land — Forest", quantity=12),
    ]
    counts = type_counts(cards)
    assert counts["Creature"] == 3
    assert counts["Land"] == 12


def test_compute_deck_metrics_uses_mana_base_ramp() -> None:
    cards = [
        _card(name="Sol Ring", slot="ramp", cmc=1, type_line="Artifact"),
        _card(name="Forest", slot="lands", cmc=0, type_line="Basic Land — Forest", quantity=36),
    ]
    mana_base = ManaBasePlan(
        template_lands=36,
        suggested_lands=36,
        actual_lands=36,
        nonland_count=63,
        ramp=RampBreakdown(total=11, mana_rocks=8, land_ramp=2, other=1, effective_reduction=2.0),
        avg_cmc_nonland=2.5,
        num_colors=1,
        pip_weights={"G": 1},
        nonbasic_target=12,
        basic_target=24,
    )
    metrics = compute_deck_metrics(cards, mana_base=mana_base)
    assert metrics["land_count"] == 36
    assert metrics["ramp_count"] == 11
    assert metrics["avg_cmc_nonland"] == 1.0
    assert metrics["avg_creature_cmc"] is None


def test_render_deck_metrics_section_includes_curve() -> None:
    metrics = compute_deck_metrics(
        [
            _card(name="Bolt", slot="removal", cmc=1, type_line="Instant"),
            _card(name="Bear", slot="synergy", cmc=2, type_line="Creature — Bear"),
            _card(name="Forest", slot="lands", cmc=0, type_line="Basic Land — Forest", quantity=2),
        ]
    )
    lines = render_deck_metrics_section(metrics)
    text = "\n".join(lines)
    assert "## Deck metrics" in text
    assert "### Mana curve (nonlands)" in text
    assert "| 1 | 1 |" in text
    assert "### Creature curve" in text


def test_build_deck_document_includes_deck_metrics_in_stats() -> None:
    cards = [
        _card(name="Bear", slot="synergy", cmc=2, type_line="Creature — Bear"),
        _card(name="Forest", slot="lands", cmc=0, type_line="Basic Land — Forest", quantity=98),
    ]
    doc = build_deck_document(
        criteria=DeckCriteria(colors=["G"], commander_oracle_ids=["cmd"]),
        commanders=[{"name": "Commander", "oracle_id": "cmd"}],
        maindeck=DeckBuildResult(cards=cards, warnings=[], budget_spent=1.0, unpriced_names=[]),
        identity=["G"],
    )
    stats = doc["stats"]
    assert "cmc_histogram" in stats
    assert "creature_cmc_histogram" in stats
    assert "type_counts" in stats
    assert stats["land_count"] == 98
    assert stats["avg_cmc_nonland"] == 2.0
