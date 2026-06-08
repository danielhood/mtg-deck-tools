"""Deck build data structures shared across builder modules."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from mtg_deck_tools.builder.mana_base import ManaBasePlan
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.rules.validate import ValidationResult

if TYPE_CHECKING:
    from mtg_deck_tools.rules.dependencies import DependencyReport
from mtg_deck_tools.wizard.slots import SLOT_FILLER_THEME_TAGS


@dataclass
class DeckCard:
    oracle_id: str
    name: str
    slot: str
    quantity: int
    cmc: float
    mana_cost: str
    type_line: str
    price_usd: float | None
    price_known: bool
    scryfall_uri: str | None
    image_uri: str | None
    mechanic_tags: list[str] = field(default_factory=list)
    oracle_text: str = ""
    color_identity: list[str] = field(default_factory=list)
    produced_mana: list[str] = field(default_factory=list)
    released_at: str | None = None
    power: str | None = None
    toughness: str | None = None
    rarity: str | None = None
    unpriced_classification: str | None = None


@dataclass
class DeckBuildResult:
    cards: list[DeckCard]
    warnings: list[str]
    budget_spent: float
    unpriced_names: list[str]
    mana_base: ManaBasePlan | None = None
    validation: ValidationResult | None = None
    dependency_report: DependencyReport | None = None


def slot_theme_tags(slot: str, criteria: DeckCriteria) -> list[str] | None:
    if slot in SLOT_FILLER_THEME_TAGS:
        return [slot]
    if slot == "synergy" and criteria.themes:
        return list(criteria.themes)
    return None
