"""Heuristic classification of dependency warnings for automated dogfood scoring."""

from __future__ import annotations

from typing import Literal

from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.rules.dependencies import DependencyIssue
from mtg_deck_tools.rules.dependency_scope import build_dependency_scope

WarningVerdict = Literal["appropriate", "inappropriate", "review"]


def classify_dependency_warning(
    issue: DependencyIssue,
    criteria: DeckCriteria,
) -> WarningVerdict:
    """
    Estimate whether a dependency warning matches user intent.

    Card-driven rules default to appropriate when they fire. Deck-level rules use
    ``dependency_scope`` and issue detail to flag likely calibration noise.
    """
    if issue.status not in ("warn", "fail"):
        return "appropriate"

    scope = build_dependency_scope(criteria)
    rule_id = issue.rule_id
    detail = issue.detail or {}

    if rule_id == "AURA_SUPPORT_MIN":
        if scope.aura_support_min:
            return "appropriate"
        return "inappropriate"

    if rule_id == "ENERGY_BALANCE":
        if scope.energy_user_intent:
            return "appropriate"
        producers = detail.get("producers") or []
        consumers = detail.get("consumers") or []
        if max(len(producers), len(consumers)) >= 2:
            return "appropriate"
        return "inappropriate"

    if rule_id == "SACRIFICE_BALANCE":
        if scope.sacrifice_user_intent:
            return "appropriate"
        outlets = detail.get("outlets") or []
        payoffs = detail.get("payoffs") or []
        if max(len(outlets), len(payoffs)) >= 2:
            return "appropriate"
        return "inappropriate"

    if rule_id == "TUTOR_TARGET_EXISTS":
        return "appropriate"

    if rule_id == "TYPE_SYNERGY_MIN":
        return "appropriate"

    return "review"
