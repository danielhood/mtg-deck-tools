"""Full deck build pipeline result (generate / analyze)."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mtg_deck_tools.builder.budget_backfill import _deck_budget_spent
from mtg_deck_tools.builder.commander_resolve import (
    commander_theme_tags,
    pick_commander,
    require_db,
    resolve_commander_oracle_ids,
)
from mtg_deck_tools.builder.deck import DeckBuildResult
from mtg_deck_tools.builder.dependency_repair import repair_dependency_issues
from mtg_deck_tools.builder.dependency_scoring import card_effects_enabled
from mtg_deck_tools.builder.filler import fill_deck
from mtg_deck_tools.builder.mechanic_packages import ensure_included_mechanic_packages
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.paths import DEFAULT_DB_PATH
from mtg_deck_tools.rules.dependencies import (
    DependencyReport,
    dependency_messages,
    validate_dependencies,
)
from mtg_deck_tools.rules.validate import ValidationResult, validate_commander_deck, validation_messages
from mtg_deck_tools.wizard.commanders import CommanderRow, combined_color_identity
from mtg_deck_tools.wizard.slots import load_slot_template_config, validate_slot_template


@dataclass
class GenerateOutcome:
    """Structured result of a full generate pass (with or without writing deck files)."""

    criteria: DeckCriteria
    commanders: list[dict[str, Any]]
    identity: list[str]
    maindeck: DeckBuildResult
    validation: ValidationResult
    dependency_report: DependencyReport
    seed: int | None
    output_json_path: Path | None = None
    output_md_path: Path | None = None

    @property
    def commander_names(self) -> list[str]:
        return [c["name"] for c in self.commanders]

    @property
    def dependency_warning_count(self) -> int:
        return len(self.dependency_report.warnings)

    @property
    def dependency_issue_rule_ids(self) -> list[str]:
        return [i.rule_id for i in self.dependency_report.issues]


def build_generate_outcome(
    *,
    db_path: Path | None = None,
    seed: int | None = None,
    colors: list[str] | None = None,
    themes: list[str] | None = None,
    slot_template: dict[str, int] | None = None,
    criteria: DeckCriteria | None = None,
    strict_budget: bool = False,
    strict_dependencies: bool = False,
    repair_dependencies: bool = False,
    prefer_available: bool = False,
    commander_names: list[str] | None = None,
) -> GenerateOutcome:
    """
    Run fill → validate → dependency report without writing output files.

    Pass ``criteria`` or CLI-style ``colors`` / ``themes``. Optional ``commander_names``
    pins commanders for repeatable analysis runs.
    """
    db = db_path or DEFAULT_DB_PATH
    conn = require_db(db)
    slot_config = load_slot_template_config()

    try:
        if criteria is not None:
            working = criteria.model_copy()
            color_filter = working.colors
            commander_ids = list(working.commander_oracle_ids)
            effective_seed = seed if seed is not None else working.seed
        else:
            working = DeckCriteria(
                themes=themes or [],
                colors=colors or [],
                slot_template=slot_template or dict(slot_config.default),
                seed=seed,
            )
            color_filter = working.colors
            commander_ids = []
            effective_seed = seed

        if commander_names:
            commander_ids = resolve_commander_oracle_ids(conn, commander_names)

        if not working.slot_template:
            working = working.model_copy(update={"slot_template": dict(slot_config.default)})

        slot_errors = validate_slot_template(working.slot_template, slot_config)
        if slot_errors:
            raise RuntimeError("Invalid slot template: " + "; ".join(slot_errors))

        rng = random.Random(effective_seed)
        commanders = pick_commander(
            conn,
            rng,
            color_filter=color_filter,
            commander_ids=commander_ids,
        )

        identity_rows = [
            {
                "oracle_id": c["oracle_id"],
                "name": c["name"],
                "type_line": c["type_line"] or "",
                "color_identity": json.loads(c["color_identity"] or "[]"),
                "partner_kind": c["partner_kind"],
                "scryfall_uri": c["scryfall_uri"],
                "image_uri": c["image_uri"],
                "price_usd": c["price_usd"],
                "price_known": bool(c["price_known"]),
                "released_at": c["released_at"],
                "mana_cost": c["mana_cost"] or "",
                "cmc": float(c["cmc"] or 0),
                "oracle_text": c["oracle_text"] or "",
                "rarity": c["rarity"],
                "power": c["power"],
                "toughness": c["toughness"],
            }
            for c in commanders
        ]
        identity = combined_color_identity(
            [
                CommanderRow(
                    oracle_id=r["oracle_id"],
                    name=r["name"],
                    color_identity=r["color_identity"],
                    partner_kind=r["partner_kind"],
                    edhrec_rank=None,
                )
                for r in identity_rows
            ]
        )

        output_criteria = working.model_copy(
            update={
                "commander_oracle_ids": [c["oracle_id"] for c in commanders],
                "colors": identity,
                "seed": effective_seed,
                "strict_budget": strict_budget or working.strict_budget,
                "strict_dependencies": strict_dependencies or working.strict_dependencies,
                "repair_dependencies": repair_dependencies or working.repair_dependencies,
                "prefer_available": prefer_available or working.prefer_available,
            }
        )

        maindeck = fill_deck(
            conn,
            output_criteria,
            identity=identity,
            commander_oracle_ids=[c["oracle_id"] for c in commanders],
            seed=effective_seed,
        )

        if card_effects_enabled(conn):
            package = ensure_included_mechanic_packages(
                conn,
                maindeck.cards,
                criteria=output_criteria,
                identity=identity,
                commander_oracle_ids=set(output_criteria.commander_oracle_ids),
                commander_theme_tags=commander_theme_tags(
                    conn, output_criteria.commander_oracle_ids
                ),
            )
            if package.swaps:
                maindeck.cards = package.cards
                maindeck.warnings.extend(package.messages)
                maindeck.budget_spent = _deck_budget_spent(maindeck.cards)

        if output_criteria.repair_dependencies and card_effects_enabled(conn):
            repair = repair_dependency_issues(
                conn,
                maindeck.cards,
                criteria=output_criteria,
                identity=identity,
                commanders=identity_rows,
                commander_oracle_ids=set(output_criteria.commander_oracle_ids),
                commander_theme_tags=commander_theme_tags(
                    conn, output_criteria.commander_oracle_ids
                ),
                strict=output_criteria.strict_dependencies,
            )
            if repair.swaps:
                maindeck.cards = repair.cards
                maindeck.warnings.extend(repair.messages)
                maindeck.budget_spent = _deck_budget_spent(maindeck.cards)

        validation = validate_commander_deck(
            conn,
            commanders=identity_rows,
            maindeck=maindeck.cards,
            identity=identity,
            budget_usd=output_criteria.budget_usd,
            budget_spent=maindeck.budget_spent,
            unpriced_count=len(maindeck.unpriced_names),
        )
        maindeck.validation = validation
        maindeck.warnings.extend(validation_messages(validation))

        dependency_report = validate_dependencies(
            conn,
            maindeck=maindeck.cards,
            commanders=identity_rows,
            criteria=output_criteria,
            strict=output_criteria.strict_dependencies,
        )
        maindeck.warnings.extend(dependency_messages(dependency_report))

        return GenerateOutcome(
            criteria=output_criteria,
            commanders=identity_rows,
            identity=identity,
            maindeck=maindeck,
            validation=validation,
            dependency_report=dependency_report,
            seed=effective_seed,
        )
    finally:
        conn.close()
