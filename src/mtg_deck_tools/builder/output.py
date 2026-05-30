"""Write deck Markdown and .deck.json output."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from mtg_deck_tools import __version__
from mtg_deck_tools.builder.deck import DeckBuildResult, DeckCard
from mtg_deck_tools.builder.mana_base import ManaBasePlan
from mtg_deck_tools.builder.mana_symbols import format_mana_notation
from mtg_deck_tools.formatting import (
    format_card_name_with_type,
    format_card_price_range_display,
    format_display_date,
    format_price_display,
    format_released_at_display,
)
from mtg_deck_tools.tags.labels import format_tag_list
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.rules.commander import format_color_identity
from mtg_deck_tools.rules.rarity import format_min_rarity_display, format_rarity_display
from mtg_deck_tools.rules.dependencies import DependencyReport, dependency_report_to_dict
from mtg_deck_tools.rules.validate import ValidationResult
from mtg_deck_tools.wizard.slots import load_slot_template_config

_VALIDATION_NOTE_RE = re.compile(r"^\[[\w.]+\]")

NOTE_GROUPS: tuple[tuple[str, str], ...] = (
    ("dependencies", "Deck dependencies"),
    ("availability", "Availability / unpriced"),
    ("unpriced", "Unpriced cards"),
    ("budget_trim", "Budget trims"),
    ("mana_base", "Mana base"),
    ("slot", "Slot filling"),
    ("build", "Build issues"),
    ("other", "Other"),
)


def _validation_dict(result: ValidationResult | None) -> dict | None:
    if result is None:
        return None
    return {
        "passed": result.passed,
        "errors": [
            {"rule": i.rule, "message": i.message, "card_name": i.card_name}
            for i in result.errors
        ],
        "warnings": [
            {"rule": i.rule, "message": i.message, "card_name": i.card_name}
            for i in result.warnings
        ],
    }


def _mana_base_dict(plan: ManaBasePlan | None) -> dict | None:
    if plan is None:
        return None
    return {
        "template_lands": plan.template_lands,
        "suggested_lands": plan.suggested_lands,
        "actual_lands": plan.actual_lands,
        "nonbasic_target": plan.nonbasic_target,
        "basic_target": plan.basic_target,
        "avg_cmc_nonland": plan.avg_cmc_nonland,
        "num_colors": plan.num_colors,
        "pip_weights": plan.pip_weights,
        "ramp": {
            "total": plan.ramp.total,
            "mana_rocks": plan.ramp.mana_rocks,
            "land_ramp": plan.ramp.land_ramp,
            "other": plan.ramp.other,
            "effective_reduction": round(plan.ramp.effective_reduction, 2),
        },
    }


def _slugify(name: str) -> str:
    slug = name.lower().replace(" ", "-")
    return "".join(ch if ch.isalnum() or ch == "-" else "" for ch in slug)[:40]


def _avg_cmc_nonland(cards: list[DeckCard]) -> float | None:
    nonlands = [c for c in cards if "Land" not in c.type_line]
    if not nonlands:
        return None
    total = sum(c.cmc * c.quantity for c in nonlands)
    count = sum(c.quantity for c in nonlands)
    return round(total / count, 2) if count else None


def format_generated_timestamp(when: datetime) -> str:
    """Friendly local timestamp, e.g. May 29, 2026 · 16:06 PDT."""
    local = when.astimezone()
    return f"{format_display_date(local.date())} · {local.strftime('%H:%M %Z')}"


def _unpriced_classifications(cards: list[DeckCard]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {"likely_obscure": [], "price_pending": []}
    for card in cards:
        label = card.unpriced_classification
        if label in grouped and card.name not in grouped[label]:
            grouped[label].append(card.name)
    return grouped


def classify_warning(message: str) -> str:
    """Bucket a build warning for grouped Notes output."""
    if message.startswith("Dependency:"):
        return "dependencies"
    if message.startswith("Likely obscure:") or message.startswith("Price pending:"):
        return "availability"
    if message.startswith("No USD price for"):
        return "unpriced"
    if message.startswith("Budget trim:"):
        return "budget_trim"
    if (
        message.startswith("Mana base:")
        or message.startswith("Mana base suggested")
        or message.startswith("Land count")
    ):
        return "mana_base"
    if message.startswith("Slot '"):
        return "slot"
    if message.startswith("Basic land '"):
        return "build"
    if _VALIDATION_NOTE_RE.match(message):
        return "validation"
    return "other"


def group_warnings(
    warnings: list[str],
    *,
    include_validation_notes: bool = False,
) -> dict[str, list[str]]:
    """Group warnings by category for the Notes section."""
    grouped: dict[str, list[str]] = defaultdict(list)
    for message in warnings:
        category = classify_warning(message)
        if category == "validation" and not include_validation_notes:
            continue
        grouped[category].append(message)
    return grouped


def format_card_price(card: DeckCard) -> str:
    return format_price_display(price_known=card.price_known, price_usd=card.price_usd)


def format_commander_list_item(cmd: dict) -> str:
    """Single commander bullet with Scryfall link, price, and release date."""
    display = format_card_name_with_type(cmd["name"], cmd.get("type_line"))
    if cmd.get("scryfall_uri"):
        display = f"[{display}]({cmd['scryfall_uri']})"
    price = format_price_display(
        price_known=bool(cmd.get("price_known")),
        price_usd=cmd.get("price_usd"),
    )
    released = format_released_at_display(cmd.get("released_at"))
    return f"- {display} — **Price:** {price} · **Released:** {released}"


def format_card_mana_cost(card: DeckCard) -> str:
    raw = card.mana_cost.strip() if card.mana_cost else ""
    if not raw:
        return "—"
    return format_mana_notation(raw, description=False)


def format_card_description(card: DeckCard) -> str:
    text = (card.oracle_text or "").strip()
    if not text:
        return "—"
    return format_mana_notation(" ".join(text.split()), description=True)


def format_card_power_toughness(card: DeckCard) -> str:
    power = (card.power or "").strip()
    toughness = (card.toughness or "").strip()
    if not power and not toughness:
        return "—"
    if power and toughness:
        return f"{power}/{toughness}"
    return power or toughness


def format_card_detail_title(card: DeckCard) -> str:
    """Card name for the details heading, linked to Scryfall when URI is known."""
    qty = f" ({card.quantity}×)" if card.quantity > 1 else ""
    title = format_card_name_with_type(card.name, card.type_line) + qty
    if card.scryfall_uri:
        return f"[{title}]({card.scryfall_uri})"
    return title


def format_card_released_at(card: DeckCard) -> str:
    return format_released_at_display(card.released_at)


def format_card_rarity(card: DeckCard) -> str:
    return format_rarity_display(card.rarity)


def _commander_card_cost(cmd: dict) -> float:
    if cmd.get("price_known") and cmd.get("price_usd") is not None:
        return float(cmd["price_usd"])
    return 0.0


def estimated_deck_price(maindeck: DeckBuildResult, commanders: list[dict]) -> float:
    """Sum priced maindeck cards and commander(s) with known USD prices."""
    total = maindeck.budget_spent + sum(_commander_card_cost(cmd) for cmd in commanders)
    return round(total, 2)


def commanders_to_deck_cards(commanders: list[dict]) -> list[DeckCard]:
    """Convert commander metadata dicts into DeckCard rows for detail rendering."""
    cards: list[DeckCard] = []
    for cmd in commanders:
        cards.append(
            DeckCard(
                oracle_id=cmd.get("oracle_id", ""),
                name=cmd["name"],
                slot="commander",
                quantity=1,
                cmc=float(cmd.get("cmc") or 0),
                mana_cost=cmd.get("mana_cost") or "",
                type_line=cmd.get("type_line") or "",
                price_usd=cmd.get("price_usd"),
                price_known=bool(cmd.get("price_known")),
                scryfall_uri=cmd.get("scryfall_uri"),
                image_uri=cmd.get("image_uri"),
                oracle_text=cmd.get("oracle_text") or "",
                released_at=cmd.get("released_at"),
                rarity=cmd.get("rarity"),
                power=cmd.get("power"),
                toughness=cmd.get("toughness"),
            )
        )
    return cards


def _render_single_card_detail(card: DeckCard) -> list[str]:
    return [
        f"#### {format_card_detail_title(card)}",
        f"- **Price:** {format_card_price(card)}",
        f"- **Rarity:** {format_card_rarity(card)}",
        f"- **Released:** {format_card_released_at(card)}",
        f"- **Mana cost:** {format_card_mana_cost(card)}",
        f"- **Power/Toughness:** {format_card_power_toughness(card)}",
        f"- **Description:** {format_card_description(card)}",
        "",
    ]


def _render_dependency_section(report: DependencyReport) -> list[str]:
    status = "OK" if report.passed else "WARNINGS"
    lines = ["## Deck dependencies", "", f"**Status:** {status}", ""]
    if report.profiles:
        lines.append("### Profile summary")
        for profile in report.profiles:
            counts = ", ".join(f"{k}={v}" for k, v in sorted(profile.counts.items()))
            lines.append(f"- **{profile.profile_id}:** {counts} ({profile.status})")
        lines.append("")
    fails = [i for i in report.issues if i.status == "fail"]
    if fails:
        lines.append("### Failures (strict)")
        for issue in fails:
            name = f" — {issue.card_name}" if issue.card_name else ""
            lines.append(f"- **[{issue.rule_id}]**{name} {issue.message}")
        lines.append("")
    warns = [i for i in report.issues if i.status == "warn"]
    if warns:
        lines.append("### Warnings")
        for issue in warns:
            name = f" — {issue.card_name}" if issue.card_name else ""
            lines.append(f"- **[{issue.rule_id}]**{name} {issue.message}")
        lines.append("")
    return lines


def _render_notes_section(
    warnings: list[str],
    *,
    validation: ValidationResult | None,
) -> list[str]:
    if not warnings:
        return []

    include_validation_notes = validation is None
    grouped = group_warnings(warnings, include_validation_notes=include_validation_notes)
    if not grouped:
        return []

    lines = ["## Notes", ""]
    for key, heading in NOTE_GROUPS:
        items = grouped.get(key)
        if not items:
            continue
        lines.append(f"### {heading}")
        for item in items:
            lines.append(f"- {item}")
        lines.append("")
    return lines


def _render_card_details_section(
    cards: list[DeckCard],
    slot_order: list[str],
    slot_labels: dict[str, str],
    *,
    commanders: list[dict] | None = None,
) -> list[str]:
    commander_cards = commanders_to_deck_cards(commanders or [])
    if not commander_cards and not cards:
        return []

    by_slot: dict[str, list[DeckCard]] = defaultdict(list)
    for card in cards:
        by_slot[card.slot].append(card)

    lines = ["## Card details", ""]
    if commander_cards:
        lines.append("### Commander")
        lines.append("")
        for card in commander_cards:
            lines.extend(_render_single_card_detail(card))

    for slot in slot_order:
        slot_cards = by_slot.get(slot)
        if not slot_cards:
            continue
        label = slot_labels.get(slot, slot)
        lines.append(f"### {label}")
        lines.append("")
        for card in sorted(slot_cards, key=lambda c: (-c.quantity, c.cmc, c.name)):
            lines.extend(_render_single_card_detail(card))
    return lines


def write_deck_outputs(
    *,
    base_path: Path,
    criteria: DeckCriteria,
    commanders: list[dict],
    maindeck: DeckBuildResult,
    identity: list[str],
) -> tuple[Path, Path]:
    """Write paired .deck.json and .md files; return json path."""
    slot_config = load_slot_template_config()
    generated_at = datetime.now(UTC)
    generated_at_iso = generated_at.isoformat()
    generated_at_display = format_generated_timestamp(generated_at)
    commander_names = ", ".join(
        format_card_name_with_type(c["name"], c.get("type_line")) for c in commanders
    )
    slug = _slugify(commanders[0]["name"] if commanders else "deck")
    timestamp = generated_at.strftime("%Y%m%d%H%M%S")
    out_base = base_path.parent / f"{slug}-{timestamp}"
    out_base.parent.mkdir(parents=True, exist_ok=True)

    avg_cmc = _avg_cmc_nonland(maindeck.cards)
    estimated = estimated_deck_price(maindeck, commanders)
    unpriced_by_class = _unpriced_classifications(maindeck.cards)
    deck_json = {
        "schema_version": "1.0",
        "generated_at": generated_at_iso,
        "generator": {"name": "mtg-deck-tools", "version": __version__},
        "criteria": criteria.model_dump(),
        "commanders": commanders,
        "cards": [
            {
                "oracle_id": c.oracle_id,
                "name": c.name,
                "slot": c.slot,
                "quantity": c.quantity,
                "cmc": c.cmc,
                "mana_cost": c.mana_cost,
                "type_line": c.type_line,
                "price_usd": c.price_usd,
                "price_known": c.price_known,
                "scryfall_uri": c.scryfall_uri,
                "image_uri": c.image_uri,
                "mechanic_tags": c.mechanic_tags,
                "released_at": c.released_at,
                "rarity": c.rarity,
                "power": c.power,
                "toughness": c.toughness,
                "unpriced_classification": c.unpriced_classification,
            }
            for c in maindeck.cards
        ],
        "stats": {
            "maindeck_cards": sum(c.quantity for c in maindeck.cards),
            "estimated_price_usd": estimated,
            "maindeck_price_usd": round(maindeck.budget_spent, 2),
            "unpriced_card_count": len(maindeck.unpriced_names),
            "unpriced_card_names": maindeck.unpriced_names,
            "unpriced_by_classification": unpriced_by_class,
            "avg_cmc_nonland": avg_cmc,
        },
        "mana_base": _mana_base_dict(maindeck.mana_base),
        "validation": _validation_dict(maindeck.validation),
        "dependency_report": (
            dependency_report_to_dict(maindeck.dependency_report)
            if maindeck.dependency_report
            else None
        ),
        "warnings": maindeck.warnings,
    }

    json_path = out_base.with_suffix(".deck.json")
    md_path = out_base.with_suffix(".md")
    json_path.write_text(json.dumps(deck_json, indent=2), encoding="utf-8")

    lines = [
        f"# {commander_names}",
        "",
        f"**Commander{'s' if len(commanders) > 1 else ''}:** {commander_names}",
        f"**Color identity:** {format_color_identity(identity)}",
    ]
    if criteria.budget_usd is not None:
        lines.append(
            f"**Budget cap:** ${criteria.budget_usd:.2f} · "
            f"**Estimated deck:** ${estimated:.2f}"
        )
    else:
        lines.append(f"**Estimated deck:** ${estimated:.2f}")
    price_range = format_card_price_range_display(
        min_usd=criteria.card_price_min_usd,
        max_usd=criteria.card_price_max_usd,
    )
    if price_range:
        lines.append(f"**Card price range:** {price_range}")
    if criteria.min_rarity != "common":
        lines.append(f"**Minimum rarity:** {format_min_rarity_display(criteria.min_rarity)}")
    if criteria.strict_budget:
        lines.append("**Strict budget:** yes (unpriced cards excluded from pool)")
    if criteria.prefer_available:
        lines.append("**Prefer available:** yes (low availability score excluded)")
    lines.append(f"**Generated:** {generated_at_display}")
    lines.append(f"**Seed:** {criteria.seed if criteria.seed is not None else 'random'}")
    if criteria.themes:
        lines.append(f"**Themes:** {format_tag_list(criteria.themes)}")
    if criteria.include_mechanics:
        lines.append(f"**Include mechanics:** {format_tag_list(criteria.include_mechanics)}")
    if criteria.avoid_mechanics:
        lines.append(f"**Avoid mechanics:** {format_tag_list(criteria.avoid_mechanics)}")
    lines.append("")

    if criteria.slot_template:
        lines.extend(["## Summary", "", "| Slot | Count |", "| --- | ---: |"])
        for slot in slot_config.order:
            count = criteria.slot_template.get(slot)
            if count is not None:
                label = slot_config.labels.get(slot, slot)
                filled = sum(c.quantity for c in maindeck.cards if c.slot == slot)
                lines.append(f"| {label} | {filled} |")
        lines.append("")

    lines.extend(["## Commander", ""])
    for cmd in commanders:
        lines.append(format_commander_list_item(cmd))
    lines.append("")

    if maindeck.dependency_report and maindeck.dependency_report.issues:
        lines.extend(_render_dependency_section(maindeck.dependency_report))

    if maindeck.validation:
        v = maindeck.validation
        status = "PASSED" if v.passed else "FAILED"
        lines.extend(["## Validation", "", f"**Status:** {status}", ""])
        if v.errors:
            lines.append("### Errors")
            for issue in v.errors:
                name = f" — {issue.card_name}" if issue.card_name else ""
                lines.append(f"- **[{issue.rule}]**{name} {issue.message}")
            lines.append("")
        if v.warnings:
            lines.append("### Warnings")
            for issue in v.warnings:
                name = f" — {issue.card_name}" if issue.card_name else ""
                lines.append(f"- **[{issue.rule}]**{name} {issue.message}")
            lines.append("")

    if maindeck.mana_base:
        mb = maindeck.mana_base
        lines.extend(
            [
                "## Mana base",
                "",
                f"- **Lands:** {mb.actual_lands} "
                f"(suggested {mb.suggested_lands}, template {mb.template_lands})",
                f"- **Mix:** {mb.nonbasic_target} nonbasic / {mb.basic_target} basic",
                f"- **Avg CMC (nonlands):** {mb.avg_cmc_nonland}",
                f"- **Ramp:** {mb.ramp.total} "
                f"({mb.ramp.mana_rocks} rocks, {mb.ramp.land_ramp} land ramp)",
            ]
        )
        if mb.pip_weights:
            pip_line = ", ".join(f"{c}:{n}" for c, n in sorted(mb.pip_weights.items()))
            lines.append(f"- **Pip weights:** {pip_line}")
        lines.append("")

    by_slot: dict[str, list[DeckCard]] = defaultdict(list)
    for card in maindeck.cards:
        by_slot[card.slot].append(card)

    lines.extend([f"## Maindeck ({sum(c.quantity for c in maindeck.cards)})", ""])
    for slot in slot_config.order:
        slot_cards = by_slot.get(slot)
        if not slot_cards:
            continue
        label = slot_config.labels.get(slot, slot)
        lines.append(f"### {label}")
        for card in sorted(slot_cards, key=lambda c: (-c.quantity, c.cmc, c.name)):
            qty = f"{card.quantity}x " if card.quantity > 1 else ""
            price = (
                f" (${card.price_usd:.2f})"
                if card.price_known and card.price_usd is not None
                else ""
            )
            display = format_card_name_with_type(card.name, card.type_line)
            lines.append(f"- {qty}{display}{price}")
        lines.append("")

    lines.extend(
        _render_notes_section(maindeck.warnings, validation=maindeck.validation)
    )
    lines.extend(
        _render_card_details_section(
            maindeck.cards,
            slot_config.order,
            slot_config.labels,
            commanders=commanders,
        )
    )

    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return json_path, md_path
