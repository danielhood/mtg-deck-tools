"""Load analysis / dogfood scenario matrices from YAML."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.paths import DOGFOOD_MATRIX_PATH

DEFAULT_MATRIX_PATH = DOGFOOD_MATRIX_PATH


@dataclass(frozen=True)
class DependencyExpect:
    max_warnings: int | None = None
    rules_must_warn: list[str] = field(default_factory=list)
    rules_must_not_warn: list[str] = field(default_factory=list)
    max_inappropriate_warnings: int | None = None


@dataclass(frozen=True)
class ValidationExpect:
    passed: bool | None = None
    max_errors: int | None = None
    max_warnings: int | None = None


@dataclass(frozen=True)
class ScenarioExpect:
    validation: ValidationExpect = field(default_factory=ValidationExpect)
    dependency: DependencyExpect = field(default_factory=DependencyExpect)


@dataclass(frozen=True)
class AnalysisScenario:
    id: str
    label: str
    criteria: DeckCriteria
    seed: int | None
    commander_names: list[str] = field(default_factory=list)
    expect: ScenarioExpect = field(default_factory=ScenarioExpect)
    strict_budget: bool = False
    strict_dependencies: bool = False
    repair_dependencies: bool = False
    prefer_available: bool = False


@dataclass(frozen=True)
class AnalysisMatrix:
    schema_version: int
    defaults: dict[str, Any]
    scenarios: list[AnalysisScenario]


def _parse_expect(raw: dict[str, Any] | None) -> ScenarioExpect:
    raw = raw or {}
    val_raw = raw.get("validation") or {}
    dep_raw = raw.get("dependency") or {}
    return ScenarioExpect(
        validation=ValidationExpect(
            passed=val_raw.get("passed"),
            max_errors=val_raw.get("max_errors"),
            max_warnings=val_raw.get("max_warnings"),
        ),
        dependency=DependencyExpect(
            max_warnings=dep_raw.get("max_warnings"),
            rules_must_warn=list(dep_raw.get("rules_must_warn") or []),
            rules_must_not_warn=list(dep_raw.get("rules_must_not_warn") or []),
            max_inappropriate_warnings=dep_raw.get("max_inappropriate_warnings"),
        ),
    )


def load_analysis_matrix(path: Path | None = None) -> AnalysisMatrix:
    matrix_path = path or DEFAULT_MATRIX_PATH
    with matrix_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    defaults = dict(data.get("defaults") or {})
    default_seed = defaults.get("seed")
    scenarios: list[AnalysisScenario] = []

    for entry in data.get("scenarios") or []:
        if not isinstance(entry, dict):
            continue
        scenario_id = str(entry["id"])
        label = str(entry.get("label") or scenario_id)
        crit_raw = dict(entry.get("criteria") or {})
        seed = entry.get("seed", default_seed)
        commander_names = list(entry.get("commander_names") or [])

        criteria = DeckCriteria.model_validate(crit_raw)
        if seed is not None:
            criteria = criteria.model_copy(update={"seed": int(seed)})

        scenarios.append(
            AnalysisScenario(
                id=scenario_id,
                label=label,
                criteria=criteria,
                seed=int(seed) if seed is not None else None,
                commander_names=commander_names,
                expect=_parse_expect(entry.get("expect")),
                strict_budget=bool(entry.get("strict_budget", False)),
                strict_dependencies=bool(entry.get("strict_dependencies", False)),
                repair_dependencies=bool(entry.get("repair_dependencies", False)),
                prefer_available=bool(entry.get("prefer_available", False)),
            )
        )

    return AnalysisMatrix(
        schema_version=int(data.get("schema_version") or 1),
        defaults=defaults,
        scenarios=scenarios,
    )
