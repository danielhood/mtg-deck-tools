"""Request/response DTOs for the service layer and HTTP API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.models.swap_constraints import SwapConstraints


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
    """Web generate returns ``id`` + ``deck``; CLI / legacy callers may include path fields."""

    id: str | None = None
    json_path: str | None = None
    md_path: str | None = None
    deck: dict[str, Any] | None = None
    markdown: str | None = None


class DeckLibraryEntry(BaseModel):
    id: str
    name: str
    saved_at: str
    commander_names: list[str] = Field(default_factory=list)
    commander_image_uri: str | None = None
    colors: list[str] = Field(default_factory=list)
    themes: list[str] = Field(default_factory=list)
    estimated_price_usd: float | None = None


class DeckLibraryDetailResponse(BaseModel):
    id: str
    name: str
    saved_at: str
    deck: dict[str, Any]


class PatchDeckRequest(BaseModel):
    name: str | None = None
    deck: dict[str, Any] | None = None


class RefillSlotRequest(BaseModel):
    slot: str
    seed: int | None = None
    constraints: SwapConstraints | None = None
    force_validation_override: bool = False


class SwapCardsRequest(BaseModel):
    oracle_ids: list[str]
    seed: int | None = None
    constraints: SwapConstraints | None = None
    strategy_id: str | None = None
    preview_limit: int | None = Field(default=None, ge=1, le=20)
    force_validation_override: bool = False


class ValidationErrorItem(BaseModel):
    code: str
    message: str


class SwapPreviewCandidateResponse(BaseModel):
    oracle_id: str
    name: str
    mana_cost: str
    price_usd: float | None = None
    rarity: str | None = None


class SwapPreviewPositionResponse(BaseModel):
    from_oracle_id: str
    from_name: str
    slot: str
    candidates: list[SwapPreviewCandidateResponse] = Field(default_factory=list)


class SwapPreviewResponse(BaseModel):
    candidates_by_position: list[SwapPreviewPositionResponse] = Field(default_factory=list)


class SwapStrategyResponse(BaseModel):
    id: str
    label: str
    default: bool = False


class SwapPlaybooksResponse(BaseModel):
    rule_id: str
    strategies: list[SwapStrategyResponse] = Field(default_factory=list)


class SwapRecordResponse(BaseModel):
    slot: str
    from_oracle_id: str
    from_name: str
    to_oracle_id: str
    to_name: str


class SwapCardsResponse(BaseModel):
    id: str
    deck: dict[str, Any]
    swaps: list[SwapRecordResponse] = Field(default_factory=list)


class WizardBuildStep(BaseModel):
    number: int
    route: str
    label: str


class WizardMetaResponse(BaseModel):
    version: str
    db_ready: bool
    db_path: str
    total_cards: int | None = None
    steps: list[WizardBuildStep] = Field(default_factory=list)
    review_route: str = "/build/review"
    result_route: str = "/build/result"


class ThemeChoiceResponse(BaseModel):
    id: str
    description: str


class MechanicChoiceResponse(BaseModel):
    id: str
    description: str


class SlotBoundsResponse(BaseModel):
    min: int
    max: int


class SlotTemplateDefaultsResponse(BaseModel):
    default: dict[str, int]
    bounds: dict[str, SlotBoundsResponse]
    order: list[str]
    labels: dict[str, str]
    maindeck_total: int
    deck_total: int
    commander_slots: int = 1


class FocusLevelOption(BaseModel):
    value: str | None
    label: str
    dots: int


class ActivatedProfileResponse(BaseModel):
    profile_id: str
    prompt_label: str
    current_level: str | None = None
    focus_options: list[FocusLevelOption] = Field(default_factory=list)


class SynergyContextResponse(BaseModel):
    activated_profiles: list[ActivatedProfileResponse] = Field(default_factory=list)
    focus_levels: list[str] = Field(default_factory=list)


class CriteriaWarningResponse(BaseModel):
    rule_id: str
    message: str


class PreflightResponse(BaseModel):
    warnings: list[CriteriaWarningResponse] = Field(default_factory=list)


class RarityChoiceResponse(BaseModel):
    id: str
    label: str


class CommanderSearchResult(BaseModel):
    oracle_id: str
    name: str
    type_line: str = ""
    color_identity: list[str] = Field(default_factory=list)
    partner_kind: str | None = None
    edhrec_rank: int | None = None
    price_usd: float | None = None
    price_known: bool = False
    released_at: str | None = None
    image_uri: str | None = None
    rarity: str | None = None


class CardSearchResult(BaseModel):
    oracle_id: str
    name: str
    type_line: str = ""
    mana_cost: str = ""
    color_identity: list[str] = Field(default_factory=list)
    price_usd: float | None = None
    price_known: bool = False
    image_uri: str | None = None
    rarity: str | None = None
