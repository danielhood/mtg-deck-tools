"""Load saved .deck.json files for regeneration."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from mtg_deck_tools.builder.deck import DeckCard
from mtg_deck_tools.models.criteria import DeckCriteria

SUPPORTED_SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class LoadedDeckFile:
    path: Path
    criteria: DeckCriteria
    commanders: list[dict]
    cards: list[DeckCard]


def _deck_card_from_saved(entry: dict) -> DeckCard:
    return DeckCard(
        oracle_id=entry["oracle_id"],
        name=entry["name"],
        slot=entry["slot"],
        quantity=int(entry.get("quantity", 1)),
        cmc=float(entry.get("cmc", 0)),
        mana_cost=entry.get("mana_cost") or "",
        type_line=entry.get("type_line") or "",
        price_usd=entry.get("price_usd"),
        price_known=bool(entry.get("price_known", entry.get("price_usd") is not None)),
        scryfall_uri=entry.get("scryfall_uri"),
        image_uri=entry.get("image_uri"),
        mechanic_tags=list(entry.get("mechanic_tags") or []),
        oracle_text=entry.get("oracle_text") or "",
        produced_mana=list(entry.get("produced_mana") or []),
        released_at=entry.get("released_at"),
        rarity=entry.get("rarity"),
        power=entry.get("power"),
        toughness=entry.get("toughness"),
    )


def load_deck_json(path: Path) -> LoadedDeckFile:
    """Parse a .deck.json file written by write_deck_outputs."""
    if not path.exists():
        raise FileNotFoundError(f"Deck file not found: {path}")
    if path.suffix != ".json":
        raise ValueError(f"Expected a .deck.json file, got: {path.name}")

    data = json.loads(path.read_text(encoding="utf-8"))
    version = data.get("schema_version")
    if version != SUPPORTED_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported schema_version {version!r}; expected {SUPPORTED_SCHEMA_VERSION!r}"
        )

    criteria = DeckCriteria.model_validate(data["criteria"])
    commanders = list(data.get("commanders") or [])
    commander_ids = [c["oracle_id"] for c in commanders if c.get("oracle_id")]
    if commander_ids and not criteria.commander_oracle_ids:
        criteria = criteria.model_copy(update={"commander_oracle_ids": commander_ids})

    cards = [_deck_card_from_saved(entry) for entry in data.get("cards") or []]
    if not cards:
        raise ValueError("Deck file contains no maindeck cards.")

    return LoadedDeckFile(path=path, criteria=criteria, commanders=commanders, cards=cards)
