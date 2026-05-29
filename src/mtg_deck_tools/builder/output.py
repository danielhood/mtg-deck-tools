"""Write deck Markdown and .deck.json output."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from mtg_deck_tools import __version__
from mtg_deck_tools.builder.filler import DeckBuildResult, DeckCard
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.wizard.slots import load_slot_template_config


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
    generated_at = datetime.now(UTC).isoformat()
    commander_names = ", ".join(c["name"] for c in commanders)
    slug = _slugify(commander_names.split(",")[0])
    timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    out_base = base_path.parent / f"{slug}-{timestamp}"
    out_base.parent.mkdir(parents=True, exist_ok=True)

    avg_cmc = _avg_cmc_nonland(maindeck.cards)
    deck_json = {
        "schema_version": "1.0",
        "generated_at": generated_at,
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
            }
            for c in maindeck.cards
        ],
        "stats": {
            "maindeck_cards": sum(c.quantity for c in maindeck.cards),
            "estimated_price_usd": round(maindeck.budget_spent, 2),
            "unpriced_card_count": len(maindeck.unpriced_names),
            "unpriced_card_names": maindeck.unpriced_names,
            "avg_cmc_nonland": avg_cmc,
        },
        "warnings": maindeck.warnings,
    }

    json_path = out_base.with_suffix(".deck.json")
    md_path = out_base.with_suffix(".md")
    json_path.write_text(json.dumps(deck_json, indent=2), encoding="utf-8")

    lines = [
        f"# {commander_names}",
        "",
        f"**Commander{'s' if len(commanders) > 1 else ''}:** {commander_names}",
        f"**Color identity:** {', '.join(identity) or 'colorless'}",
    ]
    if criteria.budget_usd is not None:
        lines.append(
            f"**Budget cap:** ${criteria.budget_usd:.2f} · "
            f"**Estimated maindeck:** ${maindeck.budget_spent:.2f}"
        )
    lines.append(f"**Generated:** {generated_at}")
    lines.append(f"**Seed:** {criteria.seed if criteria.seed is not None else 'random'}")
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
        lines.append(f"- {cmd['name']}")
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
            lines.append(f"- {qty}{card.name}{price}")
        lines.append("")

    if criteria.themes or criteria.include_mechanics or criteria.avoid_mechanics:
        lines.extend(["## Criteria", ""])
        if criteria.themes:
            lines.append(f"- **Themes:** {', '.join(criteria.themes)}")
        if criteria.include_mechanics:
            lines.append(f"- **Include mechanics:** {', '.join(criteria.include_mechanics)}")
        if criteria.avoid_mechanics:
            lines.append(f"- **Avoid mechanics:** {', '.join(criteria.avoid_mechanics)}")
        lines.append("")

    if maindeck.warnings:
        lines.extend(["## Notes", ""])
        for warning in maindeck.warnings:
            lines.append(f"- {warning}")
        lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path
