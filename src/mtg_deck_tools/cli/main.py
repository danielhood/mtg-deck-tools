"""Typer CLI for mtg-deck-tools."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.table import Table

from mtg_deck_tools import __version__
from mtg_deck_tools.builder.stub import run_generate_stub
from mtg_deck_tools.db.stats import fetch_stats
from mtg_deck_tools.import_.pipeline import run_import
from mtg_deck_tools.paths import DEFAULT_DB_PATH
from mtg_deck_tools.wizard.step1 import run_step1

app = typer.Typer(
    name="mtg-deck-tools",
    help="Local Commander deck builder for Magic: The Gathering.",
    no_args_is_help=True,
)
console = Console()


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"mtg-deck-tools {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        Optional[bool],
        typer.Option("--version", "-V", callback=_version_callback, is_eager=True),
    ] = None,
) -> None:
    """MTG Commander deck tools."""


@app.command("import")
def import_cmd(
    json_path: Annotated[
        Optional[Path],
        typer.Option("--json", help="Path to oracle-cards bulk JSON"),
    ] = None,
    db_path: Annotated[
        Optional[Path],
        typer.Option("--db", help="SQLite database output path"),
    ] = None,
) -> None:
    """Import Scryfall oracle cards and apply mechanic tags."""
    def progress(msg: str) -> None:
        console.print(msg)

    try:
        result = run_import(json_path=json_path, db_path=db_path, progress=progress)
    except FileNotFoundError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1) from exc

    table = Table(title="Import summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value")
    for key, value in result.items():
        table.add_row(key, str(value))
    console.print(table)


@app.command("stats")
def stats_cmd(
    db_path: Annotated[
        Optional[Path],
        typer.Option("--db", help="SQLite database path"),
    ] = None,
) -> None:
    """Show database statistics."""
    path = db_path or DEFAULT_DB_PATH
    if not path.exists():
        console.print(f"[red]Database not found:[/red] {path}\nRun: mtg-deck-tools import")
        raise typer.Exit(1)

    stats = fetch_stats(path)
    table = Table(title=f"Database — {path}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value")
    table.add_row("Playable cards", str(stats["total_cards"]))
    table.add_row("Commander-eligible", str(stats["commander_eligible"]))
    table.add_row("With partner ability", str(stats["with_partner"]))
    table.add_row("Tag assignments", str(stats["tag_assignments"]))
    table.add_row("Distinct tags", str(stats["distinct_tags"]))
    for key, value in stats["metadata"].items():
        table.add_row(key, value)
    console.print(table)

    if stats["top_tags"]:
        tag_table = Table(title="Top tags")
        tag_table.add_column("Tag")
        tag_table.add_column("Layer")
        tag_table.add_column("Cards", justify="right")
        for row in stats["top_tags"]:
            tag_table.add_row(row["tag"], row["layer"], str(row["n"]))
        console.print(tag_table)


@app.command("wizard")
def wizard_cmd(
    seed: Annotated[
        Optional[int],
        typer.Option("--seed", help="RNG seed stored in criteria for later generate steps"),
    ] = None,
) -> None:
    """Run the deck-building wizard (step 1: themes and slot template)."""
    try:
        run_step1(seed=seed)
    except KeyboardInterrupt:
        console.print("\n[dim]Wizard cancelled.[/dim]")
        raise typer.Exit(130) from None
    except RuntimeError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1) from exc

    console.print(
        "[dim]Steps 2–5 (mechanics, colors, commander, budget) coming soon. "
        "Use `mtg-deck-tools generate --wizard` for a stub preview.[/dim]"
    )


@app.command("generate")
def generate_cmd(
    wizard: Annotated[
        bool,
        typer.Option("--wizard", help="Run wizard step 1 before generating stub output"),
    ] = False,
    seed: Annotated[
        Optional[int],
        typer.Option("--seed", help="RNG seed for reproducible samples"),
    ] = None,
    colors: Annotated[
        Optional[str],
        typer.Option("--colors", help="Comma-separated color letters, e.g. B,G"),
    ] = None,
    themes: Annotated[
        Optional[str],
        typer.Option("--themes", help="Comma-separated theme tags, e.g. aristocrats,tokens"),
    ] = None,
    db_path: Annotated[Optional[Path], typer.Option("--db")] = None,
    output_dir: Annotated[Optional[Path], typer.Option("--out")] = None,
) -> None:
    """
    Generate deck output (Phase 1 stub: commander + sample cards).

    Use --wizard for interactive step 1, then stub preview. Full 100-card builds are Phase 2.
    """
    criteria = None
    if wizard:
        if colors or themes:
            console.print(
                "[yellow]Note:[/yellow] --colors and --themes are ignored when --wizard is set."
            )
        try:
            criteria = run_step1(seed=seed)
        except KeyboardInterrupt:
            console.print("\n[dim]Wizard cancelled.[/dim]")
            raise typer.Exit(130) from None
        except RuntimeError as exc:
            console.print(f"[red]Error:[/red] {exc}")
            raise typer.Exit(1) from exc
        console.print("[dim]Wizard steps 2–5 skipped in stub mode.[/dim]")

    color_list = [c.strip().upper() for c in colors.split(",")] if colors else None
    theme_list = [t.strip() for t in themes.split(",")] if themes else None

    try:
        out = run_generate_stub(
            db_path=db_path,
            seed=seed,
            colors=color_list,
            themes=theme_list,
            criteria=criteria,
            output_dir=output_dir,
        )
    except (FileNotFoundError, RuntimeError) as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1) from exc

    md_path = out.with_suffix(".md")
    console.print(f"[green]Wrote[/green] {out}")
    console.print(f"[green]Wrote[/green] {md_path}")
    console.print(
        "[dim]Phase 1 stub — run import first, then Phase 2 for full deck generation.[/dim]"
    )


if __name__ == "__main__":
    app()
