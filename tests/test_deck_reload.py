"""Deck .deck.json reload and slot refill tests."""

from __future__ import annotations

import json
import sqlite3

import pytest

from mtg_deck_tools.builder.deck_load import load_deck_json
from mtg_deck_tools.builder.filler import refill_deck_slot
from mtg_deck_tools.builder.reload import run_generate_from_deck
from mtg_deck_tools.db.schema import apply_schema
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.wizard.slots import load_slot_template_config


def _minimal_deck_json(*, budget_usd: float | None = 150.0) -> dict:
    slots = dict(load_slot_template_config().default)
    return {
        "schema_version": "1.0",
        "generated_at": "2026-05-30T00:00:00Z",
        "generator": {"name": "mtg-deck-tools", "version": "0.1.0"},
        "criteria": {
            "themes": ["voltron"],
            "colors": ["G"],
            "include_mechanics": [],
            "avoid_mechanics": [],
            "commander_oracle_ids": ["cmd"],
            "budget_usd": budget_usd,
            "slot_template": slots,
            "seed": 99,
        },
        "commanders": [
            {
                "oracle_id": "cmd",
                "name": "Commander",
                "type_line": "Legendary Creature — Human",
                "scryfall_uri": "https://example.com/cmd",
            }
        ],
        "cards": [
            {
                "oracle_id": "ramp-1",
                "name": "Ramp Rock",
                "slot": "ramp",
                "quantity": 1,
                "cmc": 2.0,
                "mana_cost": "{2}",
                "type_line": "Artifact",
                "price_usd": 1.0,
                "price_known": True,
            },
            {
                "oracle_id": "syn-1",
                "name": "Synergy Piece",
                "slot": "synergy",
                "quantity": 1,
                "cmc": 3.0,
                "mana_cost": "{2}{G}",
                "type_line": "Enchantment",
                "price_usd": 2.0,
                "price_known": True,
            },
            {
                "oracle_id": "forest",
                "name": "Forest",
                "slot": "lands",
                "quantity": 1,
                "cmc": 0.0,
                "mana_cost": "",
                "type_line": "Basic Land — Forest",
                "price_usd": 0.1,
                "price_known": True,
            },
        ],
    }


@pytest.fixture
def reload_db() -> sqlite3.Connection:
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
        ) VALUES (?, ?, ?, '{1}{G}', 1.0, ?, '[]', 1, 0, 0, 500, 0.5, 1, '{T}: Add {G}.')
        """,
        ("ramp-a", "Llanowar Elves", "Creature — Elf Druid", json.dumps(["G"])),
    )
    conn.execute(
        """
        INSERT INTO card_mechanic_tags (oracle_id, tag, layer, source)
        VALUES ('ramp-a', 'ramp', 'theme', 'test')
        """
    )
    conn.execute(
        """
        INSERT INTO cards (
            oracle_id, name, type_line, mana_cost, cmc, color_identity,
            keywords, commander_legal, commander_eligible, is_basic_land,
            edhrec_rank, price_usd, price_known, oracle_text
        ) VALUES (?, ?, ?, '{1}{G}', 2.0, ?, '[]', 1, 0, 0, 800, 1.5, 1, 'Draw a card.')
        """,
        ("draw-a", "Opt", "Instant", json.dumps(["G"])),
    )
    conn.execute(
        """
        INSERT INTO card_mechanic_tags (oracle_id, tag, layer, source)
        VALUES ('draw-a', 'draw', 'theme', 'test')
        """
    )
    conn.execute(
        """
        INSERT INTO cards (
            oracle_id, name, type_line, mana_cost, cmc, color_identity,
            keywords, commander_legal, commander_eligible, is_basic_land,
            edhrec_rank, price_usd, price_known, oracle_text, produced_mana
        ) VALUES (?, ?, 'Creature — Elf', '{1}{G}', 2.0, ?, '[]', 1, 0, 0, 600, 1.0, 1, '', '[]')
        """,
        ("syn-a", "Token Maker", json.dumps(["G"])),
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
            edhrec_rank, price_usd, price_known, produced_mana
        ) VALUES ('forest-db', 'Forest', 'Basic Land — Forest', '', 0.0, '[]', '[]', 1, 0, 1, 10, 0.1, 1, '["G"]')
        """
    )
    conn.commit()
    return conn


def test_load_deck_json_parses_criteria_and_cards(tmp_path) -> None:
    path = tmp_path / "test.deck.json"
    path.write_text(json.dumps(_minimal_deck_json()), encoding="utf-8")
    loaded = load_deck_json(path)
    assert loaded.criteria.themes == ["voltron"]
    assert loaded.criteria.commander_oracle_ids == ["cmd"]
    assert len(loaded.cards) == 3
    assert loaded.cards[0].slot == "ramp"


def test_load_deck_json_header_estimated_deck_without_budget(tmp_path) -> None:
    """Deck files without budget still work; MD shows estimate after regen (separate test)."""
    path = tmp_path / "nobudget.deck.json"
    path.write_text(json.dumps(_minimal_deck_json(budget_usd=None)), encoding="utf-8")
    loaded = load_deck_json(path)
    assert loaded.criteria.budget_usd is None


def test_load_deck_json_rejects_bad_schema(tmp_path) -> None:
    path = tmp_path / "bad.deck.json"
    path.write_text(json.dumps({"schema_version": "2.0"}), encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported schema_version"):
        load_deck_json(path)


def test_refill_deck_slot_keeps_other_slots(reload_db: sqlite3.Connection) -> None:
    from mtg_deck_tools.builder.deck import DeckCard

    fixed = [
        DeckCard(
            oracle_id="ramp-1",
            name="Ramp Rock",
            slot="ramp",
            quantity=1,
            cmc=2.0,
            mana_cost="{2}",
            type_line="Artifact",
            price_usd=1.0,
            price_known=True,
            scryfall_uri=None,
            image_uri=None,
        ),
        DeckCard(
            oracle_id="forest",
            name="Forest",
            slot="lands",
            quantity=1,
            cmc=0.0,
            mana_cost="",
            type_line="Basic Land — Forest",
            price_usd=0.1,
            price_known=True,
            scryfall_uri=None,
            image_uri=None,
        ),
    ]
    criteria = DeckCriteria(
        themes=["voltron"],
        colors=["G"],
        commander_oracle_ids=["cmd"],
        slot_template=_minimal_deck_json()["criteria"]["slot_template"],
        seed=1,
    )
    result = refill_deck_slot(
        reload_db,
        criteria,
        identity=["G"],
        commander_oracle_ids=["cmd"],
        fixed_cards=fixed,
        refill_slot="synergy",
        seed=1,
    )
    slots = {c.slot for c in result.cards}
    assert "ramp" in slots
    assert "lands" in slots
    assert "synergy" in slots
    assert all(c.name != "Synergy Piece" for c in result.cards if c.slot == "synergy")
    assert any("Refilled slot 'synergy'" in w for w in result.warnings)


def test_run_generate_from_deck_rejects_incomplete_regen(
    tmp_path, reload_db: sqlite3.Connection, monkeypatch
) -> None:
    deck_path = tmp_path / "deck.deck.json"
    deck_path.write_text(json.dumps(_minimal_deck_json()), encoding="utf-8")

    def fake_require_db(_path):
        return reload_db

    monkeypatch.setattr("mtg_deck_tools.builder.reload.require_db", fake_require_db)

    with pytest.raises(RuntimeError, match="valid deck"):
        run_generate_from_deck(
            deck_path,
            output_dir=tmp_path / "out",
            seed=1,
        )
