"""Wizard dependency UX: activated profiles and mechanic focus presets (UX2)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.rules.dependency_scope import _load_profile_activation

# Profiles with focus-level wizard prompts (planning/11 UX2 table).
UX2_PROFILE_IDS: tuple[str, ...] = (
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

FOCUS_LEVELS: tuple[str, ...] = ("incidental", "supported", "focused", "engine")

# Prompt labels from planning/11-dependency-engine-user-experience.md (UX2 table).
WIZARD_FOCUS_PROMPT_LABELS: dict[str, str] = {
    "energy": "Energy focus",
    "aura_support": "Aura support",
    "rad": "Rad counter focus",
    "oil": "Oil counter focus",
    "charge": "Charge counter focus",
    "experience": "Experience focus",
    "blood": "Blood counter focus",
    "plus_one": "+1/+1 counter focus",
    "vehicles": "Vehicle focus",
    "equipment": "Equipment focus",
    "tokens": "Token focus",
    "sacrifice": "Sacrifice package focus",
    "enchantments": "Enchantment focus",
    "graveyard": "Graveyard focus",
    "landfall": "Landfall focus",
}


@dataclass(frozen=True)
class ActivatedProfile:
    """A dependency profile activated by wizard theme/mechanic selections."""

    profile_id: str
    prompt_label: str


def _profile_activated_by_selection(
    profile_id: str,
    *,
    themes: set[str],
    includes: set[str],
    activation: dict[str, dict[str, list[str]]],
) -> bool:
    act = activation.get(profile_id, {})
    if themes.intersection(act.get("themes") or []):
        return True
    if includes.intersection(act.get("include_mechanics") or []):
        return True
    return False


def activated_profiles_for_wizard(
    criteria: DeckCriteria,
    *,
    activation: dict[str, dict[str, list[str]]] | None = None,
    profiles_path: Path | None = None,
) -> list[ActivatedProfile]:
    """
    Profiles the user activated in steps 1–2 that qualify for UX2 focus prompts.

    Does not consider ``mechanic_focus`` (that is what the synergy step sets).
    """
    cfg = activation or _load_profile_activation(profiles_path)
    themes = set(criteria.themes)
    includes = set(criteria.include_mechanics)
    out: list[ActivatedProfile] = []
    for profile_id in UX2_PROFILE_IDS:
        if not _profile_activated_by_selection(
            profile_id,
            themes=themes,
            includes=includes,
            activation=cfg,
        ):
            continue
        label = WIZARD_FOCUS_PROMPT_LABELS.get(profile_id, profile_id.replace("_", " ").title())
        out.append(ActivatedProfile(profile_id=profile_id, prompt_label=label))
    return out


def format_mechanic_focus_summary(focus: dict[str, str]) -> str:
    """Human-readable mechanic_focus for wizard summary."""
    if not focus:
        return "(default)"
    parts = []
    for profile_id in UX2_PROFILE_IDS:
        level = focus.get(profile_id)
        if level:
            label = WIZARD_FOCUS_PROMPT_LABELS.get(profile_id, profile_id)
            parts.append(f"{label}: {level}")
    for profile_id, level in sorted(focus.items()):
        if profile_id not in UX2_PROFILE_IDS:
            parts.append(f"{profile_id}: {level}")
    return "; ".join(parts) if parts else "(default)"
