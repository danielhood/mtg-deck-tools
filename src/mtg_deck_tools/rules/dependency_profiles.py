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


def enchantment_spell_min(profiles: dict[str, dict[str, Any]] | None = None) -> int:
    return int(_profile_defaults("enchantments", profiles).get("enchantment_min", 8))


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


def token_profile_floors(
    profiles: dict[str, dict[str, Any]] | None = None,
) -> tuple[int, int]:
    cfg = _profile_defaults("tokens", profiles)
    return (
        int(cfg.get("producer_min", 5)),
        int(cfg.get("payoff_min", 3)),
    )


def vehicle_profile_floors(
    profiles: dict[str, dict[str, Any]] | None = None,
) -> tuple[int, int]:
    cfg = _profile_defaults("vehicles", profiles)
    return (
        int(cfg.get("vehicle_min", 3)),
        int(cfg.get("creature_min", 25)),
    )


def equipment_profile_floors(
    profiles: dict[str, dict[str, Any]] | None = None,
) -> tuple[int, int]:
    cfg = _profile_defaults("equipment", profiles)
    return (
        int(cfg.get("equipment_min", 4)),
        int(cfg.get("carrier_creature_min", 22)),
    )


def resource_counter_profile_floors(
    profile_id: str,
    profiles: dict[str, dict[str, Any]] | None = None,
) -> tuple[int, int]:
    from mtg_deck_tools.rules.resource_counters import resource_profile_floors

    return resource_profile_floors(profile_id, profiles)
