"""Shared wizard utilities."""

from __future__ import annotations

import sys

from questionary import Style
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
