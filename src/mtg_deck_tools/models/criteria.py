"""Deck building criteria (wizard output)."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class DeckCriteria(BaseModel):
    """User selections from the deck wizard — consumed by the builder (Phase 2+)."""

    themes: list[str] = Field(default_factory=list)
    include_mechanics: list[str] = Field(default_factory=list)
    avoid_mechanics: list[str] = Field(default_factory=list)
    colors: list[str] = Field(default_factory=list)
    commander_oracle_ids: list[str] = Field(default_factory=list)
    budget_usd: float | None = None
    card_price_min_usd: float | None = None
    card_price_max_usd: float | None = None
    strict_budget: bool = False
    slot_template: dict[str, int] = Field(default_factory=dict)
    seed: int | None = None

    @model_validator(mode="after")
    def _card_price_range_valid(self) -> DeckCriteria:
        min_p = self.card_price_min_usd
        max_p = self.card_price_max_usd
        if min_p is not None and min_p < 0:
            raise ValueError("card_price_min_usd must be >= 0")
        if max_p is not None and max_p <= 0:
            raise ValueError("card_price_max_usd must be > 0")
        if min_p is not None and max_p is not None and min_p > max_p:
            raise ValueError("card_price_min_usd cannot exceed card_price_max_usd")
        return self
