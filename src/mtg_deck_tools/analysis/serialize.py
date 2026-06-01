"""JSON serialization for analysis case results."""

from __future__ import annotations

from typing import Any

from mtg_deck_tools.analysis.expectations import CaseExpectResult
from mtg_deck_tools.analysis.rubric import WarningVerdict
from mtg_deck_tools.builder.generate_outcome import GenerateOutcome
from mtg_deck_tools.rules.dependencies import dependency_report_to_dict


def case_result_to_dict(
    *,
    scenario_id: str,
    label: str,
    outcome: GenerateOutcome | None,
    verdicts: dict[str, WarningVerdict],
    expect_result: CaseExpectResult | None,
    error: str | None = None,
    criteria_dump: dict[str, Any] | None = None,
    seed: int | None = None,
) -> dict[str, Any]:
    if error is not None:
        return {
            "scenario_id": scenario_id,
            "label": label,
            "error": error,
            "criteria": criteria_dump,
            "seed": seed,
            "expect": None,
        }

    assert outcome is not None
    issues = []
    for issue in outcome.dependency_report.issues:
        issues.append(
            {
                "rule_id": issue.rule_id,
                "status": issue.status,
                "message": issue.message,
                "card_name": issue.card_name,
                "profile_id": issue.profile_id,
                "verdict": verdicts.get(issue.rule_id),
            }
        )

    inappropriate = sum(1 for v in verdicts.values() if v == "inappropriate")
    review = sum(1 for v in verdicts.values() if v == "review")

    payload: dict[str, Any] = {
        "scenario_id": scenario_id,
        "label": label,
        "error": error,
        "commander_names": outcome.commander_names,
        "criteria": outcome.criteria.model_dump(),
        "seed": outcome.seed,
        "validation": {
            "passed": outcome.validation.passed,
            "errors": [
                {"rule": e.rule, "message": e.message, "card_name": e.card_name}
                for e in outcome.validation.errors
            ],
            "warnings": [
                {"rule": w.rule, "message": w.message, "card_name": w.card_name}
                for w in outcome.validation.warnings
            ],
        },
        "dependency": {
            **dependency_report_to_dict(outcome.dependency_report),
            "issue_verdicts": verdicts,
            "inappropriate_warning_count": inappropriate,
            "review_warning_count": review,
            "issues_enriched": issues,
        },
        "deck_stats": {
            "maindeck_cards": len(outcome.maindeck.cards),
            "budget_spent": outcome.maindeck.budget_spent,
            "unpriced_count": len(outcome.maindeck.unpriced_names),
            "build_warnings": outcome.maindeck.warnings,
        },
        "output_json_path": str(outcome.output_json_path) if outcome.output_json_path else None,
        "output_md_path": str(outcome.output_md_path) if outcome.output_md_path else None,
    }

    if expect_result is not None:
        payload["expect"] = {
            "passed": expect_result.passed,
            "failures": [
                {"field": f.field, "message": f.message} for f in expect_result.failures
            ],
        }

    return payload
