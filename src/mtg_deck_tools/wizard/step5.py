"""Wizard step 5: budget and per-card price range."""

from __future__ import annotations

import questionary
from rich.panel import Panel

from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.rules.rarity import RARITY_ORDER, format_min_rarity_display
from mtg_deck_tools.wizard.common import WIZARD_STYLE, console, require_tty


def _validate_positive_money(text: str) -> bool | str:
    text = text.strip()
    if not text:
        return "Enter a dollar amount"
    try:
        value = float(text)
    except ValueError:
        return "Enter a valid number (e.g. 150)"
    if value <= 0:
        return "Amount must be greater than 0"
    return True


def _validate_optional_money(text: str) -> bool | str:
    text = text.strip()
    if not text:
        return True
    try:
        value = float(text)
    except ValueError:
        return "Enter a valid number or leave blank"
    if value < 0:
        return "Amount must be >= 0"
    return True


def _prompt_optional_money(label: str, *, default: str = "") -> float | None:
    raw = questionary.text(
        label,
        default=default,
        style=WIZARD_STYLE,
        validate=_validate_optional_money,
    ).ask()
    if raw is None:
        raise KeyboardInterrupt
    text = raw.strip()
    return float(text) if text else None


def _prompt_card_price_range(criteria: DeckCriteria) -> DeckCriteria:
    set_range = questionary.confirm(
        "Set a per-card price range (USD min and/or max)?",
        default=False,
        style=WIZARD_STYLE,
    ).ask()
    if set_range is None:
        raise KeyboardInterrupt
    if not set_range:
        return criteria

    min_usd = _prompt_optional_money(
        "Minimum price per card (USD, blank for none)",
        default="",
    )
    max_usd = _prompt_optional_money(
        "Maximum price per card (USD, blank for none)",
        default="",
    )
    if min_usd is None and max_usd is None:
        console.print("[yellow]No range set — skipping per-card price limits.[/yellow]")
        return criteria
    if min_usd is not None and max_usd is not None and min_usd > max_usd:
        raise RuntimeError("Minimum card price cannot exceed maximum card price.")

    return criteria.model_copy(
        update={
            "card_price_min_usd": min_usd,
            "card_price_max_usd": max_usd,
        }
    )


def _prompt_min_rarity(criteria: DeckCriteria) -> DeckCriteria:
    choices = [
        questionary.Choice(title=format_min_rarity_display(rarity), value=rarity)
        for rarity in RARITY_ORDER
    ]
    picked = questionary.select(
        "Minimum card rarity",
        choices=choices,
        default=criteria.min_rarity,
        style=WIZARD_STYLE,
    ).ask()
    if picked is None:
        raise KeyboardInterrupt
    return criteria.model_copy(update={"min_rarity": picked})


def run_step5(criteria: DeckCriteria) -> DeckCriteria:
    """Interactive step 5: optional deck budget and per-card price range."""
    require_tty()

    console.print(
        Panel(
            "[bold]Step 6 of 6[/bold] — Budget\n"
            "Optional total deck cap and per-card min/max using Scryfall prices. "
            "When a budget is set, you can exclude unpriced cards and prefer "
            "readily available picks (same as [bold]--strict-budget[/bold] / "
            "[bold]--prefer-available[/bold] at generate time).",
            title="MTG Deck Tools",
            border_style="cyan",
        )
    )

    set_budget = questionary.confirm(
        "Set a total deck budget (USD)?",
        default=False,
        style=WIZARD_STYLE,
    ).ask()
    if set_budget is None:
        raise KeyboardInterrupt

    if set_budget:
        raw = questionary.text(
            "Maximum deck budget (USD)",
            default="150",
            style=WIZARD_STYLE,
            validate=_validate_positive_money,
        ).ask()
        if raw is None:
            raise KeyboardInterrupt
        criteria = criteria.model_copy(update={"budget_usd": float(raw.strip())})
        exclude_unpriced = questionary.confirm(
            "Exclude cards without USD prices from the build?",
            default=True,
            style=WIZARD_STYLE,
        ).ask()
        if exclude_unpriced is None:
            raise KeyboardInterrupt
        criteria = criteria.model_copy(update={"strict_budget": exclude_unpriced})

        prefer_available = questionary.confirm(
            "Prefer readily available cards (filter obscure / hard-to-find picks)?",
            default=True,
            style=WIZARD_STYLE,
        ).ask()
        if prefer_available is None:
            raise KeyboardInterrupt
        criteria = criteria.model_copy(update={"prefer_available": prefer_available})

    criteria = _prompt_card_price_range(criteria)
    return _prompt_min_rarity(criteria)
