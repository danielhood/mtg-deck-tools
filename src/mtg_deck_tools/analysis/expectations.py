"""Compare scenario expectations to analysis case results."""

from __future__ import annotations

from dataclasses import dataclass, field

from mtg_deck_tools.analysis.matrix import AnalysisScenario, DependencyExpect, ValidationExpect
from mtg_deck_tools.analysis.rubric import WarningVerdict, classify_dependency_warning
from mtg_deck_tools.builder.generate_outcome import GenerateOutcome


@dataclass
class ExpectationFailure:
    field: str
    message: str


@dataclass
class CaseExpectResult:
    passed: bool
    failures: list[ExpectationFailure] = field(default_factory=list)


def _check_validation(
    expect: ValidationExpect,
    outcome: GenerateOutcome,
    failures: list[ExpectationFailure],
) -> None:
    if expect.passed is not None and outcome.validation.passed != expect.passed:
        failures.append(
            ExpectationFailure(
                field="validation.passed",
                message=(
                    f"expected validation.passed={expect.passed}, "
                    f"got {outcome.validation.passed}"
                ),
            )
        )
    if expect.max_errors is not None:
        count = len(outcome.validation.errors)
        if count > expect.max_errors:
            failures.append(
                ExpectationFailure(
                    field="validation.max_errors",
                    message=f"expected <= {expect.max_errors} errors, got {count}",
                )
            )
    if expect.max_warnings is not None:
        count = len(outcome.validation.warnings)
        if count > expect.max_warnings:
            failures.append(
                ExpectationFailure(
                    field="validation.max_warnings",
                    message=f"expected <= {expect.max_warnings} warnings, got {count}",
                )
            )


def _warned_rule_ids(outcome: GenerateOutcome) -> set[str]:
    return {
        i.rule_id
        for i in outcome.dependency_report.issues
        if i.status in ("warn", "fail")
    }


def _check_dependency(
    expect: DependencyExpect,
    outcome: GenerateOutcome,
    verdicts: dict[str, WarningVerdict],
    failures: list[ExpectationFailure],
) -> None:
    warned = _warned_rule_ids(outcome)
    warn_count = len(outcome.dependency_report.warnings)

    if expect.max_warnings is not None and warn_count > expect.max_warnings:
        failures.append(
            ExpectationFailure(
                field="dependency.max_warnings",
                message=f"expected <= {expect.max_warnings} dependency warnings, got {warn_count}",
            )
        )

    for rule_id in expect.rules_must_warn:
        if rule_id not in warned:
            failures.append(
                ExpectationFailure(
                    field="dependency.rules_must_warn",
                    message=f"expected warning for rule {rule_id!r}, not present",
                )
            )

    for rule_id in expect.rules_must_not_warn:
        if rule_id in warned:
            failures.append(
                ExpectationFailure(
                    field="dependency.rules_must_not_warn",
                    message=f"expected no warning for rule {rule_id!r}, but it fired",
                )
            )

    inappropriate = sum(1 for v in verdicts.values() if v == "inappropriate")
    if expect.max_inappropriate_warnings is not None:
        if inappropriate > expect.max_inappropriate_warnings:
            failures.append(
                ExpectationFailure(
                    field="dependency.max_inappropriate_warnings",
                    message=(
                        f"expected <= {expect.max_inappropriate_warnings} inappropriate "
                        f"warnings, got {inappropriate}"
                    ),
                )
            )


def evaluate_expectations(
    scenario: AnalysisScenario,
    outcome: GenerateOutcome,
    verdicts: dict[str, WarningVerdict],
) -> CaseExpectResult:
    failures: list[ExpectationFailure] = []
    _check_validation(scenario.expect.validation, outcome, failures)
    _check_dependency(scenario.expect.dependency, outcome, verdicts, failures)
    return CaseExpectResult(passed=not failures, failures=failures)


def verdicts_for_outcome(outcome: GenerateOutcome) -> dict[str, WarningVerdict]:
    """Map rule_id → verdict (last issue wins per rule for summary)."""
    result: dict[str, WarningVerdict] = {}
    for issue in outcome.dependency_report.issues:
        if issue.status not in ("warn", "fail"):
            continue
        result[issue.rule_id] = classify_dependency_warning(issue, outcome.criteria)
    return result
