"""Shared wizard utilities."""

from __future__ import annotations

import sys

from questionary import Choice, Style
from rich.console import Console

WIZARD_STYLE = Style(
    [
        ("qmark", "fg:cyan bold"),
        ("question", "bold"),
        ("answer", "fg:green bold"),
        ("pointer", "fg:cyan bold"),
        ("highlighted", "fg:cyan bold"),
        ("selected", "fg:green"),
    ]
)

console = Console()

COLOR_CHOICES = [
    ("W", "White"),
    ("U", "Blue"),
    ("B", "Black"),
    ("R", "Red"),
    ("G", "Green"),
]


def require_tty() -> None:
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise RuntimeError(
            "Interactive wizard requires a TTY. "
            "Use CLI flags on generate instead."
        )


def format_tag_label(tag_id: str, description: str = "") -> str:
    if description:
        return f"{tag_id} — {description}"
    return tag_id.replace("_", " ").title()


def apply_checkbox_selection(
    options: list[Choice],
    selected: list[str],
) -> list[Choice]:
    """Preselect checkbox choices (questionary 2.x uses ``checked``, not ``default`` lists)."""
    selected_set = set(selected)
    return [
        Choice(
            title=choice.title,
            value=choice.value,
            disabled=choice.disabled,
            checked=choice.value in selected_set,
            shortcut_key=choice.shortcut_key,
            description=choice.description,
        )
        for choice in options
    ]
