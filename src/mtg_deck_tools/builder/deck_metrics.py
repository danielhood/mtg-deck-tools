"""Post-build deck composition metrics (UX10a)."""

from __future__ import annotations

from mtg_deck_tools.builder.deck import DeckCard
from mtg_deck_tools.builder.mana_base import ManaBasePlan

_CMC_BUCKETS = tuple(str(n) for n in range(8)) + ("7+",)
_TYPE_ORDER = (
    "Creature",
    "Instant",
    "Sorcery",
    "Artifact",
    "Enchantment",
    "Planeswalker",
    "Battle",
    "Land",
    "Other",
)


def _is_land(type_line: str) -> bool:
    return "Land" in (type_line or "")


def _is_creature(type_line: str) -> bool:
    line = type_line or ""
    return "Creature" in line and "Vehicle" not in line


def primary_card_type(type_line: str) -> str:
    """Last recognized primary type before the em dash, matching web deck-view."""
    before_dash = (type_line or "").split("—")[0].strip()
    parts = before_dash.split()
    for part in reversed(parts):
        if part in _TYPE_ORDER:
            return part
    return parts[-1] if parts else "Other"


def _cmc_bucket(cmc: float) -> str:
    if cmc >= 7:
        return "7+"
    return str(int(cmc))


def cmc_histogram(
    cards: list[DeckCard],
    *,
    creatures_only: bool = False,
    exclude_lands: bool = True,
) -> dict[str, int]:
    """Quantity-weighted CMC histogram with buckets 0–7 and 7+."""
    counts = {bucket: 0 for bucket in _CMC_BUCKETS}
    for card in cards:
        type_line = card.type_line or ""
        if exclude_lands and _is_land(type_line):
            continue
        if creatures_only and not _is_creature(type_line):
            continue
        bucket = _cmc_bucket(card.cmc)
        counts[bucket] += card.quantity
    return counts


def type_counts(cards: list[DeckCard]) -> dict[str, int]:
    """Quantity-weighted counts by primary card type."""
    counts: dict[str, int] = {}
    for card in cards:
        key = primary_card_type(card.type_line or "")
        counts[key] = counts.get(key, 0) + card.quantity
    return counts


def _avg_cmc(cards: list[DeckCard], *, predicate) -> float | None:
    total_cmc = 0.0
    total_qty = 0
    for card in cards:
        if not predicate(card.type_line or ""):
            continue
        total_cmc += card.cmc * card.quantity
        total_qty += card.quantity
    if total_qty == 0:
        return None
    return round(total_cmc / total_qty, 2)


def compute_deck_metrics(
    cards: list[DeckCard],
    *,
    mana_base: ManaBasePlan | None = None,
) -> dict:
    """Build UX10a metrics from maindeck card rows."""
    nonland_predicate = lambda tl: not _is_land(tl)  # noqa: E731
    creature_predicate = lambda tl: _is_creature(tl)  # noqa: E731

    land_count = sum(card.quantity for card in cards if _is_land(card.type_line or ""))
    ramp_count = mana_base.ramp.total if mana_base else sum(
        card.quantity for card in cards if card.slot == "ramp"
    )

    return {
        "cmc_histogram": cmc_histogram(cards),
        "creature_cmc_histogram": cmc_histogram(cards, creatures_only=True),
        "type_counts": type_counts(cards),
        "avg_cmc_nonland": _avg_cmc(cards, predicate=nonland_predicate),
        "avg_creature_cmc": _avg_cmc(cards, predicate=creature_predicate),
        "land_count": land_count,
        "ramp_count": ramp_count,
    }


_BAR_WIDTH = 20


def _ascii_bar(count: int, max_count: int) -> str:
    if count <= 0 or max_count <= 0:
        return ""
    filled = max(1, round(count / max_count * _BAR_WIDTH))
    return "█" * filled


def _curve_blurb(cmc_histogram: dict[str, int]) -> str:
    total = sum(cmc_histogram.values())
    if total == 0:
        return "No nonland spells to chart."
    early = cmc_histogram.get("0", 0) + cmc_histogram.get("1", 0) + cmc_histogram.get("2", 0)
    top = (
        cmc_histogram.get("5", 0)
        + cmc_histogram.get("6", 0)
        + cmc_histogram.get("7", 0)
        + cmc_histogram.get("7+", 0)
    )
    early_share = early / total
    top_share = top / total
    if early_share < 0.15:
        return "Light early game — few cards at 0–2 CMC."
    if top_share > 0.45:
        return "Top-heavy curve — many cards at 5+ CMC."
    return "Mana curve is spread across several CMC bands."


def render_deck_metrics_section(metrics: dict) -> list[str]:
    """Render ## Deck metrics markdown lines."""
    lines = ["## Deck metrics", ""]
    counts_by_type: dict[str, int] = metrics.get("type_counts") or {}
    if counts_by_type:
        lines.extend(["### Card types", "", "| Type | Count |", "| --- | ---: |"])
        for key in sorted(counts_by_type, key=lambda k: (-counts_by_type[k], k)):
            lines.append(f"| {key} | {counts_by_type[key]} |")
        lines.append("")

    cmc_hist: dict[str, int] = metrics.get("cmc_histogram") or {}
    creature_hist: dict[str, int] = metrics.get("creature_cmc_histogram") or {}
    if cmc_hist:
        max_count = max(cmc_hist.values(), default=0)
        lines.extend(
            [
                "### Mana curve (nonlands)",
                "",
                f"_{_curve_blurb(cmc_hist)}_",
                "",
                "| CMC | Count | Chart |",
                "| --- | ---: | --- |",
            ]
        )
        for bucket in _CMC_BUCKETS:
            count = cmc_hist.get(bucket, 0)
            lines.append(f"| {bucket} | {count} | {_ascii_bar(count, max_count)} |")
        lines.append("")

    avg_nonland = metrics.get("avg_cmc_nonland")
    avg_creature = metrics.get("avg_creature_cmc")
    land_count = metrics.get("land_count")
    ramp_count = metrics.get("ramp_count")
    summary_parts: list[str] = []
    if avg_nonland is not None:
        summary_parts.append(f"avg nonland CMC **{avg_nonland}**")
    if avg_creature is not None:
        summary_parts.append(f"avg creature CMC **{avg_creature}**")
    if land_count is not None:
        summary_parts.append(f"**{land_count}** lands")
    if ramp_count is not None:
        summary_parts.append(f"**{ramp_count}** ramp")
    if summary_parts:
        lines.append("### Summary")
        lines.append("")
        lines.append(" · ".join(summary_parts))
        lines.append("")

    if creature_hist and any(creature_hist.values()):
        max_creature = max(creature_hist.values())
        lines.extend(
            [
                "### Creature curve",
                "",
                "| CMC | Count | Chart |",
                "| --- | ---: | --- |",
            ]
        )
        for bucket in _CMC_BUCKETS:
            count = creature_hist.get(bucket, 0)
            if count == 0:
                continue
            lines.append(f"| {bucket} | {count} | {_ascii_bar(count, max_creature)} |")
        lines.append("")

    return lines
