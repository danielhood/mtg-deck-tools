"""Tests for wizard back-navigation helpers (UX4)."""

from __future__ import annotations

import pytest

from mtg_deck_tools.wizard.navigation import (
    FIRST_STEP_WITH_POST_NAVIGATION,
    NavigationAction,
    NavigationChoice,
    WIZARD_STEP_COUNT,
    back_target_steps,
    build_navigation_choices,
    downstream_step_numbers,
    resolve_navigation,
)


def test_wizard_has_seven_steps() -> None:
    assert WIZARD_STEP_COUNT == 7


def test_post_navigation_starts_after_step_one() -> None:
    assert FIRST_STEP_WITH_POST_NAVIGATION == 2


def test_back_target_steps_after_step_one_is_empty() -> None:
    assert back_target_steps(completed_step=1) == []


def test_back_target_steps_after_step_five() -> None:
    labels = [s.label for s in back_target_steps(completed_step=5)]
    assert labels == [
        "Themes & slots",
        "Include / avoid mechanics",
        "Synergy & dependencies",
        "Colors",
    ]


def test_downstream_step_numbers_inclusive() -> None:
    assert downstream_step_numbers(from_step=2, through_step=5) == [2, 3, 4, 5]


def test_downstream_step_numbers_rejects_inverted_range() -> None:
    with pytest.raises(ValueError, match="from_step"):
        downstream_step_numbers(from_step=5, through_step=2)


def test_build_navigation_choices_step_one_has_no_back() -> None:
    values = [c.value for c in build_navigation_choices(completed_step=1, context="step")]
    back_choices = [v for v in values if v.action == NavigationAction.BACK]
    assert back_choices == []
    assert values[0].action == NavigationAction.CONTINUE
    assert values[-1].action == NavigationAction.CANCEL


def test_build_navigation_preflight_lists_all_steps() -> None:
    choices = build_navigation_choices(context="preflight")
    titles = [c.title for c in choices]
    values = [c.value for c in choices]
    assert titles[1] == "Re-run criteria review"
    assert values[1].action == NavigationAction.RESTART_CURRENT
    back_steps = sorted(
        v.back_to_step for v in values if v.action == NavigationAction.BACK
    )
    assert back_steps == list(range(1, WIZARD_STEP_COUNT + 1))


def test_build_navigation_includes_rerun_current_step() -> None:
    titles = [c.title for c in build_navigation_choices(completed_step=5, context="step")]
    assert titles[1] == "Re-run step 5 — Budget & card prices"
    assert "Back to step 4 — Colors" in titles


def test_resolve_navigation_allows_rerun_current_step() -> None:
    choice = NavigationChoice(NavigationAction.BACK, back_to_step=5)
    resolved = resolve_navigation(choice, completed_step=5)
    assert resolved.back_to_step == 5


def test_resolve_navigation_rejects_back_to_later_step() -> None:
    choice = NavigationChoice(NavigationAction.BACK, back_to_step=6)
    with pytest.raises(ValueError, match="later"):
        resolve_navigation(choice, completed_step=5)
