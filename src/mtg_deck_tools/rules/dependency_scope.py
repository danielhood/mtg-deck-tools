"""Which dependency profiles apply for a build (calibration / UX2 prep)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.paths import DEPENDENCY_PROFILES_PATH

_FOCUS_LEVELS = frozenset({"incidental", "supported", "focused", "engine"})


@dataclass(frozen=True)
class DependencyScope:
    """Gates deck-level profile rules; card-level rules stay always-on."""

    energy_balance: bool = True
    aura_support_min: bool = False
    energy_user_intent: bool = False


def _load_profile_activation(path: Path | None = None) -> dict[str, dict[str, list[str]]]:
    with (path or DEPENDENCY_PROFILES_PATH).open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    out: dict[str, dict[str, list[str]]] = {}
    for profile_id, entry in (data.get("profiles") or {}).items():
        if not isinstance(entry, dict):
            continue
        activation = entry.get("activation") or {}
        out[profile_id] = {
            "themes": list(activation.get("themes") or []),
            "include_mechanics": list(activation.get("include_mechanics") or []),
        }
    return out


def _focus_requests_profile(profile_id: str, focus: dict[str, str]) -> bool:
    level = (focus.get(profile_id) or "").strip().lower()
    return level in _FOCUS_LEVELS


def build_dependency_scope(
    criteria: DeckCriteria | None = None,
    *,
    activation: dict[str, dict[str, list[str]]] | None = None,
) -> DependencyScope:
    """
  Decide which deck-level dependency checks run.

  Card-triggered rules (tutors, lords, payoffs) are unaffected.
  """
    if criteria is None:
        return DependencyScope()

    cfg = activation or _load_profile_activation()
    themes = set(criteria.themes)
    includes = set(criteria.include_mechanics)
    focus = criteria.mechanic_focus or {}

    def _profile_active(profile_id: str) -> bool:
        if _focus_requests_profile(profile_id, focus):
            return True
        act = cfg.get(profile_id, {})
        if themes.intersection(act.get("themes") or []):
            return True
        if includes.intersection(act.get("include_mechanics") or []):
            return True
        return False

    energy_user = _profile_active("energy")
    return DependencyScope(
        energy_balance=True,
        aura_support_min=_profile_active("aura_support"),
        energy_user_intent=energy_user,
    )
