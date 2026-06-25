"""Commander deck validation tests."""

from __future__ import annotations

import json
import sqlite3

import pytest

from mtg_deck_tools.builder.filler import DeckCard
from mtg_deck_tools.db.schema import apply_schema
from mtg_deck_tools.rules.validate import (
    adjust_slot_template_for_commanders,
    is_valid_partner_pair,
    mainboard_size_for_commanders,
    validate_commander_deck,
    validation_messages,
)
from mtg_deck_tools.rules.validate import _CommanderRules


def _insert(
    conn: sqlite3.Connection,
    *,
    oracle_id: str,
    name: str,
    color_identity: list[str],
    type_line: str,
    commander_eligible: int = 0,
    commander_legal: int = 1,
    is_basic_land: int = 0,
    produced_mana: list[str] | None = None,
    oracle_text: str = "",
    partner_kind: str | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO cards (
            oracle_id, name, type_line, color_identity, commander_legal,
            commander_eligible, is_basic_land, produced_mana, oracle_text,
            partner_kind, keywords, mana_cost, cmc
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '[]', '', 0)
        """,
        (
            oracle_id,
            name,
            type_line,
            json.dumps(color_identity),
            commander_legal,
            commander_eligible,
            is_basic_land,
            json.dumps(produced_mana or []),
            oracle_text,
            partner_kind,
        ),
    )


@pytest.fixture
def rules_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    apply_schema(conn)
    _insert(
        conn,
        oracle_id="cmd",
        name="Selvala",
        color_identity=["G", "W"],
        type_line="Legendary Creature — Elf Scout",
        commander_eligible=1,
    )
    _insert(
        conn,
        oracle_id="c1",
        name="Llanowar Elves",
        color_identity=["G"],
        type_line="Creature — Elf Druid",
    )
    _insert(
        conn,
        oracle_id="bad",
        name="Lightning Bolt",
        color_identity=["R"],
        type_line="Instant",
    )
    _insert(
        conn,
        oracle_id="forest",
        name="Forest",
        color_identity=[],
        type_line="Basic Land — Forest",
        is_basic_land=1,
    )
    _insert(
        conn,
        oracle_id="tomb",
        name="Overgrown Tomb",
        color_identity=["B", "G"],
        type_line="Land — Swamp Forest",
        produced_mana=["B", "G"],
    )
    conn.commit()
    return conn


def _deck_card(oracle_id: str, name: str, **kwargs) -> DeckCard:
    return DeckCard(
        oracle_id=oracle_id,
        name=name,
        slot="synergy",
        quantity=1,
        cmc=1.0,
        mana_cost="{G}",
        type_line=kwargs.get("type_line", "Creature"),
        price_usd=1.0,
        price_known=True,
        scryfall_uri=None,
        image_uri=None,
        produced_mana=kwargs.get("produced_mana", []),
    )


def test_mainboard_size_for_partners():
    assert mainboard_size_for_commanders(1) == 99
    assert mainboard_size_for_commanders(2) == 98


def test_adjust_slot_template_trims_flex():
    slots = {
        "ramp": 10,
        "draw": 8,
        "removal": 8,
        "board_wipe": 2,
        "synergy": 30,
        "wincon": 4,
        "flex": 6,
        "lands": 31,
    }
    adjusted = adjust_slot_template_for_commanders(slots, 2)
    assert sum(adjusted.values()) == 98
    assert adjusted["flex"] == 5


def test_validate_legal_deck_passes(rules_db: sqlite3.Connection) -> None:
    maindeck = [_deck_card("c1", "Llanowar Elves")]
    maindeck += [
        _deck_card("forest", "Forest", type_line="Basic Land — Forest") for _ in range(98)
    ]
    result = validate_commander_deck(
        rules_db,
        commanders=[{"oracle_id": "cmd", "name": "Selvala", "color_identity": ["G", "W"]}],
        maindeck=maindeck,
        identity=["G", "W"],
    )
    assert result.passed
    assert not result.errors


def test_validate_singleton_violation(rules_db: sqlite3.Connection) -> None:
    maindeck = [_deck_card("c1", "Llanowar Elves"), _deck_card("c1", "Llanowar Elves")]
    maindeck += [_deck_card("forest", "Forest", type_line="Basic Land — Forest")] * 97
    result = validate_commander_deck(
        rules_db,
        commanders=[{"oracle_id": "cmd", "name": "Selvala", "color_identity": ["G", "W"]}],
        maindeck=maindeck,
        identity=["G", "W"],
    )
    assert not result.passed
    assert any(i.rule == "903.5b" for i in result.errors)


def test_validate_color_identity(rules_db: sqlite3.Connection) -> None:
    maindeck = [_deck_card("bad", "Lightning Bolt")] + [
        _deck_card("c1", "Llanowar Elves")
    ] * 98
    result = validate_commander_deck(
        rules_db,
        commanders=[{"oracle_id": "cmd", "name": "Selvala", "color_identity": ["G", "W"]}],
        maindeck=maindeck,
        identity=["G", "W"],
    )
    assert not result.passed
    assert any(i.rule == "903.5c" and i.card_name == "Lightning Bolt" for i in result.errors)


def test_validate_land_mana_production(rules_db: sqlite3.Connection) -> None:
    maindeck = [
        _deck_card(
            "tomb",
            "Overgrown Tomb",
            type_line="Land — Swamp Forest",
            produced_mana=["B", "G"],
        )
    ] + [_deck_card("c1", "Llanowar Elves")] * 98
    result = validate_commander_deck(
        rules_db,
        commanders=[{"oracle_id": "cmd", "name": "Selvala", "color_identity": ["G", "W"]}],
        maindeck=maindeck,
        identity=["G", "W"],
    )
    assert not result.passed
    assert any(i.rule == "903.5d" for i in result.errors)


def test_partner_with_name_match():
    a = _CommanderRules(
        oracle_id="a",
        name="Lathril, Blade of the Elves",
        type_line="Legendary Creature",
        color_identity=frozenset({"B", "G"}),
        commander_eligible=True,
        oracle_text="Partner with Jorael, Moodkeeper",
        partner_kind="partner_with",
    )
    b = _CommanderRules(
        oracle_id="b",
        name="Jorael, Moodkeeper",
        type_line="Legendary Creature",
        color_identity=frozenset({"G", "U"}),
        commander_eligible=True,
        oracle_text="Partner with Lathril, Blade of the Elves",
        partner_kind="partner_with",
    )
    assert is_valid_partner_pair(a, b) is None


def test_validation_messages_format():
    from mtg_deck_tools.rules.validate import ValidationIssue, ValidationResult

    result = ValidationResult(
        passed=False,
        errors=[ValidationIssue("903.5b", "Duplicate", card_name="Foo")],
        warnings=[ValidationIssue("budget", "Over budget")],
    )
    lines = validation_messages(result)
    assert any("[903.5b]" in line for line in lines)
    assert any("[budget]" in line for line in lines)


def test_format_validation_failure_includes_errors():
    from mtg_deck_tools.rules.validate import (
        ValidationIssue,
        ValidationResult,
        format_validation_failure,
        require_valid_deck,
    )

    result = ValidationResult(
        passed=False,
        errors=[
            ValidationIssue(
                "903.5a",
                "Deck has 45 cards (44 maindeck + 1 commander(s)); must be 100.",
            )
        ],
    )
    message = format_validation_failure(result)
    assert "valid deck" in message
    assert "45 cards" in message

    with pytest.raises(RuntimeError, match="valid deck"):
        require_valid_deck(result)
