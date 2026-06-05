"""Request/response DTOs for the service layer and HTTP API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from mtg_deck_tools.models.criteria import DeckCriteria


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str


class TopTagRow(BaseModel):
    tag: str
    layer: str
    n: int


class DatabaseStatsResponse(BaseModel):
    db_path: str
    metadata: dict[str, str] = Field(default_factory=dict)
    total_cards: int
    commander_eligible: int
    with_partner: int
    tag_assignments: int
    distinct_tags: int
    effect_rows: int = 0
    distinct_effect_kinds: int = 0
    top_tags: list[TopTagRow] = Field(default_factory=list)


class ImportRequest(BaseModel):
    json_path: str | None = None
    db_path: str | None = None


class ImportResponse(BaseModel):
    source_file: str
    source_count: int
    playable_count: int
    tag_count: int
    effect_count: int
    db_path: str


class GenerateRequest(BaseModel):
    """Criteria-based deck generation (wizard-equivalent when criteria is complete)."""

    criteria: DeckCriteria | None = None
    colors: list[str] | None = None
    themes: list[str] | None = None
    seed: int | None = None
    db_path: str | None = None
    output_dir: str | None = None
    stub: bool = False
    strict_budget: bool = False
    strict_dependencies: bool = False
    repair_dependencies: bool = False
    prefer_available: bool = False
    commander_names: list[str] | None = None


class GenerateFromDeckRequest(BaseModel):
    """Regenerate from an existing .deck.json document (API) or server path (CLI)."""

    deck_path: str | None = None
    deck: dict[str, Any] | None = None
    seed: int | None = None
    db_path: str | None = None
    output_dir: str | None = None
    refill_slot: str | None = None
    strict_budget: bool = False
    strict_dependencies: bool = False
    repair_dependencies: bool = False
    prefer_available: bool = False


class GenerateResponse(BaseModel):
    json_path: str
    md_path: str
    deck: dict[str, Any] | None = None
