"""Wizard preflight: criteria linter warnings and user confirmation (UX3)."""

from __future__ import annotations

from rich.panel import Panel

from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.rules.criteria_linter import CriteriaWarning, lint_criteria
from mtg_deck_tools.wizard.common import console, require_tty
from mtg_deck_tools.wizard.navigation import (
    NavigationAction,
    NavigationChoice,
    prompt_wizard_navigation,
)


def format_criteria_warnings(warnings: list[CriteriaWarning]) -> str:
    """Bullet list of linter messages for display."""
    if not warnings:
        return ""
    return "\n".join(f"  • [{w.rule_id}] {w.message}" for w in warnings)


def run_preflight(criteria: DeckCriteria) -> tuple[DeckCriteria, NavigationAction, int | None]:
    """
    Show criteria linter warnings and require acknowledgment before finishing.

    Returns (criteria, CONTINUE, None) when there are no warnings or the user continues.
    Returns (criteria, BACK, step_number) when the user chooses to revise an earlier step.
    """
    require_tty()
    warnings = lint_criteria(criteria)
    if not warnings:
        return criteria, NavigationAction.CONTINUE, None

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

    while True:
        choice = prompt_wizard_navigation(context="preflight")
        if choice.action == NavigationAction.CANCEL:
            raise RuntimeError("Wizard cancelled at criteria review.")
        if choice.action == NavigationAction.RESTART_CURRENT:
            continue
        if choice.action == NavigationAction.BACK:
            if choice.back_to_step is None:
                raise ValueError("Back navigation requires back_to_step")
            return criteria, NavigationAction.BACK, choice.back_to_step
        return criteria, NavigationAction.CONTINUE, None
