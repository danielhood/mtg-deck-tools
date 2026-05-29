"""Commander helper tests."""

from mtg_deck_tools.wizard.commanders import CommanderRow, combined_color_identity


def test_combined_color_identity():
    a = CommanderRow("1", "A", ["B", "G"], None, None)
    b = CommanderRow("2", "B", ["U", "G"], "partner", None)
    assert combined_color_identity([a, b]) == ["U", "B", "G"]
