"""Typer CLI for mtg-deck-tools."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.table import Table

from mtg_deck_tools import __version__
from mtg_deck_tools.builder.generate import run_generate
from mtg_deck_tools.builder.reload import run_generate_from_deck
from mtg_deck_tools.builder.stub import run_generate_stub
from mtg_deck_tools.db.stats import fetch_stats
from mtg_deck_tools.import_.pipeline import run_import
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.effects.audit import run_audit_to_disk
from mtg_deck_tools.paths import DEFAULT_DB_PATH, DEPENDENCY_RESOURCES_DIR
from mtg_deck_tools.wizard.run import run_wizard

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
    if stats.get("effect_rows"):
        table.add_row("Effect atom rows", str(stats["effect_rows"]))
        table.add_row("Distinct effect kinds", str(stats["distinct_effect_kinds"]))
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


@app.command("dependency-audit")
def dependency_audit_cmd(
    db_path: Annotated[
        Optional[Path],
        typer.Option("--db", help="SQLite database path"),
    ] = None,
    out_dir: Annotated[
        Optional[Path],
        typer.Option(
            "--out",
            help="Directory for audit JSON/CSV (default: resources/dependency/reports)",
        ),
    ] = None,
) -> None:
    """Scan cards.db and write dependency inventory reports (D0.5)."""
    path = db_path or DEFAULT_DB_PATH
    if not path.exists():
        console.print(f"[red]Database not found:[/red] {path}\nRun: mtg-deck-tools import")
        raise typer.Exit(1)

    output = out_dir or (DEPENDENCY_RESOURCES_DIR / "reports")
    try:
        audit = run_audit_to_disk(path, output)
    except Exception as exc:
        console.print(f"[red]Audit failed:[/red] {exc}")
        raise typer.Exit(1) from exc

    console.print(f"[green]Audit complete.[/green] {audit['commander_legal_cards']} commander-legal cards.")
    table = Table(title="Reports")
    table.add_column("Artifact")
    table.add_column("Path")
    for key, rel in audit.get("report_paths", {}).items():
        table.add_row(key, rel)
    console.print(table)

    energy = audit.get("profile_summary", {}).get("global", {}).get("energy", {})
    if energy:
        console.print(f"Energy (global): producers={energy.get('producer', 0)}, consumers={energy.get('consumer', 0)}")
    unmatched = audit.get("review_queue", {}).get("unmatched_search_total", 0)
    if unmatched:
        console.print(
            f"[yellow]Review queue:[/yellow] {unmatched} cards mention library search without a tutor atom"
        )


@app.command("wizard")
def wizard_cmd(
    seed: Annotated[
        Optional[int],
        typer.Option("--seed", help="RNG seed stored in criteria for later generate steps"),
    ] = None,
) -> None:
    """Run the full deck-building wizard (steps 1–5)."""
    try:
        run_wizard(seed=seed)
    except KeyboardInterrupt:
        console.print("\n[dim]Wizard cancelled.[/dim]")
        raise typer.Exit(130) from None
    except (FileNotFoundError, RuntimeError) as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1) from exc

    console.print(
        "[dim]Use `mtg-deck-tools generate --wizard` to build a deck from these criteria.[/dim]"
    )


@app.command("generate")
def generate_cmd(
    stub: Annotated[
        bool,
        typer.Option("--stub", help="Phase 1 preview only (sample synergy cards)"),
    ] = False,
    wizard: Annotated[
        bool,
        typer.Option("--wizard", help="Run full wizard before generating"),
    ] = False,
    seed: Annotated[
        Optional[int],
        typer.Option("--seed", help="RNG seed for reproducible deck builds"),
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
    strict_budget: Annotated[
        bool,
        typer.Option(
            "--strict-budget",
            help="Exclude unpriced cards and enforce budget cap during generation",
        ),
    ] = False,
    prefer_available: Annotated[
        bool,
        typer.Option(
            "--prefer-available",
            help="Exclude cards below the import-time availability score threshold",
        ),
    ] = False,
    card_price_min: Annotated[
        Optional[float],
        typer.Option("--card-price-min", help="Minimum USD price per card"),
    ] = None,
    card_price_max: Annotated[
        Optional[float],
        typer.Option("--card-price-max", help="Maximum USD price per card"),
    ] = None,
    min_rarity: Annotated[
        str,
        typer.Option(
            "--min-rarity",
            help="Minimum card rarity (common, uncommon, rare, mythic)",
        ),
    ] = "common",
    deck_from: Annotated[
        Optional[Path],
        typer.Option(
            "--from",
            help="Regenerate from a saved .deck.json (criteria and commanders)",
            exists=True,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
    refill_slot: Annotated[
        Optional[str],
        typer.Option(
            "--refill-slot",
            help="When using --from, refill only this slot (e.g. synergy, lands)",
        ),
    ] = None,
) -> None:
    """
    Generate a Commander deck (99-card maindeck + commander metadata).

    Use --wizard for interactive criteria. Use --from to reload a .deck.json.
    Use --stub for the old Phase 1 preview.
    """
    if deck_from and stub:
        console.print("[red]Error:[/red] --from cannot be used with --stub.")
        raise typer.Exit(1)
    if refill_slot and not deck_from:
        console.print("[red]Error:[/red] --refill-slot requires --from.")
        raise typer.Exit(1)

    criteria = None
    if wizard:
        if deck_from:
            console.print(
                "[yellow]Note:[/yellow] --from is ignored when --wizard is set."
            )
        if colors or themes:
            console.print(
                "[yellow]Note:[/yellow] --colors and --themes are ignored when --wizard is set."
            )
        try:
            criteria = run_wizard(seed=seed, db_path=db_path)
        except KeyboardInterrupt:
            console.print("\n[dim]Wizard cancelled.[/dim]")
            raise typer.Exit(130) from None
        except (FileNotFoundError, RuntimeError) as exc:
            console.print(f"[red]Error:[/red] {exc}")
            raise typer.Exit(1) from exc

    color_list = [c.strip().upper() for c in colors.split(",")] if colors else None
    theme_list = [t.strip() for t in themes.split(",")] if themes else None

    if not wizard and not deck_from:
        patch: dict = {"min_rarity": min_rarity}
        if card_price_min is not None:
            patch["card_price_min_usd"] = card_price_min
        if card_price_max is not None:
            patch["card_price_max_usd"] = card_price_max
        if strict_budget:
            patch["strict_budget"] = True
        if prefer_available:
            patch["prefer_available"] = True
        if criteria is None:
            criteria = DeckCriteria(**patch)
        else:
            criteria = criteria.model_copy(update=patch)

    try:
        if deck_from:
            out = run_generate_from_deck(
                deck_from,
                db_path=db_path,
                seed=seed,
                output_dir=output_dir,
                refill_slot=refill_slot,
                strict_budget=strict_budget,
                prefer_available=prefer_available,
            )
        else:
            runner = run_generate_stub if stub else run_generate
            kwargs = dict(
                db_path=db_path,
                seed=seed,
                colors=color_list,
                themes=theme_list,
                criteria=criteria,
                output_dir=output_dir,
            )
            if not stub:
                kwargs["strict_budget"] = strict_budget
                kwargs["prefer_available"] = prefer_available
            out = runner(**kwargs)
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1) from exc

    md_path = out.with_suffix(".md")
    console.print(f"[green]Wrote[/green] {out}")
    console.print(f"[green]Wrote[/green] {md_path}")
    if stub:
        console.print("[dim]Phase 1 stub preview — omit --stub for full slot-filled decks.[/dim]")
    elif deck_from and refill_slot:
        console.print(f"[dim]Refilled slot '{refill_slot}' from {deck_from.name}.[/dim]")
    elif deck_from:
        console.print(f"[dim]Regenerated deck from {deck_from.name}.[/dim]")
    else:
        console.print("[dim]Full maindeck generated. Review warnings in the output files.[/dim]")


if __name__ == "__main__":
    app()
