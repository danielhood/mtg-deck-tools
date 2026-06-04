"""Wizard step 3: synergy strictness and mechanic focus presets (UX2)."""

from __future__ import annotations

import questionary
from rich.panel import Panel

from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.wizard.common import WIZARD_STYLE, console, require_tty
from mtg_deck_tools.wizard.dependencies import (
    FOCUS_LEVELS,
    activated_profiles_for_wizard,
)


def _focus_level_choices() -> list[questionary.Choice]:
    return [
        questionary.Choice(
            title="Default — use theme/mechanic activation only",
            value=None,
        ),
        questionary.Choice(
            title="Incidental — splash; mechanic appears but is not the main plan",
            value="incidental",
        ),
        questionary.Choice(
            title="Supported — typical Commander support package",
            value="supported",
        ),
        questionary.Choice(
            title="Focused — main secondary plan; higher counts",
            value="focused",
        ),
        questionary.Choice(
            title="Engine — deck built around this mechanic",
            value="engine",
        ),
    ]


def _retained_mechanic_focus(criteria: DeckCriteria) -> dict[str, str]:
    activated_ids = {e.profile_id for e in activated_profiles_for_wizard(criteria)}
    return {
        profile_id: level
        for profile_id, level in criteria.mechanic_focus.items()
        if profile_id in activated_ids and level in FOCUS_LEVELS
    }


def _prompt_focus_levels(criteria: DeckCriteria) -> dict[str, str]:
    activated = activated_profiles_for_wizard(criteria)
    if not activated:
        return {}

    has_focus = bool(_retained_mechanic_focus(criteria))
    set_focus = questionary.confirm(
        f"Set synergy focus levels for {len(activated)} activated mechanic(s)?",
        default=has_focus,
        style=WIZARD_STYLE,
    ).ask()
    if set_focus is None:
        raise KeyboardInterrupt
    if not set_focus:
        return _retained_mechanic_focus(criteria)

    focus: dict[str, str] = {}
    for entry in activated:
        current = criteria.mechanic_focus.get(entry.profile_id)
        picked = questionary.select(
            entry.prompt_label,
            choices=_focus_level_choices(),
            default=current,
            style=WIZARD_STYLE,
        ).ask()
        if picked is None:
            raise KeyboardInterrupt
        if picked in FOCUS_LEVELS:
            focus[entry.profile_id] = picked
    return focus


def run_step3_synergy(criteria: DeckCriteria) -> DeckCriteria:
    """Interactive step 3: dependency strictness and optional mechanic focus."""
    require_tty()

    console.print(
        Panel(
            "[bold]Step 3 of 7[/bold] — Synergy & dependencies\n"
            "Control how strictly the builder enforces card synergies and optional "
            "focus levels for mechanics you selected in steps 1–2. "
            "Same options as [bold]--strict-dependencies[/bold] and "
            "[bold]--repair-dependencies[/bold] on generate.",
            title="MTG Deck Tools",
            border_style="cyan",
        )
    )

    strict = questionary.confirm(
        "Block picks with no valid target (strict dependencies)?",
        default=criteria.strict_dependencies,
        style=WIZARD_STYLE,
    ).ask()
    if strict is None:
        raise KeyboardInterrupt

    repair = questionary.confirm(
        "Run a post-build repair pass for dependency gaps?",
        default=criteria.repair_dependencies,
        style=WIZARD_STYLE,
    ).ask()
    if repair is None:
        raise KeyboardInterrupt

    focus = _prompt_focus_levels(criteria)

    return criteria.model_copy(
        update={
            "strict_dependencies": bool(strict),
            "repair_dependencies": bool(repair),
            "mechanic_focus": focus,
        }
    )
