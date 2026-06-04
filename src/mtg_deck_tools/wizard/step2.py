"""Wizard step 2: include / avoid keyword mechanics."""

from __future__ import annotations

import questionary
from rich.panel import Panel

from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.wizard.common import (
    WIZARD_STYLE,
    apply_checkbox_selection,
    console,
    format_tag_label,
    require_tty,
)
from mtg_deck_tools.wizard.mechanics import (
    MechanicChoice,
    keyword_mechanic_choices,
    validate_mechanic_lists,
)


def _prompt_mechanic_checkbox(
    prompt: str,
    choices: list[MechanicChoice],
    *,
    selected: list[str],
) -> list[str]:
    if not choices:
        return []

    options = apply_checkbox_selection(
        [
            questionary.Choice(
                title=format_tag_label(c.id, c.description),
                value=c.id,
            )
            for c in choices
        ],
        selected,
    )
    picked = questionary.checkbox(
        prompt,
        choices=options,
        style=WIZARD_STYLE,
        instruction="(Space to toggle, Enter to confirm; none is OK)",
    ).ask()
    if picked is None:
        raise KeyboardInterrupt
    return list(picked)


def run_step2(criteria: DeckCriteria) -> DeckCriteria:
    """Interactive step 2: keyword mechanics to prefer or exclude."""
    require_tty()
    choices = keyword_mechanic_choices()

    console.print(
        Panel(
            "[bold]Step 2 of 7[/bold] — Include / avoid mechanics\n"
            "Prefer cards with certain keywords, or hard-exclude others from the pool.",
            title="MTG Deck Tools",
            border_style="cyan",
        )
    )

    include = _prompt_mechanic_checkbox(
        "Include mechanics (prefer in deck)",
        choices,
        selected=criteria.include_mechanics,
    )
    avoid = _prompt_mechanic_checkbox(
        "Avoid mechanics (exclude from deck)",
        choices,
        selected=criteria.avoid_mechanics,
    )

    errors = validate_mechanic_lists(include, avoid)
    if errors:
        raise RuntimeError(errors[0])

    return criteria.model_copy(
        update={
            "include_mechanics": include,
            "avoid_mechanics": avoid,
        }
    )
