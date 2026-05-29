"""Wizard step 5: budget."""

from __future__ import annotations

import questionary
from rich.panel import Panel

from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.wizard.common import WIZARD_STYLE, console, require_tty


def _validate_budget_text(text: str) -> bool | str:
    text = text.strip()
    if not text:
        return "Enter a dollar amount"
    try:
        value = float(text)
    except ValueError:
        return "Enter a valid number (e.g. 150)"
    if value <= 0:
        return "Budget must be greater than 0"
    return True


def run_step5(criteria: DeckCriteria) -> DeckCriteria:
    """Interactive step 5: optional total deck budget in USD."""
    require_tty()

    console.print(
        Panel(
            "[bold]Step 5 of 5[/bold] — Budget\n"
            "Optional cap using Scryfall prices. Cards without prices are allowed with a warning.",
            title="MTG Deck Tools",
            border_style="cyan",
        )
    )

    set_budget = questionary.confirm(
        "Set a total deck budget (USD)?",
        default=False,
        style=WIZARD_STYLE,
    ).ask()
    if set_budget is None:
        raise KeyboardInterrupt
    if not set_budget:
        return criteria

    raw = questionary.text(
        "Maximum deck budget (USD)",
        default="150",
        style=WIZARD_STYLE,
        validate=_validate_budget_text,
    ).ask()
    if raw is None:
        raise KeyboardInterrupt

    return criteria.model_copy(update={"budget_usd": float(raw.strip())})
