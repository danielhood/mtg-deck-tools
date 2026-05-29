"""Run the full deck-building wizard."""

from __future__ import annotations

from pathlib import Path

from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.wizard.step1 import run_step1
from mtg_deck_tools.wizard.step2 import run_step2
from mtg_deck_tools.wizard.step3 import run_step3
from mtg_deck_tools.wizard.step4 import run_step4
from mtg_deck_tools.wizard.step5 import run_step5
from mtg_deck_tools.wizard.summary import print_wizard_summary


def run_wizard(
    *,
    seed: int | None = None,
    db_path: Path | None = None,
) -> DeckCriteria:
    """Run all five wizard steps and return complete DeckCriteria."""
    criteria = run_step1(seed=seed, show_summary=False)
    criteria = run_step2(criteria)
    criteria = run_step3(criteria)
    criteria = run_step4(criteria, db_path=db_path)
    criteria = run_step5(criteria)
    print_wizard_summary(criteria)
    return criteria
