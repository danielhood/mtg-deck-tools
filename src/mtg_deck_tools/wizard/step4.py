"""Wizard step 4: commander selection."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import questionary
from rich.panel import Panel

from mtg_deck_tools.formatting import format_card_name_with_type
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.paths import DEFAULT_DB_PATH
from mtg_deck_tools.wizard.commanders import (
    CommanderRow,
    combined_color_identity,
    fetch_commander,
    format_commander_choice,
    search_commanders,
)
from mtg_deck_tools.wizard.common import WIZARD_STYLE, console, require_tty


def _require_db(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        raise FileNotFoundError(
            f"Database not found at {db_path}. Run: mtg-deck-tools import"
        )
    from mtg_deck_tools.db.connection import connect

    return connect(db_path)


def _prompt_commander_pick(
    conn: sqlite3.Connection,
    *,
    colors: list[str],
    label: str,
) -> CommanderRow:
    while True:
        query = questionary.text(
            f"{label} — search name (blank shows popular matches)",
            style=WIZARD_STYLE,
        ).ask()
        if query is None:
            raise KeyboardInterrupt

        results = search_commanders(conn, colors=colors, name_query=query or "")
        if not results:
            console.print("[yellow]No commanders found. Try a different search or colors.[/yellow]")
            continue

        options = [
            questionary.Choice(title=format_commander_choice(cmd), value=cmd.oracle_id)
            for cmd in results
        ]
        options.append(questionary.Choice(title="Search again", value="__search__"))

        picked = questionary.select(
            f"Select {label.lower()}",
            choices=options,
            style=WIZARD_STYLE,
        ).ask()
        if picked is None:
            raise KeyboardInterrupt
        if picked == "__search__":
            continue

        commander = fetch_commander(conn, picked)
        if commander:
            return commander


def _prompt_add_partner(commander: CommanderRow) -> bool:
    if not commander.partner_kind:
        return False
    choice = questionary.confirm(
        f"{format_card_name_with_type(commander.name, commander.type_line)} supports partners. "
        "Add a second commander?",
        default=False,
        style=WIZARD_STYLE,
    ).ask()
    if choice is None:
        raise KeyboardInterrupt
    return choice


def run_step4(
    criteria: DeckCriteria,
    *,
    db_path: Path | None = None,
) -> DeckCriteria:
    """Interactive step 4: pick commander (and optional partner)."""
    require_tty()
    path = db_path or DEFAULT_DB_PATH
    conn = _require_db(path)

    try:
        console.print(
            Panel(
                "[bold]Step 5 of 6[/bold] — Commander\n"
                "Search and select your commander. Partner commanders can add a second.",
                title="MTG Deck Tools",
                border_style="cyan",
            )
        )

        primary = _prompt_commander_pick(
            conn,
            colors=criteria.colors,
            label="Commander",
        )
        commanders = [primary]

        if _prompt_add_partner(primary):
            partner = _prompt_commander_pick(
                conn,
                colors=combined_color_identity(commanders),
                label="Partner commander",
            )
            if partner.oracle_id == primary.oracle_id:
                raise RuntimeError("Partner must be a different card.")
            commanders.append(partner)

        return criteria.model_copy(
            update={
                "commander_oracle_ids": [c.oracle_id for c in commanders],
                "colors": combined_color_identity(commanders),
            }
        )
    finally:
        conn.close()
