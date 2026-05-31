"""Full deck generation entry point."""

from __future__ import annotations

from pathlib import Path

from mtg_deck_tools.builder.generate_outcome import build_generate_outcome
from mtg_deck_tools.builder.output import write_deck_outputs
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.paths import OUTPUT_DIR

# Re-export for tests and analysis that pin commanders by name.
from mtg_deck_tools.builder.commander_resolve import (  # noqa: F401
    commander_theme_tags,
    fetch_commanders,
    pick_commander,
    require_db,
    resolve_commander_oracle_ids,
)


def run_generate(
    *,
    db_path: Path | None = None,
    seed: int | None = None,
    colors: list[str] | None = None,
    themes: list[str] | None = None,
    slot_template: dict[str, int] | None = None,
    criteria: DeckCriteria | None = None,
    output_dir: Path | None = None,
    strict_budget: bool = False,
    strict_dependencies: bool = False,
    repair_dependencies: bool = False,
    prefer_available: bool = False,
    commander_names: list[str] | None = None,
) -> Path:
    """Build a full 99-card maindeck from criteria and write output files."""
    outcome = build_generate_outcome(
        db_path=db_path,
        seed=seed,
        colors=colors,
        themes=themes,
        slot_template=slot_template,
        criteria=criteria,
        strict_budget=strict_budget,
        strict_dependencies=strict_dependencies,
        repair_dependencies=repair_dependencies,
        prefer_available=prefer_available,
        commander_names=commander_names,
    )

    out_dir = output_dir or OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    placeholder = out_dir / "deck"
    json_path, md_path = write_deck_outputs(
        base_path=placeholder,
        criteria=outcome.criteria,
        commanders=outcome.commanders,
        maindeck=outcome.maindeck,
        identity=outcome.identity,
    )
    return json_path
