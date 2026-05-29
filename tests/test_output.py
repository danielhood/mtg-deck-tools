"""Deck Markdown output formatting tests."""

from __future__ import annotations

from datetime import UTC, date, datetime

from mtg_deck_tools.builder.deck import DeckBuildResult, DeckCard
from mtg_deck_tools.formatting import format_display_date
from mtg_deck_tools.builder.output import (
    classify_warning,
    format_card_description,
    format_commander_list_item,
    format_card_detail_title,
    format_card_mana_cost,
    format_card_power_toughness,
    format_card_price,
    format_card_released_at,
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


def test_format_display_date() -> None:
    assert format_display_date(date(2026, 5, 29)) == "May 29, 2026"
    assert format_display_date(date(1993, 10, 4)) == "October 4, 1993"


def test_format_generated_timestamp() -> None:
    when = datetime(2026, 5, 29, 23, 6, 57, tzinfo=UTC)
    formatted = format_generated_timestamp(when)
    local = when.astimezone()
    assert formatted == f"May 29, 2026 · {local.strftime('%H:%M %Z')}"


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
    assert format_card_mana_cost(priced) == "(G)"
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


def test_format_commander_list_item() -> None:
    item = format_commander_list_item(
        {
            "name": "Yawgmoth, Thran Physician",
            "scryfall_uri": "https://scryfall.com/card/mh1/116/yawgmoth-thran-physician",
            "price_usd": 12.34,
            "price_known": True,
            "released_at": "2019-06-14",
        }
    )
    assert "[Yawgmoth, Thran Physician]" in item
    assert "**Price:** $12.34" in item
    assert "**Released:** June 14, 2019" in item


def test_format_card_detail_title_links_scryfall() -> None:
    linked = DeckCard(
        oracle_id="1",
        name="Sol Ring",
        slot="ramp",
        quantity=1,
        cmc=1.0,
        mana_cost="{1}",
        type_line="Artifact",
        price_usd=1.0,
        price_known=True,
        scryfall_uri="https://scryfall.com/card/a25/232/sol-ring",
        image_uri=None,
    )
    assert format_card_detail_title(linked) == (
        "[Sol Ring](https://scryfall.com/card/a25/232/sol-ring)"
    )
    assert format_card_detail_title(
        DeckCard(
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
    ) == "Forest (9×)"


def test_format_card_power_toughness() -> None:
    creature = DeckCard(
        oracle_id="1",
        name="Bear",
        slot="synergy",
        quantity=1,
        cmc=2.0,
        mana_cost="{1}{G}",
        type_line="Creature — Bear",
        price_usd=0.5,
        price_known=True,
        scryfall_uri=None,
        image_uri=None,
        power="2",
        toughness="2",
    )
    assert format_card_power_toughness(creature) == "2/2"
    assert format_card_power_toughness(
        DeckCard(
            oracle_id="2",
            name="Sol Ring",
            slot="ramp",
            quantity=1,
            cmc=1.0,
            mana_cost="{1}",
            type_line="Artifact",
            price_usd=1.0,
            price_known=True,
            scryfall_uri=None,
            image_uri=None,
        )
    ) == "—"


def test_format_card_released_at() -> None:
    card = DeckCard(
        oracle_id="1",
        name="Test",
        slot="ramp",
        quantity=1,
        cmc=1.0,
        mana_cost="{G}",
        type_line="Creature",
        price_usd=1.0,
        price_known=True,
        scryfall_uri=None,
        image_uri=None,
        released_at="2015-03-27",
    )
    assert format_card_released_at(card) == "March 27, 2015"
    assert format_card_released_at(
        DeckCard(
            oracle_id="2",
            name="Unknown",
            slot="flex",
            quantity=1,
            cmc=0.0,
            mana_cost="",
            type_line="Creature",
            price_usd=None,
            price_known=False,
            scryfall_uri=None,
            image_uri=None,
        )
    ) == "—"


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
        scryfall_uri="https://scryfall.com/card/lea/258/llanowar-elves",
        image_uri=None,
        oracle_text="{T}: Add {G}.",
            released_at="1993-10-04",
            power="1",
            toughness="1",
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
        themes=["tokens", "voltron"],
        colors=["G"],
        include_mechanics=["flying"],
        avoid_mechanics=["reach"],
        commander_oracle_ids=["cmd"],
        slot_template={"ramp": 1, "lands": 98},
        seed=42,
        budget_usd=150.0,
    )
    _, md_path = write_deck_outputs(
        base_path=tmp_path / "deck",
        criteria=criteria,
        commanders=[
            {
                "name": "Test Commander",
                "oracle_id": "cmd",
                "color_identity": ["G"],
                "scryfall_uri": "https://scryfall.com/card/test/commander",
                "price_usd": 5.0,
                "price_known": True,
                "released_at": "2020-01-15",
            }
        ],
        maindeck=result,
        identity=["G"],
    )

    text = md_path.read_text(encoding="utf-8")
    assert "**Color identity:** Green" in text
    assert "**Themes:** Token creation, Equipment and aura support" in text
    assert "**Include mechanics:** Flying" in text
    assert "**Avoid mechanics:** Reach" in text
    assert "## Criteria" not in text
    assert " · " in text.split("**Generated:**")[1].splitlines()[0]
    notes_section = text.split("## Notes", 1)[1].split("## Card details", 1)[0]
    assert "### Unpriced cards" in notes_section
    assert "### Budget trims" in notes_section
    assert "[budget]" not in notes_section
    assert "**Price:** $5.00" in text.split("## Commander")[1].split("## Validation")[0]
    assert "**Released:** January 15, 2020" in text
    assert "## Card details" in text
    assert "#### [Llanowar Elves](https://scryfall.com/card/lea/258/llanowar-elves)" in text
    assert "**Price:** $1.25" in text
    assert "**Released:** October 4, 1993" in text
    assert "**Power/Toughness:** 1/1" in text
    assert "**Mana cost:** (G)" in text
    assert "**Description:** **Tap**: Add (G)." in text
    assert "#### Forest (98×)" in text
