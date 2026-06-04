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


@dataclass(frozen=True)
class NavigationChoice:
    action: NavigationAction
    back_to_step: int | None = None


def back_target_steps(*, completed_step: int) -> list[WizardStepMeta]:
    """Steps the user may jump back to after completing `completed_step` (1–7)."""
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
    if choice.back_to_step >= completed_step:
        raise ValueError("Can only go back to an earlier step")
    return choice
