"""Shared display formatting for prices and dates."""

from __future__ import annotations

from datetime import date


def format_display_date(value: date) -> str:
    """Display date as 'May 29, 2026'."""
    return f"{value.strftime('%B')} {value.day}, {value.year}"


def format_card_name_with_type(name: str, type_line: str | None) -> str:
    """Display label: 'Sol Ring - Artifact'."""
    card_type = (type_line or "").strip()
    if not card_type:
        return name
    return f"{name} - {card_type}"


def format_price_display(*, price_known: bool, price_usd: float | None) -> str:
    if price_known and price_usd is not None:
        return f"${price_usd:.2f}"
    return "No price"


def format_card_price_range_display(
    *,
    min_usd: float | None,
    max_usd: float | None,
) -> str | None:
    if min_usd is None and max_usd is None:
        return None
    if min_usd is not None and max_usd is not None:
        return f"${min_usd:.2f} – ${max_usd:.2f} per card"
    if min_usd is not None:
        return f"${min_usd:.2f} minimum per card"
    return f"${max_usd:.2f} maximum per card"


def format_released_at_display(released_at: str | None) -> str:
    """Human-readable release date from Scryfall released_at (YYYY-MM-DD)."""
    raw = (released_at or "").strip()
    if not raw:
        return "—"
    try:
        return format_display_date(date.fromisoformat(raw[:10]))
    except ValueError:
        return raw
