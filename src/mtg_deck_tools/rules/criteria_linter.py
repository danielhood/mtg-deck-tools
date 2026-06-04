"""Lightweight criteria preflight checks (UX3) — no deck build required."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.paths import DEPENDENCY_PROFILES_PATH
from mtg_deck_tools.rules.dependency_scope import _load_profile_activation
from mtg_deck_tools.rules.rarity import RARITY_RANK

_FOCUS_LEVELS = frozenset({"incidental", "supported", "focused", "engine"})
_HIGH_FOCUS_LEVELS = frozenset({"focused", "engine"})

# Profiles with UX2 focus prompts (docs/specs/dependency-engine/user-experience.md UX2 table).
_UX2_PROFILE_IDS: tuple[str, ...] = (
    "energy",
    "aura_support",
    "rad",
    "oil",
    "charge",
    "experience",
    "blood",
    "plus_one",
    "vehicles",
    "equipment",
    "tokens",
    "sacrifice",
    "enchantments",
    "graveyard",
    "landfall",
)

# Profiles whose activation depends on include_mechanics tags (avoid blocks the profile).
PROFILE_AVOID_TAGS: dict[str, tuple[str, ...]] = {
    "energy": ("energy",),
    "rad": ("rad",),
    "oil": ("oil",),
    "charge": ("charge",),
    "experience": ("experience",),
    "blood": ("blood",),
    "plus_one": ("counters",),
    "vehicles": ("vehicles",),
    "equipment": ("equip",),
    "artifacts": ("equip", "vehicles"),
}

# Theme pairs that compete for synergy slot budget (docs/specs/dependency-engine/user-experience.md UX6 step 1).
_HEAVY_THEME_PAIRS: tuple[frozenset[str], str] = (
    (frozenset({"tokens", "aristocrats"}), "tokens and aristocrats both need large synergy packages"),
)


@dataclass(frozen=True)
class CriteriaWarning:
    """Single criteria preflight warning for wizard or CLI consumers."""

    rule_id: str
    message: str


def _load_profile_labels(path: Path | None = None) -> dict[str, str]:
    with (path or DEPENDENCY_PROFILES_PATH).open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    out: dict[str, str] = {}
    for profile_id, entry in (data.get("profiles") or {}).items():
        if isinstance(entry, dict):
            label = entry.get("label")
            if isinstance(label, str) and label.strip():
                out[profile_id] = label.strip()
    return out


def _profile_label(profile_id: str, labels: dict[str, str]) -> str:
    return labels.get(profile_id, profile_id.replace("_", " ").title())


def _include_avoid_overlap(include: list[str], avoid: list[str]) -> list[str]:
    overlap = sorted(set(include) & set(avoid))
    if overlap:
        return [f"Cannot both include and avoid: {', '.join(overlap)}"]
    return []


def _active_profile_ids(
    criteria: DeckCriteria,
    *,
    activation: dict[str, dict[str, list[str]]],
) -> set[str]:
    themes = set(criteria.themes)
    includes = set(criteria.include_mechanics)
    focus = criteria.mechanic_focus or {}
    active: set[str] = set()

    for profile_id in _UX2_PROFILE_IDS:
        level = (focus.get(profile_id) or "").strip().lower()
        if level in _FOCUS_LEVELS:
            active.add(profile_id)
            continue
        act = activation.get(profile_id, {})
        if themes.intersection(act.get("themes") or []):
            active.add(profile_id)
        elif includes.intersection(act.get("include_mechanics") or []):
            active.add(profile_id)

    return active


def _high_focus_profiles(focus: dict[str, str]) -> list[str]:
    return sorted(
        profile_id
        for profile_id, level in focus.items()
        if (level or "").strip().lower() in _HIGH_FOCUS_LEVELS
    )


def lint_criteria(
    criteria: DeckCriteria,
    *,
    profiles_path: Path | None = None,
) -> list[CriteriaWarning]:
    """
    Run warn-only criteria checks before generate.

    Returns an empty list when no issues are detected.
    """
    warnings: list[CriteriaWarning] = []
    activation = _load_profile_activation(profiles_path)
    labels = _load_profile_labels(profiles_path)
    avoids = set(criteria.avoid_mechanics)
    focus = criteria.mechanic_focus or {}
    themes = set(criteria.themes)

    for message in _include_avoid_overlap(
        criteria.include_mechanics,
        criteria.avoid_mechanics,
    ):
        warnings.append(CriteriaWarning(rule_id="INCLUDE_AVOID_OVERLAP", message=message))

    active_profiles = _active_profile_ids(criteria, activation=activation)
    for profile_id in sorted(active_profiles):
        blocked = sorted(set(PROFILE_AVOID_TAGS.get(profile_id, ())) & avoids)
        if not blocked:
            continue
        label = _profile_label(profile_id, labels)
        tags = ", ".join(blocked)
        warnings.append(
            CriteriaWarning(
                rule_id="AVOID_BLOCKS_PROFILE",
                message=(
                    f"Avoid {tags} conflicts with {label} — "
                    f"those cards will be excluded from the pool."
                ),
            )
        )

    for profile_id, level in sorted(focus.items()):
        if (level or "").strip().lower() not in _FOCUS_LEVELS:
            continue
        blocked = sorted(set(PROFILE_AVOID_TAGS.get(profile_id, ())) & avoids)
        if blocked:
            label = _profile_label(profile_id, labels)
            tags = ", ".join(blocked)
            warnings.append(
                CriteriaWarning(
                    rule_id="AVOID_FOCUS_CONFLICT",
                    message=(
                        f"Mechanic focus {label} ({level}) conflicts with avoid {tags} — "
                        f"dependency checks may not match the card pool."
                    ),
                )
            )

    if "voltron" in themes and "equip" in avoids:
        warnings.append(
            CriteriaWarning(
                rule_id="AVOID_THEME_CONFLICT",
                message=(
                    "Theme voltron expects equipment support, but avoid equip excludes "
                    "equip cards from the pool."
                ),
            )
        )

    for pair, detail in _HEAVY_THEME_PAIRS:
        if pair.issubset(themes):
            warnings.append(
                CriteriaWarning(
                    rule_id="THEMED_SHARE_STACK",
                    message=(
                        f"You selected {detail}; the deck may struggle to fit both packages."
                    ),
                )
            )

    high_focus = _high_focus_profiles(focus)
    if len(high_focus) > 2:
        focus_labels = ", ".join(_profile_label(pid, labels) for pid in high_focus)
        warnings.append(
            CriteriaWarning(
                rule_id="TOO_MANY_FOCUSED_PROFILES",
                message=(
                    f"{len(high_focus)} profiles at focused or engine ({focus_labels}) — "
                    "the deck may not have room for all plans."
                ),
            )
        )

    min_rank = RARITY_RANK.get(criteria.min_rarity, 1)
    if (
        criteria.strict_budget
        and criteria.budget_usd is not None
        and min_rank >= RARITY_RANK["rare"]
        and len(high_focus) >= 3
    ):
        warnings.append(
            CriteriaWarning(
                rule_id="OVER_CONSTRAINED_BUDGET",
                message=(
                    "Strict budget with rare-or-better minimum and three or more focused "
                    "profiles — the builder may fail to reach synergy floors."
                ),
            )
        )

    return _dedupe_warnings(warnings)


def _dedupe_warnings(warnings: list[CriteriaWarning]) -> list[CriteriaWarning]:
    seen: set[tuple[str, str]] = set()
    out: list[CriteriaWarning] = []
    for warning in warnings:
        key = (warning.rule_id, warning.message)
        if key in seen:
            continue
        seen.add(key)
        out.append(warning)
    return out
