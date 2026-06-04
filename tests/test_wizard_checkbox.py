"""Wizard checkbox preselection (questionary 2.x)."""

from questionary import Choice

from mtg_deck_tools.wizard.common import apply_checkbox_selection


def test_apply_checkbox_selection_empty() -> None:
    options = apply_checkbox_selection(
        [Choice("tokens — Token synergy", value="tokens")],
        [],
    )
    assert options[0].checked is False


def test_apply_checkbox_selection_preserves_prior() -> None:
    options = apply_checkbox_selection(
        [
            Choice("tokens", value="tokens"),
            Choice("artifacts", value="artifacts"),
        ],
        ["artifacts"],
    )
    assert options[0].checked is False
    assert options[1].checked is True


def test_checkbox_builds_with_no_prior_selection() -> None:
    """Regression: questionary rejects default=[] on checkbox prompts."""
    import questionary

    options = apply_checkbox_selection(
        [Choice("tokens", value="tokens")],
        [],
    )
    questionary.checkbox("Themes", choices=options)
