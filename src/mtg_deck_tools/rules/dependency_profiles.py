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


def _subtype_lords_cfg(profiles: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    cfg = _profile_defaults("subtype_lords", profiles)
    if cfg:
        return cfg
    return _profile_defaults("elves", profiles)


def subtype_lord_minimum(
    subtype: str,
    profiles: dict[str, dict[str, Any]] | None = None,
) -> int:
    """Minimum other creatures of ``subtype`` when a lord for that subtype is in the deck."""
    cfg = _subtype_lords_cfg(profiles)
    default = int(cfg.get("payoff_creature_min", 5))
    mins = cfg.get("subtype_minimums") or {}
    if isinstance(mins, dict) and subtype in mins:
        return int(mins[subtype])
    return default


def elf_creature_min(profiles: dict[str, dict[str, Any]] | None = None) -> int:
    return subtype_lord_minimum("Elf", profiles)


def elf_subtype(profiles: dict[str, dict[str, Any]] | None = None) -> str:
    return "Elf"


def sacrifice_profile_floors(
    profiles: dict[str, dict[str, Any]] | None = None,
) -> tuple[int, int, int]:
    cfg = _profile_defaults("sacrifice", profiles)
    return (
        int(cfg.get("outlet_min", 2)),
        int(cfg.get("payoff_min", 3)),
        int(cfg.get("fodder_min", 8)),
    )
