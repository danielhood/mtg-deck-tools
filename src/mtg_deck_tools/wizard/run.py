"""Run the full deck-building wizard."""

from __future__ import annotations

from pathlib import Path

from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.wizard.navigation import (
    NavigationAction,
    NavigationChoice,
    WIZARD_STEP_COUNT,
    downstream_step_numbers,
    prompt_wizard_navigation,
    resolve_navigation,
)
from mtg_deck_tools.wizard.preflight import run_preflight
from mtg_deck_tools.wizard.step1 import run_step1
from mtg_deck_tools.wizard.step2 import run_step2
from mtg_deck_tools.wizard.step3 import run_step3
from mtg_deck_tools.wizard.step3_synergy import run_step3_synergy
from mtg_deck_tools.wizard.step4 import run_step4
from mtg_deck_tools.wizard.step5 import run_step5
from mtg_deck_tools.wizard.step6 import run_step6
from mtg_deck_tools.wizard.summary import print_wizard_summary


def _run_step(
    step: int,
    criteria: DeckCriteria,
    *,
    seed: int | None,
    db_path: Path | None,
) -> DeckCriteria:
    if step == 1:
        return run_step1(seed=seed, criteria=criteria, show_summary=False)
    if step == 2:
        return run_step2(criteria)
    if step == 3:
        return run_step3_synergy(criteria)
    if step == 4:
        return run_step3(criteria)
    if step == 5:
        return run_step4(criteria)
    if step == 6:
        return run_step5(criteria, db_path=db_path)
    if step == 7:
        return run_step6(criteria)
    raise ValueError(f"Unknown wizard step: {step}")


def _handle_navigation_choice(
    choice: NavigationChoice,
    *,
    completed_step: int,
) -> tuple[NavigationAction, int | None]:
    if choice.action == NavigationAction.CANCEL:
        raise RuntimeError("Wizard cancelled.")
    if choice.action == NavigationAction.CONTINUE:
        return NavigationAction.CONTINUE, None
    resolved = resolve_navigation(choice, completed_step=completed_step)
    return NavigationAction.BACK, resolved.back_to_step


def _rerun_from_step(
    *,
    from_step: int,
    through_step: int,
    criteria: DeckCriteria,
    seed: int | None,
    db_path: Path | None,
) -> DeckCriteria:
    for step in downstream_step_numbers(from_step=from_step, through_step=through_step):
        criteria = _run_step(step, criteria, seed=seed, db_path=db_path)
    return criteria


def _run_step_with_navigation(
    step: int,
    criteria: DeckCriteria,
    *,
    seed: int | None,
    db_path: Path | None,
) -> DeckCriteria:
    """Run one step, then prompt until the user continues or cancels."""
    criteria = _run_step(step, criteria, seed=seed, db_path=db_path)
    while True:
        choice = prompt_wizard_navigation(completed_step=step, context="step")
        action, back_to = _handle_navigation_choice(choice, completed_step=step)
        if action == NavigationAction.CONTINUE:
            return criteria
        assert back_to is not None
        criteria = _rerun_from_step(
            from_step=back_to,
            through_step=step,
            criteria=criteria,
            seed=seed,
            db_path=db_path,
        )


def run_wizard(
    *,
    seed: int | None = None,
    db_path: Path | None = None,
) -> DeckCriteria:
    """Run all seven wizard steps and return complete DeckCriteria."""
    criteria = DeckCriteria(seed=seed)
    for step in range(1, WIZARD_STEP_COUNT + 1):
        criteria = _run_step_with_navigation(
            step,
            criteria,
            seed=seed,
            db_path=db_path,
        )

    while True:
        criteria, action, back_to = run_preflight(criteria)
        if action == NavigationAction.CONTINUE:
            break
        assert back_to is not None
        criteria = _rerun_from_step(
            from_step=back_to,
            through_step=WIZARD_STEP_COUNT,
            criteria=criteria,
            seed=seed,
            db_path=db_path,
        )

    print_wizard_summary(criteria)
    return criteria
