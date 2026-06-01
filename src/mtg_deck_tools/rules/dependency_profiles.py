"""Profile threshold helpers (no builder imports)."""

from __future__ import annotations

from typing import Any

from mtg_deck_tools.rules.dependencies import load_profile_defaults


def _profile_defaults(
    profile_id: str,
    profiles: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return (profiles or load_profile_defaults()).get(profile_id, {})


def energy_profile_floors(
    profiles: dict[str, dict[str, Any]] | None = None,
) -> tuple[int, int]:
    cfg = _profile_defaults("energy", profiles)
    return (
        int(cfg.get("producer_min", 2)),
        int(cfg.get("consumer_min", 2)),
    )


def aura_spell_min(profiles: dict[str, dict[str, Any]] | None = None) -> int:
    return int(_profile_defaults("aura_support", profiles).get("aura_spell_min", 6))


def artifact_spell_min(profiles: dict[str, dict[str, Any]] | None = None) -> int:
    return int(_profile_defaults("artifacts", profiles).get("artifact_min", 8))


def elf_creature_min(profiles: dict[str, dict[str, Any]] | None = None) -> int:
    return int(_profile_defaults("elves", profiles).get("payoff_creature_min", 5))


def elf_subtype(profiles: dict[str, dict[str, Any]] | None = None) -> str:
    return str(_profile_defaults("elves", profiles).get("subtype", "Elf"))
