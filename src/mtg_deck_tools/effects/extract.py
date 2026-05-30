"""Extract effect atoms from card fields using effect-patterns.yaml."""

from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any

from mtg_deck_tools.effects.patterns import EffectPattern, EffectPatternRegistry, load_effect_patterns
from mtg_deck_tools.models.effects import EffectAtom
from mtg_deck_tools.paths import EFFECT_PATTERNS_PATH


def _matches(
    pattern: EffectPattern,
    *,
    oracle_text: str,
    type_line: str,
) -> re.Match[str] | None:
    for matcher in pattern.matchers:
        if matcher.type == "oracle_regex" and matcher.compiled:
            m = matcher.compiled.search(oracle_text)
            if m:
                return m
        if matcher.type == "type_regex" and matcher.compiled:
            m = matcher.compiled.search(type_line)
            if m:
                return m
    return None


def _singularize_subtype(plural: str) -> str:
    """Rough English plural to subtype label (v1; not exhaustive)."""
    if plural.endswith("ves") and len(plural) > 3:
        return plural[:-3] + "f"
    if plural.endswith("s") and not plural.endswith("ss") and len(plural) > 1:
        return plural[:-1]
    return plural


def _apply_captures(payload: dict[str, Any], capture_map: dict[str, int], match: re.Match[str]) -> None:
    for key, group_idx in capture_map.items():
        value = match.group(group_idx)
        if value is None:
            continue
        if key == "subtypes_plural":
            payload["subtypes"] = [_singularize_subtype(value)]
        elif key in ("types", "subtypes", "supertypes"):
            if key == "types":
                payload[key] = [value.lower()]
            elif key == "subtypes":
                payload[key] = [value]
            else:
                payload[key] = [value]
        elif key == "max_cmc":
            payload[key] = int(value)
        else:
            payload[key] = value


def _normalize_list_values(payload: dict[str, Any]) -> None:
    for key in ("types", "subtypes", "supertypes"):
        if key in payload and isinstance(payload[key], list):
            if key == "types":
                payload[key] = [v.lower() for v in payload[key]]
            elif key == "subtypes" and payload[key]:
                payload[key] = [payload[key][0][:1].upper() + payload[key][0][1:]]


class EffectExtractor:
    def __init__(self, registry: EffectPatternRegistry) -> None:
        self._registry = registry
        self._by_id = {p.id: p for p in registry.patterns}

    @classmethod
    def from_yaml(cls, path: Path | None = None) -> EffectExtractor:
        return cls(load_effect_patterns(path or EFFECT_PATTERNS_PATH))

    def extract(
        self,
        *,
        oracle_text: str = "",
        type_line: str = "",
        face_index: int = 0,
    ) -> list[EffectAtom]:
        matched_ids: set[str] = set()
        atoms: list[EffectAtom] = []

        for pattern in self._registry.patterns:
            if pattern.exclude_if_matched and matched_ids.intersection(pattern.exclude_if_matched):
                continue

            match = _matches(pattern, oracle_text=oracle_text, type_line=type_line)
            if not match:
                continue

            payload = copy.deepcopy(pattern.payload)
            if pattern.capture:
                _apply_captures(payload, pattern.capture, match)
            _normalize_list_values(payload)

            atoms.append(
                EffectAtom(
                    effect_kind=pattern.effect_kind,
                    payload=payload,
                    confidence=pattern.confidence,
                    source=pattern.id,
                    face_index=face_index,
                )
            )
            matched_ids.add(pattern.id)

        return atoms


def extract_card_effects(
    card: dict[str, Any],
    *,
    extractor: EffectExtractor | None = None,
) -> list[EffectAtom]:
    """
    Extract effects from a normalized card dict (import row shape).

    v1 face policy: single merged oracle_text / type_line; face_index 0 only.
    """
    ext = extractor or EffectExtractor.from_yaml()
    return ext.extract(
        oracle_text=card.get("oracle_text") or "",
        type_line=card.get("type_line") or "",
        face_index=0,
    )
