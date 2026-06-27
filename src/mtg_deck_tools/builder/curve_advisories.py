"""Post-build curve advisory rules (UX10c)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

from mtg_deck_tools.paths import CURVE_ADVISORIES_PATH

RULE_CURVE_MISSING_EARLY = "CURVE_MISSING_EARLY"
RULE_CURVE_TOP_HEAVY = "CURVE_TOP_HEAVY"


@dataclass(frozen=True)
class CurveAdvisory:
    rule: str
    status: str
    message: str
    actual_share: float
    threshold: float
    histogram: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_curve_advisory_config(path: Path | None = None) -> dict[str, Any]:
    with (path or CURVE_ADVISORIES_PATH).open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return {
        "defaults": dict(data.get("defaults") or {}),
        "theme_overrides": dict(data.get("theme_overrides") or {}),
    }


def _histogram_for_rule(
    metrics: dict[str, Any],
    rule_cfg: dict[str, Any],
    default_histogram: str,
) -> dict[str, int]:
    key = rule_cfg.get("histogram") or default_histogram
    if key == "creatures":
        return dict(metrics.get("creature_cmc_histogram") or {})
    return dict(metrics.get("cmc_histogram") or {})


def _bucket_share(histogram: dict[str, int], buckets: list[str]) -> float | None:
    total = sum(histogram.values())
    if total <= 0:
        return None
    selected = sum(histogram.get(bucket, 0) for bucket in buckets)
    return selected / total


def _resolve_rule_cfg(
    rule_id: str,
    *,
    defaults: dict[str, Any],
    theme_overrides: dict[str, Any],
    themes: list[str],
) -> dict[str, Any]:
    base_histogram = defaults.get("histogram") or "nonlands"
    rules = defaults.get("rules") or {}
    merged = dict(rules.get(rule_id) or {})
    if not merged:
        return {}

    min_shares: list[float] = []
    max_shares: list[float] = []
    for theme in themes:
        theme_rules = theme_overrides.get(theme) or {}
        override = theme_rules.get(rule_id)
        if not isinstance(override, dict):
            continue
        if "min_share" in override:
            min_shares.append(float(override["min_share"]))
        if "max_share" in override:
            max_shares.append(float(override["max_share"]))

    if min_shares:
        merged["min_share"] = min(min_shares)
    if max_shares:
        merged["max_share"] = max(max_shares)
    merged.setdefault("histogram", base_histogram)
    return merged


def evaluate_curve_advisories(
    metrics: dict[str, Any],
    *,
    themes: list[str] | None = None,
    config: dict[str, Any] | None = None,
) -> list[CurveAdvisory]:
    """Evaluate warn-only curve advisories from UX10a histogram metrics."""
    cfg = config or load_curve_advisory_config()
    defaults = cfg.get("defaults") or {}
    theme_overrides = cfg.get("theme_overrides") or {}
    theme_list = themes or []
    default_histogram = defaults.get("histogram") or "nonlands"
    rules = defaults.get("rules") or {}

    advisories: list[CurveAdvisory] = []
    for rule_id in rules:
        rule_cfg = _resolve_rule_cfg(
            rule_id,
            defaults=defaults,
            theme_overrides=theme_overrides,
            themes=theme_list,
        )
        if not rule_cfg:
            continue

        histogram = _histogram_for_rule(metrics, rule_cfg, default_histogram)
        buckets = list(rule_cfg.get("buckets") or [])
        share = _bucket_share(histogram, buckets)
        if share is None:
            continue

        message = str(rule_cfg.get("message") or rule_id)
        histogram_key = str(rule_cfg.get("histogram") or default_histogram)

        min_share = rule_cfg.get("min_share")
        if min_share is not None and share < float(min_share):
            advisories.append(
                CurveAdvisory(
                    rule=rule_id,
                    status="warn",
                    message=message,
                    actual_share=round(share, 4),
                    threshold=float(min_share),
                    histogram=histogram_key,
                )
            )
            continue

        max_share = rule_cfg.get("max_share")
        if max_share is not None and share > float(max_share):
            advisories.append(
                CurveAdvisory(
                    rule=rule_id,
                    status="warn",
                    message=message,
                    actual_share=round(share, 4),
                    threshold=float(max_share),
                    histogram=histogram_key,
                )
            )

    return advisories


def curve_advisory_blurb(advisories: list[CurveAdvisory], *, histogram: str = "nonlands") -> str:
    """Human-readable curve summary for markdown / web blurb."""
    matching = [item for item in advisories if item.histogram == histogram]
    if matching:
        return " ".join(item.message for item in matching)
    return "Mana curve is spread across several CMC bands."
