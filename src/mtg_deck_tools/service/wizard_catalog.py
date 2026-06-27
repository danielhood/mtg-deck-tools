"""Wizard catalog and validation facades for the web build flow (UX7c)."""

from __future__ import annotations

from pathlib import Path

from mtg_deck_tools import __version__
from mtg_deck_tools.db.connection import connect
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.paths import resolve_db_path
from mtg_deck_tools.rules.criteria_linter import lint_criteria
from mtg_deck_tools.rules.rarity import RARITY_ORDER, format_min_rarity_display
from mtg_deck_tools.service.dto import (
    ActivatedProfileResponse,
    CommanderSearchResult,
    CriteriaWarningResponse,
    FocusLevelOption,
    MechanicChoiceResponse,
    PreflightResponse,
    RarityChoiceResponse,
    SlotBoundsResponse,
    SlotTemplateDefaultsResponse,
    SynergyContextResponse,
    ThemeChoiceResponse,
    WizardBuildStep,
    WizardMetaResponse,
)
from mtg_deck_tools.service.stats import get_database_stats
from mtg_deck_tools.wizard.commanders import CommanderRow, search_commanders
from mtg_deck_tools.wizard.dependencies import FOCUS_LEVELS, activated_profiles_for_wizard
from mtg_deck_tools.wizard.mechanics import keyword_mechanic_choices
from mtg_deck_tools.wizard.slots import load_slot_template_config, slot_template_total
from mtg_deck_tools.wizard.themes import archetype_choices

_FOCUS_LEVEL_OPTIONS: tuple[tuple[str | None, str, int], ...] = (
    (None, "Default", 1),
    ("incidental", "Incidental", 2),
    ("supported", "Supported", 3),
    ("focused", "Focused", 4),
    ("engine", "Engine", 5),
)

WIZARD_BUILD_STEPS: tuple[WizardBuildStep, ...] = (
    WizardBuildStep(number=1, route="/build/1", label="Themes & slot template"),
    WizardBuildStep(number=2, route="/build/2", label="Include / avoid mechanics"),
    WizardBuildStep(number=3, route="/build/3", label="Synergy & dependencies"),
    WizardBuildStep(number=4, route="/build/4", label="Colors"),
    WizardBuildStep(number=5, route="/build/5", label="Budget & card prices"),
    WizardBuildStep(number=6, route="/build/6", label="Commander"),
    WizardBuildStep(number=7, route="/build/7", label="Card rarity"),
)


def get_wizard_meta(db_path: Path | None = None) -> WizardMetaResponse:
    path = resolve_db_path(db_path)
    db_ready = path.exists()
    total_cards: int | None = None
    if db_ready:
        stats = get_database_stats(path)
        total_cards = stats.total_cards
    return WizardMetaResponse(
        version=__version__,
        db_ready=db_ready,
        db_path=str(path.resolve()),
        total_cards=total_cards,
        steps=list(WIZARD_BUILD_STEPS),
        review_route="/build/review",
        result_route="/build/result",
    )


def get_wizard_themes() -> list[ThemeChoiceResponse]:
    return [
        ThemeChoiceResponse(id=choice.id, description=choice.description)
        for choice in archetype_choices()
    ]


def get_slot_template_defaults() -> SlotTemplateDefaultsResponse:
    config = load_slot_template_config()
    default = dict(config.default)
    maindeck_total = slot_template_total(default)
    return SlotTemplateDefaultsResponse(
        default=default,
        bounds={
            slot: SlotBoundsResponse(min=spec.min, max=spec.max)
            for slot, spec in config.bounds.items()
        },
        order=list(config.order),
        labels=dict(config.labels),
        maindeck_total=maindeck_total,
        deck_total=maindeck_total + 1,
        commander_slots=1,
    )


def get_wizard_mechanics() -> list[MechanicChoiceResponse]:
    return [
        MechanicChoiceResponse(id=choice.id, description=choice.description)
        for choice in keyword_mechanic_choices()
    ]


def get_synergy_context(criteria: DeckCriteria) -> SynergyContextResponse:
    focus_options = [
        FocusLevelOption(value=level, label=label, dots=dots)
        for level, label, dots in _FOCUS_LEVEL_OPTIONS
    ]
    profiles = [
        ActivatedProfileResponse(
            profile_id=entry.profile_id,
            prompt_label=entry.prompt_label,
            current_level=criteria.mechanic_focus.get(entry.profile_id),
            focus_options=focus_options,
        )
        for entry in activated_profiles_for_wizard(criteria)
    ]
    return SynergyContextResponse(
        activated_profiles=profiles,
        focus_levels=list(FOCUS_LEVELS),
    )


def run_wizard_preflight(criteria: DeckCriteria) -> PreflightResponse:
    warnings = lint_criteria(criteria)
    return PreflightResponse(
        warnings=[
            CriteriaWarningResponse(rule_id=warning.rule_id, message=warning.message)
            for warning in warnings
        ]
    )


def get_wizard_rarities() -> list[RarityChoiceResponse]:
    return [
        RarityChoiceResponse(id=rarity, label=format_min_rarity_display(rarity))
        for rarity in RARITY_ORDER
    ]


def search_wizard_commanders(
    *,
    colors: list[str],
    name_query: str = "",
    color_match: str = "includes",
    card_price_min_usd: float | None = None,
    card_price_max_usd: float | None = None,
    budget_usd: float | None = None,
    strict_budget: bool = False,
    limit: int = 15,
    db_path: Path | None = None,
) -> list[CommanderSearchResult]:
    path = resolve_db_path(db_path)
    if not path.exists():
        raise FileNotFoundError(f"Database not found: {path}")

    if color_match not in {"exact", "includes"}:
        raise ValueError("color_match must be 'exact' or 'includes'")

    conn = connect(path)
    try:
        rows = search_commanders(
            conn,
            colors=colors,
            name_query=name_query,
            limit=limit,
            color_match=color_match,  # type: ignore[arg-type]
            card_price_min_usd=card_price_min_usd,
            card_price_max_usd=card_price_max_usd,
            budget_usd=budget_usd,
            strict_budget=strict_budget,
        )
    finally:
        conn.close()
    return [_commander_to_result(row) for row in rows]


def _commander_to_result(row: CommanderRow) -> CommanderSearchResult:
    return CommanderSearchResult(
        oracle_id=row.oracle_id,
        name=row.name,
        type_line=row.type_line,
        color_identity=row.color_identity,
        partner_kind=row.partner_kind,
        edhrec_rank=row.edhrec_rank,
        price_usd=row.price_usd,
        price_known=row.price_known,
        released_at=row.released_at,
        image_uri=row.image_uri,
        rarity=row.rarity,
    )
