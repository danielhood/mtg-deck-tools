"""Commander rules helper tests."""

from mtg_deck_tools.rules.commander import (
    color_identity_subset,
    detect_partner_kind,
    is_commander_eligible,
    is_playable_card,
    parse_color_identity,
)


def test_color_identity_subset():
    commander = parse_color_identity(["B", "G"])
    assert color_identity_subset(parse_color_identity(["B"]), commander)
    assert color_identity_subset(parse_color_identity([]), commander)
    assert not color_identity_subset(parse_color_identity(["R"]), commander)


def test_commander_eligible_creature():
    assert is_commander_eligible("Legendary Creature — Elf Druid", "")
    assert not is_commander_eligible("Creature — Elf", "")


def test_commander_eligible_special():
    text = "Some text. This card can be your commander."
    assert is_commander_eligible("Legendary Enchantment — Background", text)


def test_partner_detection():
    assert detect_partner_kind("Partner with Thrasios", []) == "partner_with"
    assert detect_partner_kind("", ["Partner"]) == "partner"


def test_playable_card_filters():
    assert is_playable_card(layout="normal", lang="en", commander_legal=True)
    assert not is_playable_card(layout="token", lang="en", commander_legal=True)
    assert not is_playable_card(layout="normal", lang="en", commander_legal=False)
