"""Profile threshold helpers (no builder imports)."""

from __future__ import annotations

from typing import Any

from mtg_deck_tools.rules.dependencies import load_profile_defaults


def energy_profile_floors(
    profiles: dict[str, dict[str, Any]] | None = None,
) -> tuple[int, int]:
    cfg = (profiles or load_profile_defaults()).get("energy", {})
    return (
        int(cfg.get("producer_min", 2)),
        int(cfg.get("consumer_min", 2)),
    )
