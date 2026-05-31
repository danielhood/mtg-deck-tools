"""Aggregate analysis suite results into summary artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class SuiteSummary:
    matrix_path: str
    run_at: str
    scenario_count: int
    scenarios_passed: int
    scenarios_failed: int
    scenarios_errored: int
    validation_pass_count: int
    total_dependency_warnings: int
    inappropriate_warning_count: int
    review_warning_count: int
    false_positive_rate: float | None
    cases: list[dict[str, Any]] = field(default_factory=list)


def build_suite_summary(
    *,
    matrix_path: Path,
    cases: list[dict[str, Any]],
) -> SuiteSummary:
    def _expect_block(case: dict[str, Any]) -> dict[str, Any] | None:
        exp = case.get("expect")
        return exp if isinstance(exp, dict) else None

    passed = sum(1 for c in cases if _expect_block(c) and _expect_block(c).get("passed") is True)
    failed = sum(1 for c in cases if _expect_block(c) and _expect_block(c).get("passed") is False)
    errored = sum(1 for c in cases if c.get("error"))
    val_pass = sum(
        1 for c in cases if c.get("validation", {}).get("passed") and not c.get("error")
    )
    total_dep_warns = 0
    inappropriate = 0
    review = 0
    for c in cases:
        if c.get("error"):
            continue
        dep = c.get("dependency") or {}
        total_dep_warns += len(
            [i for i in (dep.get("issues") or []) if i.get("status") in ("warn", "fail")]
        )
        inappropriate += int(dep.get("inappropriate_warning_count") or 0)
        review += int(dep.get("review_warning_count") or 0)

    fp_rate: float | None = None
    if total_dep_warns > 0:
        fp_rate = inappropriate / total_dep_warns

    return SuiteSummary(
        matrix_path=str(matrix_path),
        run_at=datetime.now(timezone.utc).isoformat(),
        scenario_count=len(cases),
        scenarios_passed=passed,
        scenarios_failed=failed,
        scenarios_errored=errored,
        validation_pass_count=val_pass,
        total_dependency_warnings=total_dep_warns,
        inappropriate_warning_count=inappropriate,
        review_warning_count=review,
        false_positive_rate=fp_rate,
        cases=cases,
    )


def write_suite_reports(output_dir: Path, summary: SuiteSummary) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    cases_dir = output_dir / "cases"
    cases_dir.mkdir(exist_ok=True)

    for case in summary.cases:
        case_id = case.get("scenario_id") or "unknown"
        case_path = cases_dir / f"{case_id}.json"
        case_path.write_text(json.dumps(case, indent=2), encoding="utf-8")

    summary_dict = {
        "matrix_path": summary.matrix_path,
        "run_at": summary.run_at,
        "scenario_count": summary.scenario_count,
        "scenarios_passed": summary.scenarios_passed,
        "scenarios_failed": summary.scenarios_failed,
        "scenarios_errored": summary.scenarios_errored,
        "validation_pass_count": summary.validation_pass_count,
        "total_dependency_warnings": summary.total_dependency_warnings,
        "inappropriate_warning_count": summary.inappropriate_warning_count,
        "review_warning_count": summary.review_warning_count,
        "false_positive_rate": summary.false_positive_rate,
        "cases": [
            {
                "scenario_id": c.get("scenario_id"),
                "label": c.get("label"),
                "error": c.get("error"),
                "validation_passed": (c.get("validation") or {}).get("passed"),
                "expect_passed": (c.get("expect") or {}).get("passed"),
                "dependency_warning_count": len(
                    [
                        i
                        for i in (c.get("dependency") or {}).get("issues") or []
                        if i.get("status") in ("warn", "fail")
                    ]
                ),
                "inappropriate_warning_count": (c.get("dependency") or {}).get(
                    "inappropriate_warning_count"
                ),
            }
            for c in summary.cases
        ],
    }

    json_path = output_dir / "summary.json"
    json_path.write_text(json.dumps(summary_dict, indent=2), encoding="utf-8")
    md_path = output_dir / "summary.md"
    md_path.write_text(_render_summary_md(summary), encoding="utf-8")
    return json_path, md_path


def _render_summary_md(summary: SuiteSummary) -> str:
    lines = [
        "# Deck analysis run",
        "",
        f"- **Matrix:** `{summary.matrix_path}`",
        f"- **Run at:** {summary.run_at}",
        f"- **Scenarios:** {summary.scenario_count}",
        f"- **Expectations passed:** {summary.scenarios_passed}",
        f"- **Expectations failed:** {summary.scenarios_failed}",
        f"- **Errors:** {summary.scenarios_errored}",
        f"- **Validation passed:** {summary.validation_pass_count}",
        f"- **Dependency warnings:** {summary.total_dependency_warnings}",
        f"- **Inappropriate (heuristic):** {summary.inappropriate_warning_count}",
        f"- **Needs review:** {summary.review_warning_count}",
    ]
    if summary.false_positive_rate is not None:
        lines.append(
            f"- **False-positive rate:** {summary.false_positive_rate:.1%} "
            f"(target &lt; 5% per planning/13)"
        )
    lines.extend(["", "## Scenarios", ""])
    lines.append("| ID | Label | Validation | Expect | Dep warns | Inappropriate |")
    lines.append("| --- | --- | --- | --- | ---: | ---: |")
    for c in summary.cases:
        if c.get("error"):
            lines.append(
                f"| {c.get('scenario_id')} | {c.get('label')} | ERROR | — | — | — |"
            )
            continue
        val_ok = "PASS" if (c.get("validation") or {}).get("passed") else "FAIL"
        exp = c.get("expect")
        exp_ok = "—" if exp is None else ("PASS" if exp.get("passed") else "FAIL")
        dep = c.get("dependency") or {}
        warn_n = len(
            [i for i in dep.get("issues") or [] if i.get("status") in ("warn", "fail")]
        )
        inapp = dep.get("inappropriate_warning_count", 0)
        lines.append(
            f"| {c.get('scenario_id')} | {c.get('label')} | {val_ok} | {exp_ok} | "
            f"{warn_n} | {inapp} |"
        )
    lines.append("")
    return "\n".join(lines)
