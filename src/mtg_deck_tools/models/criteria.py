"""Deck building criteria (wizard output)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DeckCriteria(BaseModel):
    """User selections from the deck wizard — consumed by the builder (Phase 2+)."""

    themes: list[str] = Field(default_factory=list)
    include_mechanics: list[str] = Field(default_factory=list)
    avoid_mechanics: list[str] = Field(default_factory=list)
    colors: list[str] = Field(default_factory=list)
    commander_oracle_ids: list[str] = Field(default_factory=list)
    budget_usd: float | None = None
    slot_template: dict[str, int] = Field(default_factory=dict)
    seed: int | None = None
