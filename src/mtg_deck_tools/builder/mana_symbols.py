"""Render Scryfall mana notation as readable Markdown text."""

from __future__ import annotations

import re

_MANA_BRACE_RE = re.compile(r"\{([^}]+)\}")


def _format_single_symbol(inner: str, *, description: bool) -> str:
    symbol = inner.strip()
    upper = symbol.upper()

    if description:
        if upper == "T":
            return "**Tap**"
        if upper == "Q":
            return "**Untap**"

    if symbol.isdigit():
        return f"**{symbol}**"

    return f"({symbol})"


def format_mana_notation(text: str, *, description: bool = False) -> str:
    """
    Replace {symbols} in mana costs and oracle text for Markdown output.

    Mana symbols become parentheses, e.g. {G} → (G); digits → **n**;
    in descriptions {T}/{Q} → **Tap**/**Untap**.
    """
    if not text:
        return text

    return _MANA_BRACE_RE.sub(
        lambda match: _format_single_symbol(match.group(1), description=description),
        text,
    )
