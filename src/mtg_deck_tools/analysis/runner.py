"""Run analysis matrices (dogfood / regression suites)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from mtg_deck_tools.analysis.expectations import (
    evaluate_expectations,
    verdicts_for_outcome,
)
from mtg_deck_tools.analysis.matrix import load_analysis_matrix
from mtg_deck_tools.analysis.report import SuiteSummary, build_suite_summary, write_suite_reports
from mtg_deck_tools.analysis.serialize import case_result_to_dict
from mtg_deck_tools.builder.generate_outcome import build_generate_outcome
from mtg_deck_tools.builder.output import write_deck_outputs
from mtg_deck_tools.paths import DEFAULT_DB_PATH, OUTPUT_DIR


@dataclass
class AnalysisSuiteResult:
    output_dir: Path
    summary: SuiteSummary
    summary_json_path: Path
    summary_md_path: Path


def run_analysis_suite(
    *,
    matrix_path: Path | None = None,
    db_path: Path | None = None,
    output_dir: Path | None = None,
    write_decks: bool = False,
    progress: Callable[[str], None] | None = None,
) -> AnalysisSuiteResult:
    """
    Execute every scenario in the matrix and write summary + per-case JSON.

    Requires ``cards.db`` from import. Scenarios should pin ``commander_names`` for
    repeatable runs.
    """
    matrix = load_analysis_matrix(matrix_path)
    db = db_path or DEFAULT_DB_PATH
    if not db.exists():
        raise FileNotFoundError(f"Database not found at {db}. Run: mtg-deck-tools import")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    out_root = output_dir or (OUTPUT_DIR / f"analysis-{stamp}")
    out_root.mkdir(parents=True, exist_ok=True)

    cases: list[dict] = []

    for scenario in matrix.scenarios:
        if progress:
            progress(f"Running scenario: {scenario.id} — {scenario.label}")

        try:
            outcome = build_generate_outcome(
                db_path=db,
                criteria=scenario.criteria,
                seed=scenario.seed,
                commander_names=scenario.commander_names or None,
                strict_budget=scenario.strict_budget,
                strict_dependencies=scenario.strict_dependencies,
                repair_dependencies=scenario.repair_dependencies,
                prefer_available=scenario.prefer_available,
            )
            verdicts = verdicts_for_outcome(outcome)
            expect_result = evaluate_expectations(scenario, outcome, verdicts)

            if write_decks:
                case_dir = out_root / "decks"
                case_dir.mkdir(exist_ok=True)
                base = case_dir / scenario.id
                json_path, md_path = write_deck_outputs(
                    base_path=base,
                    criteria=outcome.criteria,
                    commanders=outcome.commanders,
                    maindeck=outcome.maindeck,
                    identity=outcome.identity,
                )
                outcome.output_json_path = json_path
                outcome.output_md_path = md_path

            case = case_result_to_dict(
                scenario_id=scenario.id,
                label=scenario.label,
                outcome=outcome,
                verdicts=verdicts,
                expect_result=expect_result,
            )
        except Exception as exc:
            case = case_result_to_dict(
                scenario_id=scenario.id,
                label=scenario.label,
                outcome=None,
                verdicts={},
                expect_result=None,
                error=str(exc),
                criteria_dump=scenario.criteria.model_dump(),
                seed=scenario.seed,
            )

        cases.append(case)

    from mtg_deck_tools.analysis.matrix import DEFAULT_MATRIX_PATH

    resolved_matrix = matrix_path or DEFAULT_MATRIX_PATH
    summary = build_suite_summary(matrix_path=resolved_matrix, cases=cases)
    json_path, md_path = write_suite_reports(out_root, summary)

    return AnalysisSuiteResult(
        output_dir=out_root,
        summary=summary,
        summary_json_path=json_path,
        summary_md_path=md_path,
    )
