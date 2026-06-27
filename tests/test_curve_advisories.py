"""UX10c curve advisory rules."""

from __future__ import annotations

from mtg_deck_tools.builder.curve_advisories import (
    RULE_CURVE_MISSING_EARLY,
    RULE_CURVE_TOP_HEAVY,
    evaluate_curve_advisories,
    load_curve_advisory_config,
)


def test_evaluate_curve_missing_early_default() -> None:
    metrics = {
        "cmc_histogram": {
            "0": 0,
            "1": 0,
            "2": 1,
            "3": 8,
            "4": 10,
            "5": 12,
            "6": 8,
            "7": 4,
            "7+": 2,
        },
        "creature_cmc_histogram": {},
    }
    advisories = evaluate_curve_advisories(metrics)
    rules = {item.rule for item in advisories}
    assert RULE_CURVE_MISSING_EARLY in rules
    assert RULE_CURVE_TOP_HEAVY in rules


def test_evaluate_balanced_curve_has_no_advisories() -> None:
    metrics = {
        "cmc_histogram": {
            "0": 0,
            "1": 4,
            "2": 8,
            "3": 10,
            "4": 8,
            "5": 6,
            "6": 2,
            "7": 0,
            "7+": 0,
        },
        "creature_cmc_histogram": {},
    }
    assert evaluate_curve_advisories(metrics) == []


def test_theme_override_ramp_lenient_on_early_game() -> None:
    metrics = {
        "cmc_histogram": {
            "0": 0,
            "1": 2,
            "2": 2,
            "3": 10,
            "4": 10,
            "5": 8,
            "6": 4,
            "7": 2,
            "7+": 0,
        },
        "creature_cmc_histogram": {},
    }
    default = evaluate_curve_advisories(metrics)
    ramp = evaluate_curve_advisories(metrics, themes=["ramp"])
    assert any(item.rule == RULE_CURVE_MISSING_EARLY for item in default)
    assert not any(item.rule == RULE_CURVE_MISSING_EARLY for item in ramp)


def test_theme_override_tokens_strict_on_early_game() -> None:
    metrics = {
        "cmc_histogram": {
            "0": 0,
            "1": 4,
            "2": 4,
            "3": 8,
            "4": 8,
            "5": 6,
            "6": 2,
            "7": 0,
            "7+": 0,
        },
        "creature_cmc_histogram": {},
    }
    # Early share 8/32 = 0.25 — passes default (0.15) and tokens (0.18)
    assert not any(
        item.rule == RULE_CURVE_MISSING_EARLY
        for item in evaluate_curve_advisories(metrics)
    )

    strict_metrics = {
        "cmc_histogram": {
            "0": 0,
            "1": 2,
            "2": 3,
            "3": 10,
            "4": 10,
            "5": 8,
            "6": 2,
            "7": 0,
            "7+": 0,
        },
        "creature_cmc_histogram": {},
    }
    # Early share 5/35 ≈ 0.143 — fails default; tokens stricter at 0.18 also fails
    assert any(
        item.rule == RULE_CURVE_MISSING_EARLY
        for item in evaluate_curve_advisories(strict_metrics)
    )
    assert any(
        item.rule == RULE_CURVE_MISSING_EARLY
        for item in evaluate_curve_advisories(strict_metrics, themes=["tokens"])
    )

    borderline_metrics = {
        "cmc_histogram": {
            "0": 0,
            "1": 3,
            "2": 3,
            "3": 10,
            "4": 10,
            "5": 8,
            "6": 2,
            "7": 0,
            "7+": 0,
        },
        "creature_cmc_histogram": {},
    }
    # Early share 6/36 ≈ 0.167 — passes default (0.15), fails tokens (0.18)
    assert not any(
        item.rule == RULE_CURVE_MISSING_EARLY
        for item in evaluate_curve_advisories(borderline_metrics)
    )
    assert any(
        item.rule == RULE_CURVE_MISSING_EARLY
        for item in evaluate_curve_advisories(borderline_metrics, themes=["tokens"])
    )


def test_load_curve_advisory_config_has_defaults() -> None:
    cfg = load_curve_advisory_config()
    rules = cfg["defaults"]["rules"]
    assert RULE_CURVE_MISSING_EARLY in rules
    assert RULE_CURVE_TOP_HEAVY in rules
