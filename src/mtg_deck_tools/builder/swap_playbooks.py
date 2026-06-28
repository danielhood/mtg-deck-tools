"""Load UX12 swap resolution playbooks from YAML."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import yaml

from mtg_deck_tools.models.swap_constraints import SwapConstraints
from mtg_deck_tools.paths import CONFIG_DIR

SWAP_PLAYBOOKS_PATH = CONFIG_DIR / "swap-playbooks.yaml"


@lru_cache(maxsize=1)
def load_swap_playbooks() -> dict[str, Any]:
    with SWAP_PLAYBOOKS_PATH.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def strategies_for_rule(rule_id: str, *, deficit: str | None = None) -> list[dict[str, Any]]:
    """Return strategy dicts for a dependency rule, optionally filtered by deficit."""
    rules = load_swap_playbooks().get("rules") or {}
    entry = rules.get(rule_id) or {}
    strategies = list(entry.get("strategies") or [])
    if deficit is None:
        return strategies
    filtered: list[dict[str, Any]] = []
    for strategy in strategies:
        when = strategy.get("when_deficit")
        if when is None or deficit in when:
            filtered.append(strategy)
    if filtered:
        return filtered
    return strategies


def default_strategy_for_rule(rule_id: str, *, deficit: str | None = None) -> dict[str, Any] | None:
    strategies = strategies_for_rule(rule_id, deficit=deficit)
    if not strategies:
        return None
    for strategy in strategies:
        if strategy.get("id") != "quick_shuffle":
            return strategy
    return strategies[0]


def constraints_for_strategy(strategy_id: str, *, rule_id: str | None = None) -> SwapConstraints | None:
    rules = load_swap_playbooks().get("rules") or {}
    search_rules = [rule_id] if rule_id else list(rules.keys())
    for rid in search_rules:
        if rid is None:
            continue
        for strategy in rules.get(rid, {}).get("strategies") or []:
            if strategy.get("id") != strategy_id:
                continue
            raw = strategy.get("constraints") or {}
            return SwapConstraints.model_validate(raw)
    return None
