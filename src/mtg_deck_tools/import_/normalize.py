"""Normalize Scryfall card objects for storage."""

from __future__ import annotations

import json
from typing import Any

from mtg_deck_tools.rules.commander import (
    detect_partner_kind,
    is_commander_eligible,
    is_playable_card,
)


def _join_faces(card: dict[str, Any], field: str, sep: str = "\n//\n") -> str:
    faces = card.get("card_faces") or []
    parts = [f.get(field, "") or "" for f in faces]
    return sep.join(p for p in parts if p)


def _merge_colors(card: dict[str, Any]) -> list[str]:
    if card.get("colors"):
        return list(card["colors"])
    faces = card.get("card_faces") or []
    colors: list[str] = []
    for face in faces:
        colors.extend(face.get("colors") or [])
    return sorted(set(colors), key=lambda c: "WUBRG".index(c) if c in "WUBRG" else 99)


def _merge_keywords(card: dict[str, Any]) -> list[str]:
    base = list(card.get("keywords") or [])
    for face in card.get("card_faces") or []:
        base.extend(face.get("keywords") or [])
    return sorted(set(base))


def normalize_card(raw: dict[str, Any]) -> dict[str, Any] | None:
    """Transform a Scryfall oracle card into a flat row dict for SQLite."""
    layout = raw.get("layout") or "normal"
    lang = raw.get("lang") or "en"
    legalities = raw.get("legalities") or {}
    commander_legal = legalities.get("commander") == "legal"

    type_line = raw.get("type_line") or _join_faces(raw, "type_line", " // ")
    oracle_text = raw.get("oracle_text") or _join_faces(raw, "oracle_text")
    mana_cost = raw.get("mana_cost") or _join_faces(raw, "mana_cost", "")

    color_identity = raw.get("color_identity")
    if not color_identity and raw.get("card_faces"):
        ids: list[str] = []
        for face in raw["card_faces"]:
            ids.extend(face.get("color_identity") or [])
        color_identity = sorted(set(ids), key=lambda c: "WUBRG".index(c) if c in "WUBRG" else 99)

    keywords = _merge_keywords(raw)
    colors = _merge_colors(raw)

    playable = is_playable_card(
        layout=layout,
        lang=lang,
        commander_legal=commander_legal,
    )

    prices = raw.get("prices") or {}
    usd_raw = prices.get("usd")
    price_usd: float | None = None
    price_known = 0
    if usd_raw is not None:
        try:
            price_usd = float(usd_raw)
            price_known = 1
        except (TypeError, ValueError):
            pass

    image_uris = raw.get("image_uris") or {}
    if not image_uris and raw.get("card_faces"):
        image_uris = (raw["card_faces"][0].get("image_uris") or {})

    cmc = raw.get("cmc")
    if cmc is None:
        cmc = 0.0

    is_basic = type_line.startswith("Basic Land")

    row = {
        "oracle_id": raw["oracle_id"],
        "scryfall_id": raw.get("id"),
        "name": raw["name"],
        "layout": layout,
        "type_line": type_line,
        "oracle_text": oracle_text or "",
        "mana_cost": mana_cost or "",
        "cmc": float(cmc),
        "colors": json.dumps(colors),
        "color_identity": json.dumps(list(color_identity or [])),
        "keywords": json.dumps(keywords),
        "produced_mana": json.dumps(raw.get("produced_mana") or []),
        "power": raw.get("power") or _join_faces(raw, "power", "/"),
        "toughness": raw.get("toughness") or _join_faces(raw, "toughness", "/"),
        "commander_legal": 1 if commander_legal else 0,
        "commander_eligible": 1 if is_commander_eligible(type_line, oracle_text or "") else 0,
        "is_basic_land": 1 if is_basic else 0,
        "partner_kind": detect_partner_kind(oracle_text or "", keywords),
        "edhrec_rank": raw.get("edhrec_rank"),
        "price_usd": price_usd,
        "price_known": price_known,
        "released_at": raw.get("released_at"),
        "rarity": raw.get("rarity"),
        "scryfall_uri": raw.get("scryfall_uri"),
        "image_uri": image_uris.get("normal"),
        "set_type": raw.get("set_type"),
        "reprint": 1 if raw.get("reprint") else 0,
        "playable": playable,
    }
    return row
