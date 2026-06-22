"""Typer CLI for mtg-deck-tools."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.table import Table

from mtg_deck_tools import __version__
from mtg_deck_tools.analysis.matrix import DEFAULT_MATRIX_PATH
from mtg_deck_tools.analysis.runner import run_analysis_suite
from mtg_deck_tools.builder.deck_load import load_deck_criteria_for_wizard
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.effects.audit import run_audit_to_disk
from mtg_deck_tools.api.serve import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    run_server,
    serve_config_from_options,
)
from mtg_deck_tools.paths import DEFAULT_DB_PATH, DEPENDENCY_RESOURCES_DIR, resolve_db_path
from mtg_deck_tools.service import (
    GenerateFromDeckRequest,
    generate_deck_cli,
    generate_deck_from_saved,
    get_database_stats,
    import_oracle_cards,
    ensure_cards_database,
    run_interactive_wizard,
)

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


@app.command("serve")
def serve_cmd(
    host: Annotated[
        Optional[str],
        typer.Option(
            "--host",
            help=f"Bind address (default: {DEFAULT_HOST} or MTG_SERVE_HOST)",
        ),
    ] = None,
    port: Annotated[
        Optional[int],
        typer.Option(
            "--port",
            help=f"Listen port (default: {DEFAULT_PORT} or MTG_SERVE_PORT)",
        ),
    ] = None,
    with_ui: Annotated[
        bool,
        typer.Option(
            "--with-ui",
            help="Serve built SPA from packages/web/dist (or --ui-dir)",
        ),
    ] = False,
    ui_dir: Annotated[
        Optional[Path],
        typer.Option(
            "--ui-dir",
            help="Override static UI directory (implies bundled UI mount)",
        ),
    ] = None,
    db_path: Annotated[
        Optional[Path],
        typer.Option(
            "--db",
            help="Default SQLite path for API requests (also sets MTG_DB_PATH)",
        ),
    ] = None,
    reload: Annotated[
        bool,
        typer.Option("--reload", help="Restart on code changes (development)"),
    ] = False,
) -> None:
    """Start the HTTP API (and optionally the built web UI)."""
    try:
        config = serve_config_from_options(
            host=host,
            port=port,
            reload=reload,
            with_ui=with_ui,
            ui_dir=ui_dir,
            db_path=db_path,
        )
    except ValueError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1) from exc

    if config.static_dir is not None and not config.static_dir.is_dir():
        console.print(f"[red]Web UI build not found:[/red] {config.static_dir}")
        console.print(
            "[dim]Build the SPA (see docs/packages/web/README.md) or omit --with-ui.[/dim]"
        )
        raise typer.Exit(1)

    db = config.db_path or resolve_db_path()
    if not db.exists():
        console.print("[yellow]Card database missing — downloading and importing...[/yellow]")
        try:
            ensure_cards_database(
                db_path=config.db_path,
                progress=lambda msg: console.print(msg),
            )
        except (FileNotFoundError, RuntimeError) as exc:
            console.print(f"[red]Bootstrap failed:[/red] {exc}")
            console.print(
                "[dim]Set MTG_AUTO_DOWNLOAD=0 to skip automatic download, "
                "or run `mtg-deck-tools import` manually.[/dim]"
            )
            raise typer.Exit(1) from exc

    console.print(
        f"[green]Starting API[/green] http://{config.host}:{config.port}/health"
    )
    if config.static_dir is not None:
        console.print(f"[green]Serving UI[/green] from {config.static_dir}")
    if config.db_path is not None:
        console.print(f"[dim]Default database:[/dim] {config.db_path}")
    elif db_path is None:
        console.print(
            "[dim]Default database: data/cards.db (override with --db or MTG_DB_PATH)[/dim]"
        )

    try:
        run_server(config)
    except KeyboardInterrupt:
        console.print("\n[dim]Server stopped.[/dim]")
        raise typer.Exit(0) from None
    except SystemExit as exc:
        if exc.code and exc.code != 0:
            message = exc.args[0] if exc.args else str(exc.code)
            console.print(f"[red]Error:[/red] {message}")
        raise


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
    no_download: Annotated[
        bool,
        typer.Option(
            "--no-download",
            help="Do not download oracle bulk data from Scryfall when no local JSON exists",
        ),
    ] = False,
) -> None:
    """Import Scryfall oracle cards and apply mechanic tags."""
    def progress(msg: str) -> None:
        console.print(msg)

    try:
        result = import_oracle_cards(
            json_path=json_path,
            db_path=db_path,
            progress=progress,
            auto_download=False if no_download else None,
        )
    except FileNotFoundError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1) from exc
    except RuntimeError as exc:
        console.print(f"[red]Download failed:[/red] {exc}")
        raise typer.Exit(1) from exc

    table = Table(title="Import summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value")
    for key, value in result.model_dump().items():
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

    try:
        stats = get_database_stats(path)
    except FileNotFoundError:
        console.print(f"[red]Database not found:[/red] {path}\nRun: mtg-deck-tools import")
        raise typer.Exit(1)

    table = Table(title=f"Database — {path}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value")
    table.add_row("Playable cards", str(stats.total_cards))
    table.add_row("Commander-eligible", str(stats.commander_eligible))
    table.add_row("With partner ability", str(stats.with_partner))
    table.add_row("Tag assignments", str(stats.tag_assignments))
    table.add_row("Distinct tags", str(stats.distinct_tags))
    if stats.effect_rows:
        table.add_row("Effect atom rows", str(stats.effect_rows))
        table.add_row("Distinct effect kinds", str(stats.distinct_effect_kinds))
    for key, value in stats.metadata.items():
        table.add_row(key, value)
    console.print(table)

    if stats.top_tags:
        tag_table = Table(title="Top tags")
        tag_table.add_column("Tag")
        tag_table.add_column("Layer")
        tag_table.add_column("Cards", justify="right")
        for row in stats.top_tags:
            tag_table.add_row(row.tag, row.layer, str(row.n))
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
    deck_from: Annotated[
        Optional[Path],
        typer.Option(
            "--from",
            help="Pre-fill wizard from a saved .deck.json (criteria and commanders)",
            exists=True,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
) -> None:
    """Run the full deck-building wizard (steps 1–6)."""
    initial_criteria = None
    if deck_from:
        try:
            initial_criteria = load_deck_criteria_for_wizard(deck_from)
        except (FileNotFoundError, ValueError) as exc:
            console.print(f"[red]Error:[/red] {exc}")
            raise typer.Exit(1) from exc

    try:
        run_interactive_wizard(
            seed=seed,
            initial_criteria=initial_criteria,
            prepopulated_from=deck_from,
        )
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
    strict_dependencies: Annotated[
        bool,
        typer.Option(
            "--strict-dependencies",
            help=(
                "Exclude dead tutors and unsupported dependency picks during fill; "
                "post-build dependency issues are failures"
            ),
        ),
    ] = False,
    repair_dependencies: Annotated[
        bool,
        typer.Option(
            "--repair-dependencies",
            help="After fill, swap flex/synergy cards to fix dependency warnings when possible",
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
    if wizard and refill_slot:
        console.print("[red]Error:[/red] --refill-slot cannot be used with --wizard.")
        raise typer.Exit(1)

    criteria = None
    wizard_initial: DeckCriteria | None = None
    if wizard:
        if deck_from:
            try:
                wizard_initial = load_deck_criteria_for_wizard(deck_from)
            except (FileNotFoundError, ValueError) as exc:
                console.print(f"[red]Error:[/red] {exc}")
                raise typer.Exit(1) from exc
        if colors or themes:
            console.print(
                "[yellow]Note:[/yellow] --colors and --themes are ignored when --wizard is set."
            )
        try:
            criteria = run_interactive_wizard(
                seed=seed,
                db_path=db_path,
                initial_criteria=wizard_initial,
                prepopulated_from=deck_from,
            )
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
        if strict_dependencies:
            patch["strict_dependencies"] = True
        if repair_dependencies:
            patch["repair_dependencies"] = True
        if prefer_available:
            patch["prefer_available"] = True
        if criteria is None:
            criteria = DeckCriteria(**patch)
        else:
            criteria = criteria.model_copy(update=patch)

    try:
        if deck_from and not wizard:
            response = generate_deck_from_saved(
                GenerateFromDeckRequest(
                    deck_path=str(deck_from),
                    db_path=str(db_path) if db_path else None,
                    output_dir=str(output_dir) if output_dir else None,
                    seed=seed,
                    refill_slot=refill_slot,
                    strict_budget=strict_budget,
                    strict_dependencies=strict_dependencies,
                    repair_dependencies=repair_dependencies,
                    prefer_available=prefer_available,
                ),
            )
            out = Path(response.json_path)
            md_path = Path(response.md_path)
        else:
            result = generate_deck_cli(
                stub=stub,
                db_path=db_path,
                seed=seed,
                colors=color_list,
                themes=theme_list,
                criteria=criteria,
                output_dir=output_dir,
                strict_budget=strict_budget,
                strict_dependencies=strict_dependencies,
                repair_dependencies=repair_dependencies,
                prefer_available=prefer_available,
            )
            out = result.json_path
            md_path = result.md_path
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1) from exc

    console.print(f"[green]Wrote[/green] {out}")
    console.print(f"[green]Wrote[/green] {md_path}")
    if stub:
        console.print("[dim]Phase 1 stub preview — omit --stub for full slot-filled decks.[/dim]")
    elif deck_from and wizard:
        console.print(
            f"[dim]Generated deck from wizard (pre-filled from {deck_from.name}).[/dim]"
        )
    elif deck_from and refill_slot:
        console.print(f"[dim]Refilled slot '{refill_slot}' from {deck_from.name}.[/dim]")
    elif deck_from:
        console.print(f"[dim]Regenerated deck from {deck_from.name}.[/dim]")
    else:
        console.print("[dim]Full maindeck generated. Review warnings in the output files.[/dim]")


analyze_app = typer.Typer(
    help="Run repeatable deck validation and dependency analysis suites.",
    no_args_is_help=True,
)
app.add_typer(analyze_app, name="analyze")


@analyze_app.command("run")
def analyze_run_cmd(
    matrix: Annotated[
        Optional[Path],
        typer.Option(
            "--matrix",
            help="Scenario matrix YAML (default: config/dogfood-matrix.yaml)",
        ),
    ] = None,
    db_path: Annotated[
        Optional[Path],
        typer.Option("--db", help="SQLite database path"),
    ] = None,
    output_dir: Annotated[
        Optional[Path],
        typer.Option(
            "--output-dir",
            "-o",
            help="Report directory (default: output/analysis-<timestamp>)",
        ),
    ] = None,
    write_decks: Annotated[
        bool,
        typer.Option(
            "--write-decks",
            help="Also write .deck.json and .md under <output-dir>/decks/",
        ),
    ] = False,
    fail_on_expect: Annotated[
        bool,
        typer.Option(
            "--fail-on-expect",
            help="Exit 1 if any scenario fails its expect block",
        ),
    ] = False,
) -> None:
    """Generate decks from a matrix and write summary + per-case JSON reports."""
    matrix_path = matrix or DEFAULT_MATRIX_PATH
    if not matrix_path.exists():
        console.print(f"[red]Matrix not found:[/red] {matrix_path}")
        raise typer.Exit(1)

    def progress(msg: str) -> None:
        console.print(msg)

    try:
        result = run_analysis_suite(
            matrix_path=matrix_path,
            db_path=db_path,
            output_dir=output_dir,
            write_decks=write_decks,
            progress=progress,
        )
    except FileNotFoundError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1) from exc

    s = result.summary
    console.print(f"\n[green]Analysis complete.[/green] {result.output_dir}")
    table = Table(title="Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value")
    table.add_row("Scenarios", str(s.scenario_count))
    table.add_row("Expect passed", str(s.scenarios_passed))
    table.add_row("Expect failed", str(s.scenarios_failed))
    table.add_row("Errors", str(s.scenarios_errored))
    table.add_row("Validation passed", str(s.validation_pass_count))
    table.add_row("Dependency warnings", str(s.total_dependency_warnings))
    table.add_row("Inappropriate (heuristic)", str(s.inappropriate_warning_count))
    if s.false_positive_rate is not None:
        table.add_row("False-positive rate", f"{s.false_positive_rate:.1%}")
    console.print(table)
    console.print(f"Summary: {result.summary_json_path}")
    console.print(f"Markdown: {result.summary_md_path}")

    if fail_on_expect and (s.scenarios_failed > 0 or s.scenarios_errored > 0):
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
