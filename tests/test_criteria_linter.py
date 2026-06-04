"""UX3 criteria linter preflight checks."""

from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.rules.criteria_linter import lint_criteria


def _rule_ids(criteria: DeckCriteria) -> set[str]:
    return {w.rule_id for w in lint_criteria(criteria)}


def test_lint_clean_criteria_empty() -> None:
    assert lint_criteria(DeckCriteria()) == []


def test_lint_include_avoid_overlap() -> None:
    criteria = DeckCriteria(include_mechanics=["energy"], avoid_mechanics=["energy"])
    ids = _rule_ids(criteria)
    assert "INCLUDE_AVOID_OVERLAP" in ids


def test_lint_avoid_blocks_active_profile() -> None:
    criteria = DeckCriteria(
        include_mechanics=["energy"],
        avoid_mechanics=["energy"],
    )
    messages = [w.message for w in lint_criteria(criteria)]
    assert any("Energy" in m for m in messages)


def test_lint_avoid_focus_conflict() -> None:
    criteria = DeckCriteria(
        avoid_mechanics=["rad"],
        mechanic_focus={"rad": "engine"},
    )
    ids = _rule_ids(criteria)
    assert "AVOID_FOCUS_CONFLICT" in ids or "AVOID_BLOCKS_PROFILE" in ids


def test_lint_voltron_avoid_equip() -> None:
    criteria = DeckCriteria(themes=["voltron"], avoid_mechanics=["equip"])
    ids = _rule_ids(criteria)
    assert "AVOID_THEME_CONFLICT" in ids
    assert "AVOID_BLOCKS_PROFILE" in ids


def test_lint_tokens_aristocrats_theme_stack() -> None:
    criteria = DeckCriteria(themes=["tokens", "aristocrats"])
    ids = _rule_ids(criteria)
    assert "THEMED_SHARE_STACK" in ids


def test_lint_too_many_focused_profiles() -> None:
    criteria = DeckCriteria(
        mechanic_focus={
            "energy": "focused",
            "rad": "engine",
            "oil": "focused",
        },
    )
    ids = _rule_ids(criteria)
    assert "TOO_MANY_FOCUSED_PROFILES" in ids


def test_lint_over_constrained_budget() -> None:
    criteria = DeckCriteria(
        budget_usd=50.0,
        strict_budget=True,
        min_rarity="rare",
        mechanic_focus={
            "energy": "focused",
            "rad": "focused",
            "oil": "engine",
        },
    )
    ids = _rule_ids(criteria)
    assert "TOO_MANY_FOCUSED_PROFILES" in ids
    assert "OVER_CONSTRAINED_BUDGET" in ids


def test_lint_artifacts_avoid_equip() -> None:
    criteria = DeckCriteria(include_mechanics=["equip"], avoid_mechanics=["equip"])
    ids = _rule_ids(criteria)
    assert "INCLUDE_AVOID_OVERLAP" in ids
