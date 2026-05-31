"""Deck analysis suite (matrix, rubric, runner)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from mtg_deck_tools.analysis.expectations import evaluate_expectations, verdicts_for_outcome
from mtg_deck_tools.analysis.matrix import load_analysis_matrix
from mtg_deck_tools.analysis.rubric import classify_dependency_warning
from mtg_deck_tools.analysis.runner import run_analysis_suite
from mtg_deck_tools.builder.deck import DeckBuildResult
from mtg_deck_tools.builder.generate_outcome import GenerateOutcome
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.rules.dependencies import DependencyIssue, DependencyReport


def test_load_dogfood_matrix_has_scenarios() -> None:
    matrix = load_analysis_matrix()
    assert matrix.schema_version >= 1
    assert len(matrix.scenarios) >= 8
    assert all(s.commander_names for s in matrix.scenarios)


def test_classify_incidental_energy_inappropriate() -> None:
    criteria = DeckCriteria(themes=["tokens"])
    issue = DependencyIssue(
        rule_id="ENERGY_BALANCE",
        status="warn",
        message="test",
        profile_id="energy",
        detail={"producers": ["Hub"], "consumers": []},
    )
    assert classify_dependency_warning(issue, criteria) == "inappropriate"


def test_classify_energy_include_appropriate() -> None:
    criteria = DeckCriteria(include_mechanics=["energy"])
    issue = DependencyIssue(
        rule_id="ENERGY_BALANCE",
        status="warn",
        message="test",
        profile_id="energy",
        detail={"producers": ["Hub"], "consumers": []},
    )
    assert classify_dependency_warning(issue, criteria) == "appropriate"


def test_expect_rules_must_not_warn() -> None:
    from mtg_deck_tools.analysis.matrix import (
        AnalysisScenario,
        DependencyExpect,
        ScenarioExpect,
    )

    criteria = DeckCriteria(themes=["tokens"])
    report = DependencyReport(
        issues=[
            DependencyIssue(
                rule_id="AURA_SUPPORT_MIN",
                status="warn",
                message="noise",
                profile_id="aura_support",
            )
        ]
    )
    outcome = GenerateOutcome(
        criteria=criteria,
        commanders=[],
        identity=["G"],
        maindeck=DeckBuildResult(cards=[], warnings=[], budget_spent=0.0, unpriced_names=[]),
        validation=__import__(
            "mtg_deck_tools.rules.validate", fromlist=["ValidationResult"]
        ).ValidationResult(passed=True),
        dependency_report=report,
        seed=42,
    )
    scenario = AnalysisScenario(
        id="t",
        label="t",
        criteria=criteria,
        seed=42,
        expect=ScenarioExpect(
            dependency=DependencyExpect(rules_must_not_warn=["AURA_SUPPORT_MIN"])
        ),
    )
    verdicts = verdicts_for_outcome(outcome)
    result = evaluate_expectations(scenario, outcome, verdicts)
    assert not result.passed


def _fake_outcome(criteria: DeckCriteria) -> GenerateOutcome:
    from mtg_deck_tools.rules.validate import ValidationResult

    return GenerateOutcome(
        criteria=criteria,
        commanders=[{"oracle_id": "cmd-1", "name": "Test Commander", "type_line": ""}],
        identity=["G"],
        maindeck=DeckBuildResult(cards=[], warnings=[], budget_spent=0.0, unpriced_names=[]),
        validation=ValidationResult(passed=True),
        dependency_report=DependencyReport(),
        seed=42,
    )


@pytest.fixture
def mini_db_file(tmp_path: Path) -> Path:
    from mtg_deck_tools.db.schema import apply_schema

    path = tmp_path / "cards.db"
    conn = sqlite3.connect(path)
    apply_schema(conn)
    conn.commit()
    conn.close()
    return path


def test_run_mini_analysis_suite(tmp_path: Path, mini_db_file: Path, monkeypatch) -> None:
    matrix_path = Path(__file__).parent / "fixtures" / "analysis-matrix-mini.yaml"

    def fake_build(**kwargs):
        return _fake_outcome(kwargs["criteria"])

    monkeypatch.setattr(
        "mtg_deck_tools.analysis.runner.build_generate_outcome",
        fake_build,
    )
    result = run_analysis_suite(
        matrix_path=matrix_path,
        db_path=mini_db_file,
        output_dir=tmp_path / "out",
    )
    assert result.summary.scenario_count == 1
    assert result.summary.scenarios_errored == 0
    assert result.summary.scenarios_passed == 1
    assert (tmp_path / "out" / "summary.json").exists()
    assert (tmp_path / "out" / "cases" / "mini-tokens.json").exists()
    case = json.loads((tmp_path / "out" / "cases" / "mini-tokens.json").read_text())
    assert case.get("expect", {}).get("passed") is True
