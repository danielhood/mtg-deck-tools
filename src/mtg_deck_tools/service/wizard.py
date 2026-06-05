"""Interactive wizard facade (CLI-only; API uses criteria-based generate)."""

from __future__ import annotations

from pathlib import Path

from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.wizard.run import run_wizard


def run_interactive_wizard(
    *,
    seed: int | None = None,
    db_path: Path | None = None,
    initial_criteria: DeckCriteria | None = None,
    prepopulated_from: Path | None = None,
) -> DeckCriteria:
    """Run the terminal wizard and return complete DeckCriteria."""
    return run_wizard(
        seed=seed,
        db_path=db_path,
        initial_criteria=initial_criteria,
        prepopulated_from=prepopulated_from,
    )
