"""Phase 1 generate stub — validates DB and demonstrates seeded sampling."""

from __future__ import annotations

import json
import random
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from mtg_deck_tools.db.connection import connect
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.paths import DEFAULT_DB_PATH, OUTPUT_DIR


def _require_db(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        raise FileNotFoundError(
            f"Database not found at {db_path}. Run: mtg-deck-tools import"
        )
    return connect(db_path)


def run_generate_stub(
    *,
    db_path: Path | None = None,
    seed: int | None = None,
    colors: list[str] | None = None,
    themes: list[str] | None = None,
    slot_template: dict[str, int] | None = None,
    criteria: DeckCriteria | None = None,
    output_dir: Path | None = None,
) -> Path:
    """
    Phase 1 stub: sample a commander and cards matching optional filters.
    Full wizard and 100-card slot filling arrive in Phase 2.
    """
    db = db_path or DEFAULT_DB_PATH
    conn = _require_db(db)
    rng = random.Random(seed)

    if criteria is not None:
        color_filter = criteria.colors
        theme_filter = criteria.themes
        slot_counts = criteria.slot_template
        seed = criteria.seed if criteria.seed is not None else seed
    else:
        color_filter = colors or []
        theme_filter = themes or []
        slot_counts = slot_template or {}

    commander_sql = """
        SELECT oracle_id, name, color_identity, partner_kind, scryfall_uri
        FROM cards
        WHERE commander_eligible = 1
    """
    params: list = []
    if color_filter:
        # JSON array contains all selected colors (commander identity superset of pick)
        for color in color_filter:
            commander_sql += " AND color_identity LIKE ?"
            params.append(f'%"{color}"%')
    commanders = conn.execute(commander_sql, params).fetchall()
    if not commanders:
        conn.close()
        raise RuntimeError("No commanders match the given filters. Try different --colors.")

    commander = rng.choice(commanders)
    identity = json.loads(commander["color_identity"])

    synergy_sql = """
        SELECT DISTINCT c.oracle_id, c.name, c.cmc, c.type_line, c.scryfall_uri, c.image_uri
        FROM cards c
        JOIN card_mechanic_tags t ON t.oracle_id = c.oracle_id
        WHERE c.commander_legal = 1
          AND c.commander_eligible = 0
          AND c.is_basic_land = 0
          AND c.oracle_id != ?
    """
    synergy_params: list = [commander["oracle_id"]]
    if theme_filter:
        placeholders = ",".join("?" * len(theme_filter))
        synergy_sql += f" AND t.tag IN ({placeholders}) AND t.layer = 'theme'"
        synergy_params.extend(theme_filter)
    synergy_sql += " LIMIT 200"
    candidates = conn.execute(synergy_sql, synergy_params).fetchall()
    sample_size = min(10, len(candidates))
    sampled = rng.sample(list(candidates), k=sample_size) if candidates else []

    criteria = DeckCriteria(
        themes=theme_filter,
        colors=color_filter or identity,
        commander_oracle_ids=[commander["oracle_id"]],
        slot_template=slot_counts,
        seed=seed,
    )

    out_dir = output_dir or OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = f"stub-{commander['name'].lower().replace(' ', '-')[:40]}"
    timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    base = out_dir / f"{slug}-{timestamp}"

    deck_json = {
        "schema_version": "1.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "generator": {"name": "mtg-deck-tools", "version": "0.1.0", "phase": "stub"},
        "criteria": criteria.model_dump(),
        "commanders": [
            {
                "oracle_id": commander["oracle_id"],
                "name": commander["name"],
                "partner_kind": commander["partner_kind"],
                "scryfall_uri": commander["scryfall_uri"],
            }
        ],
        "sample_cards": [
            {
                "oracle_id": r["oracle_id"],
                "name": r["name"],
                "cmc": r["cmc"],
                "type_line": r["type_line"],
                "scryfall_uri": r["scryfall_uri"],
                "image_uri": r["image_uri"],
            }
            for r in sampled
        ],
        "note": "Phase 1 stub — not a complete 100-card deck. Use Phase 2 generate for full builds.",
    }

    json_path = base.with_suffix(".deck.json")
    md_path = base.with_suffix(".md")
    json_path.write_text(json.dumps(deck_json, indent=2), encoding="utf-8")

    lines = [
        f"# Stub deck sample — {commander['name']}",
        "",
        "> Phase 1 preview only. Full 100-card generation is Phase 2.",
        "",
        f"**Commander:** {commander['name']}",
        f"**Color identity:** {', '.join(identity) or 'colorless'}",
        f"**Seed:** {seed if seed is not None else 'random'}",
        "",
    ]
    if criteria.themes:
        lines.append(f"**Themes:** {', '.join(criteria.themes)}")
        lines.append("")
    if criteria.slot_template:
        lines.append("## Slot template")
        lines.append("")
        for slot, count in criteria.slot_template.items():
            lines.append(f"- {slot}: {count}")
        lines.append("")
    lines.extend(
        [
            "## Sample synergy cards",
            "",
        ]
    )
    for row in sampled:
        lines.append(f"- {row['name']} ({row['type_line']}, CMC {row['cmc']})")
    if not sampled:
        lines.append("- _(no matching cards for theme filters)_")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    conn.close()
    return json_path
