"""Wizard step navigation: continue, back, cancel (UX4)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal

import questionary

from mtg_deck_tools.wizard.common import WIZARD_STYLE, require_tty

WizardContext = Literal["step", "preflight"]


class NavigationAction(str, Enum):
    CONTINUE = "continue"
    BACK = "back"
    RESTART_CURRENT = "restart_current"
    CANCEL = "cancel"


@dataclass(frozen=True)
class WizardStepMeta:
    """One interactive wizard step (1-based number matches UI)."""

    number: int
    label: str


WIZARD_STEPS: tuple[WizardStepMeta, ...] = (
    WizardStepMeta(1, "Themes & slots"),
    WizardStepMeta(2, "Include / avoid mechanics"),
    WizardStepMeta(3, "Synergy & dependencies"),
    WizardStepMeta(4, "Colors"),
    WizardStepMeta(5, "Budget & card prices"),
    WizardStepMeta(6, "Commander"),
    WizardStepMeta(7, "Card rarity"),
)

WIZARD_STEP_COUNT = len(WIZARD_STEPS)

# Step 1 advances straight to step 2; continue/back/cancel starts after step 2.
FIRST_STEP_WITH_POST_NAVIGATION = 2


@dataclass(frozen=True)
class NavigationChoice:
    action: NavigationAction
    back_to_step: int | None = None


def wizard_step_meta(step_number: int) -> WizardStepMeta:
    if not 1 <= step_number <= WIZARD_STEP_COUNT:
        raise ValueError(f"step_number must be 1–{WIZARD_STEP_COUNT}")
    return WIZARD_STEPS[step_number - 1]


def back_target_steps(*, completed_step: int) -> list[WizardStepMeta]:
    """Earlier steps the user may jump back to after completing `completed_step` (1–7)."""
    if completed_step <= 1:
        return []
    return [s for s in WIZARD_STEPS if s.number < completed_step]


def downstream_step_numbers(*, from_step: int, through_step: int) -> list[int]:
    """Inclusive range of step numbers to re-run after editing an earlier step."""
    if from_step > through_step:
        raise ValueError("from_step cannot exceed through_step")
    return list(range(from_step, through_step + 1))


def build_navigation_choices(
    *,
    completed_step: int | None = None,
    context: WizardContext = "step",
) -> list[questionary.Choice]:
    """Build questionary choices for continue / back / cancel."""
    choices: list[questionary.Choice] = [
        questionary.Choice(title="Continue", value=NavigationChoice(NavigationAction.CONTINUE)),
    ]

    if context == "preflight":
        choices.append(
            questionary.Choice(
                title="Re-run criteria review",
                value=NavigationChoice(NavigationAction.RESTART_CURRENT),
            )
        )
        for step in WIZARD_STEPS:
            choices.append(
                questionary.Choice(
                    title=f"Back to step {step.number} — {step.label}",
                    value=NavigationChoice(
                        NavigationAction.BACK,
                        back_to_step=step.number,
                    ),
                )
            )
    elif completed_step is not None:
        if completed_step >= FIRST_STEP_WITH_POST_NAVIGATION:
            current = wizard_step_meta(completed_step)
            choices.append(
                questionary.Choice(
                    title=f"Re-run step {current.number} — {current.label}",
                    value=NavigationChoice(
                        NavigationAction.BACK,
                        back_to_step=current.number,
                    ),
                )
            )
        for step in back_target_steps(completed_step=completed_step):
            choices.append(
                questionary.Choice(
                    title=f"Back to step {step.number} — {step.label}",
                    value=NavigationChoice(
                        NavigationAction.BACK,
                        back_to_step=step.number,
                    ),
                )
            )

    choices.append(
        questionary.Choice(
            title="Cancel wizard",
            value=NavigationChoice(NavigationAction.CANCEL),
        )
    )
    return choices


def prompt_wizard_navigation(
    *,
    completed_step: int | None = None,
    context: WizardContext = "step",
) -> NavigationChoice:
    """
    Ask whether to continue, revise an earlier step, or cancel.

    `completed_step` is the 1-based step just finished (required when context is "step").
    """
    require_tty()
    if context == "step":
        if completed_step is None or not 1 <= completed_step <= WIZARD_STEP_COUNT:
            raise ValueError("completed_step must be 1–7 when context is 'step'")

    prompt = (
        "Criteria review — what next?"
        if context == "preflight"
        else f"Step {completed_step} complete — what next?"
    )

    picked = questionary.select(
        prompt,
        choices=build_navigation_choices(completed_step=completed_step, context=context),
        style=WIZARD_STYLE,
    ).ask()
    if picked is None:
        raise KeyboardInterrupt
    return picked


def resolve_navigation(
    choice: NavigationChoice,
    *,
    completed_step: int,
) -> NavigationChoice:
    """Validate back targets for mid-flow navigation."""
    if choice.action != NavigationAction.BACK:
        return choice
    if choice.back_to_step is None:
        raise ValueError("Back navigation requires back_to_step")
    if choice.back_to_step > completed_step:
        raise ValueError("Cannot go back to a later step")
    return choice
