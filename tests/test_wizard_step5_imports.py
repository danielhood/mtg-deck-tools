"""Regression: commander step must import helpers it calls."""

from __future__ import annotations

import mtg_deck_tools.wizard.step5 as step5


def test_step5_imports_filter_eligible_commander_ids() -> None:
    assert "filter_eligible_commander_ids" in step5.__dict__
