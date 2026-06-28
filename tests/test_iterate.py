"""UX11 deck iterate engine tests."""

from __future__ import annotations

import json
import sqlite3

import pytest

from mtg_deck_tools.builder.deck import DeckCard, DeckBuildResult
from mtg_deck_tools.builder.filler import refill_deck_slot
from mtg_deck_tools.builder.iterate import preview_swap_deck_cards, swap_deck_cards
from mtg_deck_tools.builder.output import build_deck_document
from mtg_deck_tools.builder.swap_constraints import filter_candidates_by_swap_constraints
from mtg_deck_tools.builder.swap_playbooks import (
    constraints_for_strategy,
    strategies_for_rule,
)
from mtg_deck_tools.db.schema import apply_schema
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.models.swap_constraints import EffectRoleConstraint, SwapConstraints
from mtg_deck_tools.wizard.slots import load_slot_template_config


def _deck_card(**kwargs) -> DeckCard:
    defaults = dict(
        oracle_id="x",
        name="Card",
        slot="synergy",
        quantity=1,
        cmc=2.0,
        mana_cost="{2}",
        type_line="Creature",
        price_usd=1.0,
        price_known=True,
        scryfall_uri=None,
        image_uri=None,
    )
    defaults.update(kwargs)
    return DeckCard(**defaults)


@pytest.fixture
def iterate_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    apply_schema(conn)
    conn.execute(
        """
        INSERT INTO cards (
            oracle_id, name, type_line, mana_cost, cmc, color_identity,
            keywords, commander_legal, commander_eligible, is_basic_land,
            edhrec_rank, price_usd, price_known, oracle_text
        ) VALUES (?, ?, ?, '', 3.0, ?, '[]', 1, 1, 0, 100, 2.0, 1, '')
        """,
        ("cmd", "Commander", "Legendary Creature — Human", json.dumps(["G"])),
    )
    conn.execute(
        """
        INSERT INTO cards (
            oracle_id, name, type_line, mana_cost, cmc, color_identity,
            keywords, commander_legal, commander_eligible, is_basic_land,
            edhrec_rank, price_usd, price_known, oracle_text
        ) VALUES (?, ?, ?, '{1}{G}', 2.0, ?, '[]', 1, 0, 0, 600, 1.0, 1, '')
        """,
        ("syn-a", "Token Maker", "Creature — Elf", json.dumps(["G"])),
    )
    conn.execute(
        """
        INSERT INTO card_mechanic_tags (oracle_id, tag, layer, source)
        VALUES ('syn-a', 'tokens', 'theme', 'test')
        """
    )
    conn.execute(
        """
        INSERT INTO cards (
            oracle_id, name, type_line, mana_cost, cmc, color_identity,
            keywords, commander_legal, commander_eligible, is_basic_land,
            edhrec_rank, price_usd, price_known, oracle_text
        ) VALUES (?, ?, ?, '{1}{G}', 2.0, ?, '[]', 1, 0, 0, 700, 1.2, 1, '')
        """,
        ("syn-b", "Other Maker", "Creature — Human", json.dumps(["G"])),
    )
    conn.execute(
        """
        INSERT INTO card_mechanic_tags (oracle_id, tag, layer, source)
        VALUES ('syn-b', 'tokens', 'theme', 'test')
        """
    )
    conn.execute(
        """
        INSERT INTO cards (
            oracle_id, name, type_line, mana_cost, cmc, color_identity,
            keywords, commander_legal, commander_eligible, is_basic_land,
            edhrec_rank, price_usd, price_known, oracle_text, rarity
        ) VALUES (?, ?, ?, '{1}', 1.0, ?, '[]', 1, 0, 0, 500, 3.0, 1, '', 'uncommon')
        """,
        ("equip-a", "Test Sword", "Artifact — Equipment", json.dumps(["G"])),
    )
    conn.execute(
        """
        INSERT INTO card_mechanic_tags (oracle_id, tag, layer, source)
        VALUES ('equip-a', 'tokens', 'theme', 'test')
        """
    )
    conn.execute(
        """
        INSERT INTO cards (
            oracle_id, name, type_line, mana_cost, cmc, color_identity,
            keywords, commander_legal, commander_eligible, is_basic_land,
            edhrec_rank, price_usd, price_known, oracle_text, rarity
        ) VALUES (?, ?, ?, '{2}', 2.0, ?, '[]', 1, 0, 0, 800, 1.5, 1, '', 'common')
        """,
        ("creature-a", "Carrier Elf", "Creature — Elf", json.dumps(["G"])),
    )
    conn.commit()
    return conn


