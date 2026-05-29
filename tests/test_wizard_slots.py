"""Wizard slot template tests."""

from mtg_deck_tools.wizard.slots import (
    COMMANDER_DECK_SIZE,
    load_slot_template_config,
    slot_template_total,
    suggest_lands_count,
    validate_slot_template,
)
from mtg_deck_tools.wizard.themes import archetype_choices


def test_default_slot_template_totals_99():
    config = load_slot_template_config()
    assert slot_template_total(config.default) == COMMANDER_DECK_SIZE
    assert validate_slot_template(config.default, config) == []


def test_validate_slot_template_rejects_bad_total():
    config = load_slot_template_config()
    bad = dict(config.default)
    bad["ramp"] = config.default["ramp"] + 1
    errors = validate_slot_template(bad, config)
    assert any("99" in e for e in errors)


def test_validate_slot_template_rejects_out_of_bounds():
    config = load_slot_template_config()
    bad = dict(config.default)
    bad["ramp"] = config.bounds["ramp"].max + 1
    errors = validate_slot_template(bad, config)
    assert any("Ramp" in e or "ramp" in e.lower() for e in errors)


def test_suggest_lands_count():
    config = load_slot_template_config()
    slots = {k: v for k, v in config.default.items() if k != "lands"}
    assert suggest_lands_count(slots) == config.default["lands"]


def test_default_slot_summary_from_order():
    config = load_slot_template_config()
    summary = ", ".join(
        f"{config.labels.get(slot, slot)} {config.default[slot]}"
        for slot in config.order
        if slot in config.default
    )
    assert "Ramp 10" in summary
    assert "Lands 31" in summary


def test_archetype_choices_exclude_slot_fillers():
    ids = {c.id for c in archetype_choices()}
    assert "aristocrats" in ids
    assert "tokens" in ids
    assert "ramp" not in ids
    assert "draw" not in ids
    assert "removal" not in ids
