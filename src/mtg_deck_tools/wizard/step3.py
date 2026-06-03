"""Wizard step 3: color identity."""

from __future__ import annotations

import questionary
from rich.panel import Panel

from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.wizard.common import COLOR_CHOICES, WIZARD_STYLE, console, require_tty


def run_step3(criteria: DeckCriteria) -> DeckCriteria:
    """Interactive step 3: mana colors for commander and deck."""
    require_tty()

    console.print(
        Panel(
            "[bold]Step 4 of 6[/bold] — Colors\n"
            "Pick the colors your commander must use. Leave none for any (including colorless).",
            title="MTG Deck Tools",
            border_style="cyan",
        )
    )

    options = [
        questionary.Choice(title=f"{letter} — {name}", value=letter)
        for letter, name in COLOR_CHOICES
    ]
    selected = questionary.checkbox(
        "Commander color identity",
        choices=options,
        style=WIZARD_STYLE,
        instruction="(Space to toggle, Enter to confirm)",
    ).ask()
    if selected is None:
        raise KeyboardInterrupt

    return criteria.model_copy(update={"colors": sorted(selected)})
