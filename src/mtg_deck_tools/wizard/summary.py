"""Wizard criteria summary display."""

from __future__ import annotations

from rich.table import Table

from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.wizard.common import console
from mtg_deck_tools.wizard.slots import (
    COMMANDER_DECK_SIZE,
    load_slot_template_config,
    slot_template_total,
)


def print_wizard_summary(criteria: DeckCriteria) -> None:
    config = load_slot_template_config()
    table = Table(title="Deck criteria", show_header=True)
    table.add_column("Setting", style="cyan")
    table.add_column("Value")

    table.add_row("Themes", ", ".join(criteria.themes) if criteria.themes else "(none)")
    table.add_row(
        "Include mechanics",
        ", ".join(criteria.include_mechanics) if criteria.include_mechanics else "(none)",
    )
    table.add_row(
        "Avoid mechanics",
        ", ".join(criteria.avoid_mechanics) if criteria.avoid_mechanics else "(none)",
    )
    table.add_row(
        "Colors",
        ", ".join(criteria.colors) if criteria.colors else "(any)",
    )
    table.add_row(
        "Commanders",
        f"{len(criteria.commander_oracle_ids)} selected"
        if criteria.commander_oracle_ids
        else "(not set)",
    )

    if criteria.slot_template:
        for slot in config.order:
            count = criteria.slot_template.get(slot)
            if count is not None:
                table.add_row(config.labels.get(slot, slot), str(count))
        total = slot_template_total(criteria.slot_template)
        table.add_row("Total (excl. commander)", f"{total} / {COMMANDER_DECK_SIZE}")

    if criteria.budget_usd is not None:
        table.add_row("Budget", f"${criteria.budget_usd:.2f}")
    else:
        table.add_row("Budget", "(none)")

    if criteria.seed is not None:
        table.add_row("Seed", str(criteria.seed))

    console.print(table)
