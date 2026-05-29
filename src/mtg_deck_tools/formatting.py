"""Shared display formatting for prices and dates."""

from __future__ import annotations

from datetime import date


def format_display_date(value: date) -> str:
    """Display date as 'May 29, 2026'."""
    return f"{value.strftime('%B')} {value.day}, {value.year}"


def format_price_display(*, price_known: bool, price_usd: float | None) -> str:
    if price_known and price_usd is not None:
        return f"${price_usd:.2f}"
    return "No price"


def format_released_at_display(released_at: str | None) -> str:
    """Human-readable release date from Scryfall released_at (YYYY-MM-DD)."""
    raw = (released_at or "").strip()
    if not raw:
        return "—"
    try:
        return format_display_date(date.fromisoformat(raw[:10]))
    except ValueError:
        return raw
