"""Wizard step 6: minimum card rarity."""

from __future__ import annotations

import questionary
from rich.panel import Panel

from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.rules.rarity import RARITY_ORDER, format_min_rarity_display
from mtg_deck_tools.wizard.common import WIZARD_STYLE, console, require_tty


def _prompt_min_rarity(criteria: DeckCriteria) -> DeckCriteria:
    choices = [
        questionary.Choice(title=format_min_rarity_display(rarity), value=rarity)
        for rarity in RARITY_ORDER
    ]
    picked = questionary.select(
        "Minimum card rarity",
        choices=choices,
        default=criteria.min_rarity,
        style=WIZARD_STYLE,
    ).ask()
    if picked is None:
        raise KeyboardInterrupt
    return criteria.model_copy(update={"min_rarity": picked})


def run_step6(criteria: DeckCriteria) -> DeckCriteria:
    """Interactive step 6: minimum card rarity for the maindeck."""
    require_tty()

    console.print(
        Panel(
            "[bold]Step 6 of 6[/bold] — Card rarity\n"
            "Exclude maindeck cards below this rarity (commander is not filtered here).",
            title="MTG Deck Tools",
            border_style="cyan",
        )
    )

    return _prompt_min_rarity(criteria)
