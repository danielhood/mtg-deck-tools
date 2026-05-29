"""Deck Markdown output formatting tests."""

from __future__ import annotations

from datetime import UTC, datetime

from mtg_deck_tools.builder.deck import DeckBuildResult, DeckCard
from mtg_deck_tools.builder.output import (
    classify_warning,
    format_card_description,
    format_card_mana_cost,
    format_card_price,
    format_generated_timestamp,
    group_warnings,
    write_deck_outputs,
)
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.rules.commander import format_color_identity
from mtg_deck_tools.rules.validate import ValidationIssue, ValidationResult


def test_format_color_identity() -> None:
    assert format_color_identity(["W", "G"]) == "White, Green"
    assert format_color_identity([]) == "Colorless"


def test_format_generated_timestamp() -> None:
    when = datetime(2026, 5, 29, 23, 6, 57, tzinfo=UTC)
    formatted = format_generated_timestamp(when)
    local = when.astimezone()
    assert formatted == local.strftime("%d %B %Y · %H:%M %Z")


def test_classify_warning() -> None:
    assert classify_warning("No USD price for Forest; not counted toward budget.") == "unpriced"
    assert classify_warning("Budget trim: replaced A with B.") == "budget_trim"
    assert classify_warning("Mana base suggested 32 lands based on ramp/curve/colors; using 31.") == (
        "mana_base"
    )
    assert classify_warning("Slot 'ramp': only 2 candidates available (wanted 10).") == "slot"
    assert classify_warning("[budget] 3 card(s) had no USD price.") == "validation"


def test_group_warnings_skips_validation_when_section_exists() -> None:
    warnings = [
        "No USD price for Forest; not counted toward budget.",
        "Budget trim: replaced A with B.",
        "[budget] 3 card(s) had no USD price.",
    ]
    grouped = group_warnings(warnings, include_validation_notes=False)
    assert "unpriced" in grouped
    assert "budget_trim" in grouped
    assert "validation" not in grouped


def test_card_detail_formatters() -> None:
    priced = DeckCard(
        oracle_id="1",
        name="Crop Rotation",
        slot="ramp",
        quantity=1,
        cmc=1.0,
        mana_cost="{G}",
        type_line="Instant",
        price_usd=3.53,
        price_known=True,
        scryfall_uri=None,
        image_uri=None,
        oracle_text="Search your library for a land card,\nreveal it, and put it into your hand.",
    )
    assert format_card_price(priced) == "$3.53"
    assert format_card_mana_cost(priced) == "{G}"
    assert "Search your library" in format_card_description(priced)

    unpriced = DeckCard(
        oracle_id="2",
        name="Forest",
        slot="lands",
        quantity=9,
        cmc=0.0,
        mana_cost="",
        type_line="Basic Land — Forest",
        price_usd=None,
        price_known=False,
        scryfall_uri=None,
        image_uri=None,
    )
    assert format_card_price(unpriced) == "No price"
    assert format_card_mana_cost(unpriced) == "—"


def test_write_deck_outputs_groups_notes_and_card_details(tmp_path) -> None:
    cards = [
        DeckCard(
            oracle_id="c1",
            name="Llanowar Elves",
            slot="ramp",
            quantity=1,
            cmc=1.0,
            mana_cost="{G}",
            type_line="Creature — Elf Druid",
            price_usd=1.25,
            price_known=True,
            scryfall_uri=None,
            image_uri=None,
            oracle_text="{T}: Add {G}.",
        ),
        DeckCard(
            oracle_id="f1",
            name="Forest",
            slot="lands",
            quantity=98,
            cmc=0.0,
            mana_cost="",
            type_line="Basic Land — Forest",
            price_usd=None,
            price_known=False,
            scryfall_uri=None,
            image_uri=None,
        ),
    ]
    validation = ValidationResult(
        passed=True,
        warnings=[ValidationIssue("budget", "1 card(s) had no USD price.")],
    )
    result = DeckBuildResult(
        cards=cards,
        warnings=[
            "No USD price for Forest; not counted toward budget.",
            "Budget trim: replaced Sol Ring ($1.50) with Llanowar Elves ($1.25).",
            "[budget] 1 card(s) had no USD price.",
        ],
        budget_spent=1.25,
        unpriced_names=["Forest"],
        mana_base=None,
        validation=validation,
    )

    criteria = DeckCriteria(
        themes=["tokens"],
        colors=["G"],
        commander_oracle_ids=["cmd"],
        slot_template={"ramp": 1, "lands": 98},
        seed=42,
        budget_usd=150.0,
    )
    _, md_path = write_deck_outputs(
        base_path=tmp_path / "deck",
        criteria=criteria,
        commanders=[{"name": "Test Commander", "oracle_id": "cmd", "color_identity": ["G"]}],
        maindeck=result,
        identity=["G"],
    )

    text = md_path.read_text(encoding="utf-8")
    assert "**Color identity:** Green" in text
    assert " · " in text.split("**Generated:**")[1].splitlines()[0]
    notes_section = text.split("## Notes", 1)[1].split("## Card details", 1)[0]
    assert "### Unpriced cards" in notes_section
    assert "### Budget trims" in notes_section
    assert "[budget]" not in notes_section
    assert "## Card details" in text
    assert "#### Llanowar Elves" in text
    assert "**Price:** $1.25" in text
    assert "**Mana cost:** {G}" in text
    assert "**Description:** {T}: Add {G}." in text
    assert "#### Forest (98×)" in text
