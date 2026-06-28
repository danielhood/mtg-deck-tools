"""Swap constraint models for UX12 advanced iterate."""

from __future__ import annotations

from pydantic import BaseModel, Field


class EffectRoleConstraint(BaseModel):
    profile_id: str
    role: str


class SwapConstraints(BaseModel):
    type_lines_any: list[str] = Field(default_factory=list)
    type_lines_none: list[str] = Field(default_factory=list)
    colors_all: list[str] = Field(default_factory=list)
    rarities: list[str] = Field(default_factory=list)
    max_price_usd: float | None = None
    effect_role: EffectRoleConstraint | None = None
    replacement_oracle_id: str | None = None
    slot_policy: str = "same"
