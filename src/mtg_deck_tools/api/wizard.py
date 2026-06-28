"""Wizard HTTP routes (UX7c)."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.service.dto import (
    CardSearchResult,
    CommanderSearchResult,
    MechanicChoiceResponse,
    PreflightResponse,
    RarityChoiceResponse,
    SlotTemplateDefaultsResponse,
    SynergyContextResponse,
    ThemeChoiceResponse,
    WizardMetaResponse,
)
from mtg_deck_tools.service.wizard_catalog import (
    get_slot_template_defaults,
    get_synergy_context,
    get_wizard_mechanics,
    get_wizard_meta,
    get_wizard_rarities,
    get_wizard_themes,
    run_wizard_preflight,
    search_wizard_commanders,
    search_wizard_cards,
)

router = APIRouter(prefix="/api/v1/wizard", tags=["wizard"])


@router.get("/meta", response_model=WizardMetaResponse)
def wizard_meta(
    db: Annotated[str | None, Query(description="SQLite database path")] = None,
) -> WizardMetaResponse:
    return get_wizard_meta(Path(db) if db else None)


@router.get("/themes", response_model=list[ThemeChoiceResponse])
def wizard_themes() -> list[ThemeChoiceResponse]:
    return get_wizard_themes()


@router.get("/slot-template/defaults", response_model=SlotTemplateDefaultsResponse)
def wizard_slot_template_defaults() -> SlotTemplateDefaultsResponse:
    return get_slot_template_defaults()


@router.get("/mechanics", response_model=list[MechanicChoiceResponse])
def wizard_mechanics() -> list[MechanicChoiceResponse]:
    return get_wizard_mechanics()


@router.post("/synergy-context", response_model=SynergyContextResponse)
def wizard_synergy_context(body: DeckCriteria) -> SynergyContextResponse:
    return get_synergy_context(body)


@router.post("/preflight", response_model=PreflightResponse)
def wizard_preflight(body: DeckCriteria) -> PreflightResponse:
    return run_wizard_preflight(body)


@router.get("/commanders/search", response_model=list[CommanderSearchResult])
def wizard_commanders_search(
    q: Annotated[str, Query(description="Commander name substring")] = "",
    colors: Annotated[list[str], Query(description="WUBRG color filter")] = [],
    color_match: Annotated[str, Query(description="includes or exact")] = "includes",
    card_price_min_usd: Annotated[float | None, Query()] = None,
    card_price_max_usd: Annotated[float | None, Query()] = None,
    budget_usd: Annotated[float | None, Query()] = None,
    strict_budget: Annotated[bool, Query()] = False,
    limit: Annotated[int, Query(ge=1, le=50)] = 15,
    db: Annotated[str | None, Query(description="SQLite database path")] = None,
) -> list[CommanderSearchResult]:
    try:
        return search_wizard_commanders(
            colors=colors,
            name_query=q,
            color_match=color_match,
            card_price_min_usd=card_price_min_usd,
            card_price_max_usd=card_price_max_usd,
            budget_usd=budget_usd,
            strict_budget=strict_budget,
            limit=limit,
            db_path=Path(db) if db else None,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/cards/search", response_model=list[CardSearchResult])
def wizard_cards_search(
    q: Annotated[str, Query(description="Card name substring")] = "",
    colors: Annotated[list[str], Query(description="WUBRG color filter (subset)")] = [],
    limit: Annotated[int, Query(ge=1, le=50)] = 15,
    db: Annotated[str | None, Query(description="SQLite database path")] = None,
) -> list[CardSearchResult]:
    try:
        return search_wizard_cards(
            name_query=q,
            colors=colors or None,
            limit=limit,
            db_path=Path(db) if db else None,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/rarities", response_model=list[RarityChoiceResponse])
def wizard_rarities() -> list[RarityChoiceResponse]:
    return get_wizard_rarities()
