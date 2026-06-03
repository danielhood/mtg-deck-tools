"""Effect atom schema for the card dependency engine (D0 contract)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class SearchLibraryPayload(BaseModel):
    """Payload for search_library effect_kind."""

    types: list[str] = Field(default_factory=list)
    subtypes: list[str] = Field(default_factory=list)
    supertypes: list[str] = Field(default_factory=list)
    max_cmc: int | None = None
    min_cmc: int | None = None
    colors: list[str] = Field(default_factory=list)
    card_name: str | None = None
    type_match: str | None = None
    zones: list[str] = Field(default_factory=lambda: ["library"])
    destination: str = "hand"
    any_card: bool = False


class ResourceCounterPayload(BaseModel):
    """Payload for energy_produce / energy_consume / similar resource kinds."""

    resource: str = "energy"
    min_cost: int | None = None
    amount: int | Literal["variable"] | None = "variable"


class TypeFilterPayload(BaseModel):
    """Payload for buff_subtype, whenever_cast_type, etc."""

    types: list[str] = Field(default_factory=list)
    subtypes: list[str] = Field(default_factory=list)
    scope: str | None = None


class EffectAtom(BaseModel):
    """
    One extracted atomic effect on a card face.

    Stored in card_effects.payload as JSON (D1+). effect_kind + payload discriminates shape.
    """

    effect_kind: str
    payload: dict[str, Any]
    confidence: float = 1.0
    source: str
    face_index: int = 0

    def model_dump_row(self) -> dict[str, Any]:
        """Serialize for future card_effects SQLite row."""
        return {
            "effect_kind": self.effect_kind,
            "payload": self.payload,
            "confidence": self.confidence,
            "source": self.source,
            "face_index": self.face_index,
        }


# Known effect_kind values for D0/D1 (pattern id → kind documented in effect-patterns.yaml)
EFFECT_KINDS = frozenset(
    {
        "search_library",
        "energy_produce",
        "energy_consume",
        "experience_produce",
        "experience_consume",
        "blood_produce",
        "blood_consume",
        "plus_one_produce",
        "plus_one_consume",
        "buff_subtype",
        "whenever_cast_type",
        "whenever_cast_enchantment",
        "type_line_aura",
    }
)
