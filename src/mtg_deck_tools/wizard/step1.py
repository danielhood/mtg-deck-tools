"""Wizard step 1: themes and slot template."""

from __future__ import annotations

import questionary
from rich.panel import Panel
from rich.table import Table

from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.wizard.common import WIZARD_STYLE, console, require_tty
from mtg_deck_tools.wizard.slots import (
    COMMANDER_DECK_SIZE,
    SlotTemplateConfig,
    clamp_slot_count,
    load_slot_template_config,
    slot_template_total,
    suggest_lands_count,
    validate_slot_template,
)
from mtg_deck_tools.wizard.themes import ArchetypeChoice, archetype_choices


def _prompt_themes(choices: list[ArchetypeChoice]) -> list[str]:
    if not choices:
        return []

    options = [
        questionary.Choice(
            title=f"{c.id} — {c.description}" if c.description else c.id,
            value=c.id,
        )
        for c in choices
    ]
    selected = questionary.checkbox(
        "Select deck themes (archetypes)",
        choices=options,
        style=WIZARD_STYLE,
        instruction="(Space to toggle, Enter to confirm; none is OK)",
    ).ask()

    if selected is None:
        raise KeyboardInterrupt
    return list(selected)


def _prompt_use_default_slots(config: SlotTemplateConfig) -> bool:
    default = config.default
    summary = ", ".join(
        f"{config.labels.get(slot, slot)} {default[slot]}"
        for slot in config.order
        if slot in default
    )
    choice = questionary.select(
        "Slot template",
        choices=[
            questionary.Choice(
                title=f"Use defaults ({summary})",
                value=True,
            ),
            questionary.Choice(title="Customize slot counts", value=False),
        ],
        style=WIZARD_STYLE,
    ).ask()
    if choice is None:
        raise KeyboardInterrupt
    return choice


def _prompt_slot_count(
    slot: str,
    *,
    config: SlotTemplateConfig,
    current_slots: dict[str, int],
) -> int:
    bounds = config.bounds[slot]
    label = config.labels.get(slot, slot)
    default = current_slots.get(slot, config.default[slot])

    if slot == "lands":
        suggested = suggest_lands_count(current_slots)
        default = clamp_slot_count(slot, suggested, config)
        running = slot_template_total({**current_slots, "lands": 0})
        hint = f"non-land cards: {running}; suggested lands: {suggested}"
    else:
        hint = f"allowed {bounds.min}–{bounds.max}"

    while True:
        raw = questionary.text(
            f"{label} [{hint}]",
            default=str(default),
            style=WIZARD_STYLE,
            validate=lambda text: _validate_count_text(slot, text, config=config),
        ).ask()
        if raw is None:
            raise KeyboardInterrupt
        count = int(raw.strip())
        return count


def _validate_count_text(
    slot: str,
    text: str,
    *,
    config: SlotTemplateConfig,
) -> bool | str:
    text = text.strip()
    if not text.isdigit():
        return "Enter a whole number"
    count = int(text)
    bounds = config.bounds[slot]
    if count < bounds.min or count > bounds.max:
        label = config.labels.get(slot, slot)
        return f"{label} must be between {bounds.min} and {bounds.max}"
    return True


def _prompt_custom_slots(config: SlotTemplateConfig) -> dict[str, int]:
    slots: dict[str, int] = {}
    for slot in config.order:
        if slot == "lands":
            continue
        count = _prompt_slot_count(slot, config=config, current_slots=slots)
        slots[slot] = count

    lands = _prompt_slot_count("lands", config=config, current_slots=slots)
    slots["lands"] = lands
    return slots


def print_step1_summary(criteria: DeckCriteria, config: SlotTemplateConfig | None = None) -> None:
    cfg = config or load_slot_template_config()
    table = Table(title="Step 1 — Themes & slots", show_header=True)
    table.add_column("Setting", style="cyan")
    table.add_column("Value")

    if criteria.themes:
        table.add_row("Themes", ", ".join(criteria.themes))
    else:
        table.add_row("Themes", "(none)")

    for slot in cfg.order:
        count = criteria.slot_template.get(slot)
        if count is not None:
            label = cfg.labels.get(slot, slot)
            table.add_row(label, str(count))

    total = slot_template_total(criteria.slot_template)
    table.add_row("Total (excl. commander)", f"{total} / {COMMANDER_DECK_SIZE}")
    console.print(table)


def run_step1(*, seed: int | None = None, show_summary: bool = True) -> DeckCriteria:
    """
    Interactive step 1: archetype themes and slot template counts.

    Returns partial DeckCriteria (colors, commander, mechanics filled in later steps).
    """
    require_tty()
    config = load_slot_template_config()
    choices = archetype_choices()

    console.print(
        Panel(
            "[bold]Step 1 of 6[/bold] — Themes & slot template\n"
            "Pick archetype tags for synergy cards and how many cards per deck slot.",
            title="MTG Deck Tools",
            border_style="cyan",
        )
    )

    themes = _prompt_themes(choices)

    if _prompt_use_default_slots(config):
        slot_template = dict(config.default)
    else:
        slot_template = _prompt_custom_slots(config)
        errors = validate_slot_template(slot_template, config)
        if errors:
            raise RuntimeError("Invalid slot template: " + "; ".join(errors))

    criteria = DeckCriteria(
        themes=themes,
        slot_template=slot_template,
        seed=seed,
    )
    if show_summary:
        print_step1_summary(criteria, config)
    return criteria
