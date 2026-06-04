"""UX5: wizard prepopulate from saved .deck.json."""

from __future__ import annotations

import json

import pytest

from mtg_deck_tools.builder.deck_load import load_deck_criteria_for_wizard
from mtg_deck_tools.wizard.slots import load_slot_template_config


def _criteria_only_deck_json() -> dict:
    slots = dict(load_slot_template_config().default)
    return {
        "schema_version": "1.0",
        "criteria": {
            "themes": ["tokens"],
            "colors": ["G", "U"],
            "include_mechanics": ["flash"],
            "avoid_mechanics": [],
            "slot_template": slots,
            "seed": 7,
            "strict_dependencies": True,
        },
        "commanders": [
            {
                "oracle_id": "cmd-a",
                "name": "Saved Commander",
                "type_line": "Legendary Creature",
            }
        ],
    }


def test_load_deck_criteria_for_wizard_without_cards(tmp_path) -> None:
    path = tmp_path / "saved.deck.json"
    path.write_text(json.dumps(_criteria_only_deck_json()), encoding="utf-8")
    criteria = load_deck_criteria_for_wizard(path)
    assert criteria.themes == ["tokens"]
    assert criteria.colors == ["G", "U"]
    assert criteria.include_mechanics == ["flash"]
    assert criteria.strict_dependencies is True
    assert criteria.seed == 7
    assert criteria.commander_oracle_ids == ["cmd-a"]


def test_load_deck_criteria_for_wizard_keeps_criteria_commander_ids(tmp_path) -> None:
    data = _criteria_only_deck_json()
    data["criteria"]["commander_oracle_ids"] = ["from-criteria"]
    path = tmp_path / "saved.deck.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    criteria = load_deck_criteria_for_wizard(path)
    assert criteria.commander_oracle_ids == ["from-criteria"]


def test_load_deck_criteria_for_wizard_requires_criteria_block(tmp_path) -> None:
    path = tmp_path / "empty.deck.json"
    path.write_text(
        json.dumps({"schema_version": "1.0", "cards": []}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="no criteria block"):
        load_deck_criteria_for_wizard(path)