def test_refill_deck_slot_keeps_locked_cards(iterate_db: sqlite3.Connection) -> None:
    slots = dict(load_slot_template_config().default)
    criteria = DeckCriteria(
        themes=["tokens"],
        colors=["G"],
        commander_oracle_ids=["cmd"],
        slot_template=slots,
        seed=1,
    )
    fixed = [
        _deck_card(oracle_id="syn-locked", name="Pinned", slot="synergy", locked=True),
        _deck_card(oracle_id="syn-old", name="Replace Me", slot="synergy"),
    ]
    result = refill_deck_slot(
        iterate_db,
        criteria,
        identity=["G"],
        commander_oracle_ids=["cmd"],
        fixed_cards=fixed,
        refill_slot="synergy",
        seed=1,
    )
    synergy = [c for c in result.cards if c.slot == "synergy"]
    assert any(c.name == "Pinned" and c.locked for c in synergy)
    assert all(c.name != "Replace Me" for c in synergy)


def test_refill_deck_slot_rejects_all_locked(iterate_db: sqlite3.Connection) -> None:
    slots = dict(load_slot_template_config().default)
    slots["synergy"] = 1
    criteria = DeckCriteria(
        themes=["tokens"],
        colors=["G"],
        commander_oracle_ids=["cmd"],
        slot_template=slots,
        seed=1,
    )
    fixed = [
        _deck_card(oracle_id="syn-locked", name="Pinned", slot="synergy", locked=True),
    ]
    with pytest.raises(ValueError, match="All cards in slot 'synergy' are locked"):
        refill_deck_slot(
            iterate_db,
            criteria,
            identity=["G"],
            commander_oracle_ids=["cmd"],
            fixed_cards=fixed,
            refill_slot="synergy",
            seed=1,
        )


def test_swap_deck_cards_replaces_selection(iterate_db: sqlite3.Connection) -> None:
    slots = dict(load_slot_template_config().default)
    criteria = DeckCriteria(
        themes=["tokens"],
        colors=["G"],
        commander_oracle_ids=["cmd"],
        slot_template=slots,
        seed=3,
    )
    fixed = [
        _deck_card(oracle_id="syn-old", name="Old Card", slot="synergy"),
        _deck_card(oracle_id="ramp-1", name="Ramp", slot="ramp"),
    ]
    result, swaps = swap_deck_cards(
        iterate_db,
        criteria,
        identity=["G"],
        commander_oracle_ids=["cmd"],
        fixed_cards=fixed,
        oracle_ids=["syn-old"],
        seed=3,
    )
    assert len(swaps) == 1
    assert swaps[0].from_name == "Old Card"
    assert swaps[0].to_name
    assert all(c.name != "Old Card" for c in result.cards if c.slot == "synergy")
    assert any(c.name == "Ramp" for c in result.cards)


def test_build_deck_document_includes_locked_flag() -> None:
    card = _deck_card(locked=True)
    doc = build_deck_document(
        criteria=DeckCriteria(themes=[], colors=["G"], commander_oracle_ids=["cmd"]),
        commanders=[{"oracle_id": "cmd", "name": "Commander", "type_line": "Legendary Creature"}],
        maindeck=DeckBuildResult(cards=[card], warnings=[], budget_spent=1.0, unpriced_names=[]),
        identity=["G"],
    )
    assert doc["cards"][0]["locked"] is True


def test_swap_rejects_commander_oracle_id(iterate_db: sqlite3.Connection) -> None:
    criteria = DeckCriteria(
        themes=["tokens"],
        colors=["G"],
        commander_oracle_ids=["cmd"],
        seed=1,
    )
    with pytest.raises(ValueError, match="Cannot swap commander"):
        swap_deck_cards(
            iterate_db,
            criteria,
            identity=["G"],
            commander_oracle_ids=["cmd"],
            fixed_cards=[_deck_card()],
            oracle_ids=["cmd"],
            seed=1,
        )


def test_swap_with_equipment_constraint(iterate_db: sqlite3.Connection) -> None:
    slots = dict(load_slot_template_config().default)
    criteria = DeckCriteria(
        themes=["tokens"],
        colors=["G"],
        commander_oracle_ids=["cmd"],
        slot_template=slots,
        seed=5,
    )
    fixed = [_deck_card(oracle_id="syn-old", name="Old Card", slot="synergy")]
    constraints = SwapConstraints(type_lines_any=["Equipment"])
    _result, swaps = swap_deck_cards(
        iterate_db,
        criteria,
        identity=["G"],
        commander_oracle_ids=["cmd"],
        fixed_cards=fixed,
        oracle_ids=["syn-old"],
        seed=5,
        constraints=constraints,
    )
    assert len(swaps) == 1
    assert swaps[0].to_name == "Test Sword"


