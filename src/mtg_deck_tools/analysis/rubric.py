"""Heuristic classification of dependency warnings for automated dogfood scoring."""

from __future__ import annotations

from typing import Literal

from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.rules.dependencies import DependencyIssue
from mtg_deck_tools.rules.dependency_scope import build_dependency_scope
from mtg_deck_tools.rules.resource_counters import spec_for_rule

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
        # Fires only for voltron theme or card-driven aura tutors / Aura cast payoffs.
        return "appropriate"

    if rule_id == "ENCHANTMENT_SUPPORT_MIN":
        if scope.enchantments_user_intent:
            return "appropriate"
        return "appropriate"

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

    if rule_id == "TOKEN_BALANCE":
        if scope.tokens_user_intent:
            return "appropriate"
        producers = detail.get("producers") or []
        payoffs = detail.get("payoffs") or []
        if max(len(producers), len(payoffs)) >= 2:
            return "appropriate"
        return "inappropriate"

    if rule_id == "VEHICLE_BALANCE":
        if scope.vehicles_user_intent:
            return "appropriate"
        vehicles = detail.get("vehicles")
        if vehicles is not None and vehicles >= 2:
            return "appropriate"
        return "inappropriate"

    resource_spec = spec_for_rule(rule_id)
    if resource_spec is not None:
        if scope.resource_user_intent(resource_spec.profile_id):
            return "appropriate"
        producers = detail.get("producers") or []
        consumers = detail.get("consumers") or []
        if max(len(producers), len(consumers)) >= 2:
            return "appropriate"
        return "inappropriate"

    if rule_id == "TUTOR_TARGET_EXISTS":
        return "appropriate"

    if rule_id == "TYPE_SYNERGY_MIN":
        return "appropriate"

    if rule_id in (
        "REANIMATION_SUPPORT",
        "GRAVEYARD_COST_SUPPORT",
        "SELF_MILL_BALANCE",
        "LANDFALL_BALANCE",
    ):
        if rule_id == "LANDFALL_BALANCE" and scope.landfall_user_intent:
            return "appropriate"
        if rule_id in (
            "REANIMATION_SUPPORT",
            "GRAVEYARD_COST_SUPPORT",
            "SELF_MILL_BALANCE",
        ) and scope.graveyard_user_intent:
            return "appropriate"
        detail = issue.detail or {}
        if rule_id == "REANIMATION_SUPPORT":
            return "appropriate"
        if rule_id == "GRAVEYARD_COST_SUPPORT":
            cards = detail.get("graveyard_cost") or []
            return "appropriate" if len(cards) >= 2 else "inappropriate"
        if rule_id == "SELF_MILL_BALANCE":
            mill = detail.get("mill_enabler") or []
            payoffs = detail.get("graveyard_payoff") or []
            return "appropriate" if max(len(mill), len(payoffs)) >= 2 else "inappropriate"
        if rule_id == "LANDFALL_BALANCE":
            payoffs = detail.get("landfall_payoff") or []
            return "appropriate" if len(payoffs) >= 2 else "inappropriate"

    return "review"
