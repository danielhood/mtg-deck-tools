"""Import oracle JSON into SQLite and apply mechanic tags."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable

from mtg_deck_tools.availability.score import record_availability_percentile
from mtg_deck_tools.db.schema import SCHEMA_VERSION, apply_schema
from mtg_deck_tools.import_.normalize import normalize_card
from mtg_deck_tools.effects.extract import EffectExtractor
from mtg_deck_tools.import_.scryfall_bulk import ensure_oracle_cards_json
from mtg_deck_tools.paths import EFFECT_PATTERNS_PATH, TAXONOMY_PATH, resolve_db_path
from mtg_deck_tools.tags.tagger import Tagger, load_taxonomy

CARD_INSERT_SQL = """
INSERT OR REPLACE INTO cards (
    oracle_id, scryfall_id, name, layout, type_line, oracle_text, mana_cost, cmc,
    colors, color_identity, keywords, produced_mana, power, toughness,
    commander_legal, commander_eligible, is_basic_land, partner_kind,
    edhrec_rank, price_usd, price_known, released_at, rarity,
    scryfall_uri, image_uri, set_type, reprint, availability_score
) VALUES (
    :oracle_id, :scryfall_id, :name, :layout, :type_line, :oracle_text, :mana_cost, :cmc,
    :colors, :color_identity, :keywords, :produced_mana, :power, :toughness,
    :commander_legal, :commander_eligible, :is_basic_land, :partner_kind,
    :edhrec_rank, :price_usd, :price_known, :released_at, :rarity,
    :scryfall_uri, :image_uri, :set_type, :reprint, :availability_score
)
"""

TAG_INSERT_SQL = """
INSERT OR REPLACE INTO card_mechanic_tags (oracle_id, tag, layer, source)
VALUES (?, ?, ?, ?)
"""

EFFECT_INSERT_SQL = """
INSERT OR REPLACE INTO card_effects (
    oracle_id, face_index, effect_kind, payload, confidence, source
) VALUES (?, ?, ?, ?, ?, ?)
"""


def run_import(
    *,
    json_path: Path | None = None,
    db_path: Path | None = None,
    taxonomy_path: Path | None = None,
    progress: Callable[[str], None] | None = None,
    auto_download: bool | None = None,
) -> dict[str, int | str]:
    """Load oracle bulk JSON, populate cards, and tag playable cards."""
    log = progress or (lambda _msg: None)
    if json_path is None:
        source = ensure_oracle_cards_json(auto_download=auto_download, progress=log)
    else:
        source = json_path
    db = resolve_db_path(db_path)
    taxonomy = taxonomy_path or TAXONOMY_PATH

    log(f"Loading {source.name}...")
    with source.open(encoding="utf-8") as f:
        raw_cards = json.load(f)

    log(f"Parsed {len(raw_cards):,} oracle cards. Writing database...")
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    apply_schema(conn)

    conn.execute("DELETE FROM card_mechanic_tags")
    conn.execute("DELETE FROM card_effects")
    conn.execute("DELETE FROM cards")

    tag_defs = load_taxonomy(taxonomy)
    tagger = Tagger(tag_defs)
    extractor = EffectExtractor.from_yaml(EFFECT_PATTERNS_PATH)

    inserted = 0
    playable = 0
    tag_rows: list[tuple[str, str, str, str]] = []
    effect_rows: list[tuple[str, int, str, str, float, str]] = []

    for raw in raw_cards:
        row = normalize_card(raw)
        if row is None:
            continue
        if not row.pop("playable"):
            continue
        playable += 1
        conn.execute(CARD_INSERT_SQL, {k: v for k, v in row.items() if k != "playable"})
        inserted += 1

        card_for_tags = {
            "oracle_id": row["oracle_id"],
            "type_line": row["type_line"],
            "oracle_text": row["oracle_text"],
            "keywords": json.loads(row["keywords"]),
        }
        for assignment in tagger.tag_card(card_for_tags):
            tag_rows.append(
                (row["oracle_id"], assignment.tag, assignment.layer, assignment.source)
            )

        for atom in extractor.extract(
            oracle_text=row["oracle_text"],
            type_line=row["type_line"],
        ):
            effect_rows.append(
                (
                    row["oracle_id"],
                    atom.face_index,
                    atom.effect_kind,
                    json.dumps(atom.payload),
                    atom.confidence,
                    atom.source,
                )
            )

    log(f"Applying {len(tag_rows):,} mechanic tags...")
    conn.executemany(TAG_INSERT_SQL, tag_rows)
    log(f"Writing {len(effect_rows):,} card effect atoms...")
    conn.executemany(EFFECT_INSERT_SQL, effect_rows)

    p25 = record_availability_percentile(conn)
    if p25 is not None:
        log(f"Availability p25 threshold: {p25:.1f}")

    now = datetime.now(UTC).isoformat()
    meta = [
        ("schema_version", SCHEMA_VERSION),
        ("imported_at", now),
        ("source_file", str(source)),
        ("source_count", str(len(raw_cards))),
        ("playable_count", str(playable)),
        ("tag_count", str(len(tag_rows))),
        ("effect_count", str(len(effect_rows))),
        ("extraction_version", str(extractor._registry.extraction_version)),
    ]
    conn.executemany(
        "INSERT OR REPLACE INTO import_metadata (key, value) VALUES (?, ?)",
        meta,
    )
    conn.commit()
    conn.close()

    log("Import complete.")
    return {
        "source_file": str(source),
        "source_count": len(raw_cards),
        "playable_count": playable,
        "tag_count": len(tag_rows),
        "effect_count": len(effect_rows),
        "db_path": str(db),
    }