def test_preview_swap_returns_candidates(iterate_db: sqlite3.Connection) -> None:
    slots = dict(load_slot_template_config().default)
    criteria = DeckCriteria(
        themes=["tokens"],
        colors=["G"],
        commander_oracle_ids=["cmd"],
        slot_template=slots,
        seed=2,
    )
    fixed = [_deck_card(oracle_id="syn-old", name="Old Card", slot="synergy")]
    positions = preview_swap_deck_cards(
        iterate_db,
        criteria,
        identity=["G"],
        commander_oracle_ids=["cmd"],
        fixed_cards=fixed,
        oracle_ids=["syn-old"],
        constraints=SwapConstraints(type_lines_any=["Equipment"]),
        preview_limit=3,
        seed=2,
    )
    assert len(positions) == 1
    assert positions[0].from_name == "Old Card"
    assert positions[0].candidates
    assert positions[0].candidates[0].name == "Test Sword"


def test_swap_playbooks_load_equipment_strategies() -> None:
    strategies = strategies_for_rule("EQUIPMENT_BALANCE", deficit="equipment")
    ids = {row["id"] for row in strategies}
    assert "add_equipment" in ids
    constraints = constraints_for_strategy("add_equipment", rule_id="EQUIPMENT_BALANCE")
    assert constraints is not None
    assert "Equipment" in constraints.type_lines_any



def test_effect_role_token_payoff_filter(iterate_db: sqlite3.Connection) -> None:
    iterate_db.execute(
        """
        INSERT INTO cards (
            oracle_id, name, type_line, mana_cost, cmc, color_identity,
            keywords, commander_legal, commander_eligible, is_basic_land,
            edhrec_rank, price_usd, price_known, oracle_text
        ) VALUES (?, ?, ?, '{2}{G}', 3.0, ?, '[]', 1, 0, 0, 550, 2.0, 1, 'Whenever you create a token, draw a card.')
        """,
        ("payoff-a", "Token Payoff", "Enchantment", json.dumps(["G"])),
    )
    iterate_db.execute(
        """
        INSERT INTO card_mechanic_tags (oracle_id, tag, layer, source)
        VALUES ('payoff-a', 'tokens', 'theme', 'test')
        """
    )
    iterate_db.execute(
        """
        INSERT INTO card_effects (
            oracle_id, face_index, effect_kind, payload, confidence, source
        ) VALUES ('payoff-a', 0, 'token_payoff', '{}', 1.0, 'test')
        """
    )
    iterate_db.commit()

    row = iterate_db.execute(
        "SELECT * FROM cards WHERE oracle_id = 'payoff-a'"
    ).fetchone()
    from mtg_deck_tools.builder.pool import _row_to_candidate

    candidate = _row_to_candidate(row)
    constraints = SwapConstraints(
        effect_role=EffectRoleConstraint(profile_id="tokens", role="consumer"),
    )
    filtered = filter_candidates_by_swap_constraints(
        iterate_db,
        [candidate, _row_to_candidate(iterate_db.execute("SELECT * FROM cards WHERE oracle_id = 'syn-a'").fetchone())],
        constraints,
    )
    assert [c.oracle_id for c in filtered] == ["payoff-a"]


def test_named_card_swap(iterate_db: sqlite3.Connection) -> None:
    slots = dict(load_slot_template_config().default)
    criteria = DeckCriteria(
        themes=["tokens"],
        colors=["G"],
        commander_oracle_ids=["cmd"],
        slot_template=slots,
        seed=7,
    )
    fixed = [_deck_card(oracle_id="syn-old", name="Old Card", slot="synergy")]
    constraints = SwapConstraints(replacement_oracle_id="equip-a")
    _result, swaps = swap_deck_cards(
        iterate_db,
        criteria,
        identity=["G"],
        commander_oracle_ids=["cmd"],
        fixed_cards=fixed,
        oracle_ids=["syn-old"],
        seed=7,
        constraints=constraints,
    )
    assert swaps[0].to_oracle_id == "equip-a"
    assert swaps[0].to_name == "Test Sword"
