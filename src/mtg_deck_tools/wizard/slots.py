"""Slot template loading and validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from mtg_deck_tools.paths import SLOT_TEMPLATES_PATH

COMMANDER_DECK_SIZE = 99

# Theme-layer tags used for slot filling, not archetype selection in the wizard.
SLOT_FILLER_THEME_TAGS = frozenset({"ramp", "draw", "removal", "board_wipe"})


@dataclass(frozen=True)
class SlotBounds:
    min: int
    max: int


@dataclass(frozen=True)
class SlotTemplateConfig:
    default: dict[str, int]
    bounds: dict[str, SlotBounds]
    order: tuple[str, ...]
    labels: dict[str, str]


def load_slot_template_config(path: Path | None = None) -> SlotTemplateConfig:
    config_path = path or SLOT_TEMPLATES_PATH
    with config_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)

    default = {k: int(v) for k, v in data["default"].items()}
    bounds = {
        slot: SlotBounds(min=int(spec["min"]), max=int(spec["max"]))
        for slot, spec in data["bounds"].items()
    }
    order = tuple(data.get("order", list(default.keys())))
    labels = {k: str(v) for k, v in data.get("labels", {}).items()}
    return SlotTemplateConfig(default=default, bounds=bounds, order=order, labels=labels)


def slot_template_total(slots: dict[str, int]) -> int:
    return sum(slots.values())


def validate_slot_template(
    slots: dict[str, int],
    config: SlotTemplateConfig | None = None,
) -> list[str]:
    """Return human-readable validation errors (empty if valid)."""
    cfg = config or load_slot_template_config()
    errors: list[str] = []

    unknown = set(slots) - set(cfg.default)
    if unknown:
        errors.append(f"Unknown slots: {', '.join(sorted(unknown))}")

    missing = set(cfg.default) - set(slots)
    if missing:
        errors.append(f"Missing slots: {', '.join(sorted(missing))}")

    for slot, count in slots.items():
        if slot not in cfg.bounds:
            continue
        bounds = cfg.bounds[slot]
        if count < bounds.min or count > bounds.max:
            label = cfg.labels.get(slot, slot)
            errors.append(f"{label}: {count} (allowed {bounds.min}–{bounds.max})")

    total = slot_template_total(slots)
    if total != COMMANDER_DECK_SIZE:
        errors.append(f"Slot total is {total}; must be {COMMANDER_DECK_SIZE}")

    return errors


def suggest_lands_count(slots: dict[str, int], *, exclude_lands: bool = True) -> int:
    """Remaining cards for the lands slot so the deck sums to 99."""
    if exclude_lands:
        non_land = sum(v for k, v in slots.items() if k != "lands")
    else:
        non_land = slot_template_total(slots)
    return COMMANDER_DECK_SIZE - non_land


def clamp_slot_count(slot: str, count: int, config: SlotTemplateConfig) -> int:
    bounds = config.bounds[slot]
    return max(bounds.min, min(bounds.max, count))
