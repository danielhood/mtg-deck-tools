"""Wizard preflight: criteria linter warnings and user confirmation (UX3)."""

from __future__ import annotations

import questionary
from rich.panel import Panel

from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.rules.criteria_linter import CriteriaWarning, lint_criteria
from mtg_deck_tools.wizard.common import WIZARD_STYLE, console, require_tty


def format_criteria_warnings(warnings: list[CriteriaWarning]) -> str:
    """Bullet list of linter messages for display."""
    if not warnings:
        return ""
    return "\n".join(f"  • [{w.rule_id}] {w.message}" for w in warnings)


def run_preflight(criteria: DeckCriteria) -> DeckCriteria:
    """
    Show criteria linter warnings and require acknowledgment before finishing.

    Returns criteria unchanged when there are no warnings or the user confirms.
    """
    require_tty()
    warnings = lint_criteria(criteria)
    if not warnings:
        return criteria

    console.print(
        Panel(
            "[bold]Criteria review[/bold]\n"
            "The builder spotted possible issues with your selections. "
            "These are warnings only — generation will still run unless you cancel.\n\n"
            + format_criteria_warnings(warnings),
            title="MTG Deck Tools",
            border_style="yellow",
        )
    )

    proceed = questionary.confirm(
        "Continue with these criteria?",
        default=True,
        style=WIZARD_STYLE,
    ).ask()
    if proceed is None:
        raise KeyboardInterrupt
    if not proceed:
        raise RuntimeError("Wizard cancelled at criteria review.")

    return criteria
