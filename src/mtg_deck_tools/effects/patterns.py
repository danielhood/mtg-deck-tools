"""Load effect-patterns.yaml."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class PatternMatcher:
    type: str
    pattern: str | None = None
    compiled: re.Pattern[str] | None = None


@dataclass(frozen=True)
class EffectPattern:
    id: str
    effect_kind: str
    confidence: float
    matchers: tuple[PatternMatcher, ...]
    payload: dict[str, Any]
    capture: dict[str, int] = field(default_factory=dict)
    exclude_if_matched: tuple[str, ...] = ()


@dataclass(frozen=True)
class EffectPatternRegistry:
    schema_version: int
    extraction_version: int
    patterns: tuple[EffectPattern, ...]


def load_effect_patterns(path: Path) -> EffectPatternRegistry:
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    patterns: list[EffectPattern] = []
    for entry in data.get("patterns", []):
        matchers: list[PatternMatcher] = []
        for m in entry.get("matchers", []):
            mtype = m["type"]
            pattern = m.get("pattern")
            compiled = None
            if pattern and mtype in ("oracle_regex", "type_regex"):
                compiled = re.compile(pattern)
            matchers.append(
                PatternMatcher(type=mtype, pattern=pattern, compiled=compiled)
            )
        patterns.append(
            EffectPattern(
                id=entry["id"],
                effect_kind=entry["effect_kind"],
                confidence=float(entry.get("confidence", 1.0)),
                matchers=tuple(matchers),
                payload=dict(entry.get("payload") or {}),
                capture=dict(entry.get("capture") or {}),
                exclude_if_matched=tuple(entry.get("exclude_if_matched") or []),
            )
        )
    return EffectPatternRegistry(
        schema_version=int(data.get("schema_version", 1)),
        extraction_version=int(data.get("extraction_version", 1)),
        patterns=tuple(patterns),
    )
