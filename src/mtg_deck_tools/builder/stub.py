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
from mtg_deck_tools.wizard.commanders import CommanderRow, combined_color_identity


def _require_db(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        raise FileNotFoundError(
            f"Database not found at {db_path}. Run: mtg-deck-tools import"
        )
    return connect(db_path)


def _fetch_commanders(
    conn: sqlite3.Connection,
    oracle_ids: list[str],
) -> list[sqlite3.Row]:
    if not oracle_ids:
        return []
    placeholders = ",".join("?" * len(oracle_ids))
    rows = conn.execute(
        f"""
        SELECT oracle_id, name, color_identity, partner_kind, scryfall_uri
        FROM cards
        WHERE commander_eligible = 1 AND oracle_id IN ({placeholders})
        """,
        oracle_ids,
    ).fetchall()
    by_id = {row["oracle_id"]: row for row in rows}
    return [by_id[oid] for oid in oracle_ids if oid in by_id]


def _pick_commander(
    conn: sqlite3.Connection,
    rng: random.Random,
    *,
    color_filter: list[str],
    commander_ids: list[str],
) -> list[sqlite3.Row]:
    if commander_ids:
        commanders = _fetch_commanders(conn, commander_ids)
        if not commanders:
            raise RuntimeError("Selected commander(s) not found in database. Re-run import.")
        return commanders

    commander_sql = """
        SELECT oracle_id, name, color_identity, partner_kind, scryfall_uri
        FROM cards
        WHERE commander_eligible = 1
    """
    params: list = []
    for color in color_filter:
        commander_sql += " AND color_identity LIKE ?"
        params.append(f'%"{color}"%')
    commanders = conn.execute(commander_sql, params).fetchall()
    if not commanders:
        raise RuntimeError("No commanders match the given filters. Try different colors.")
    return [rng.choice(commanders)]


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
    Full 100-card slot filling arrives in Phase 2.
    """
    db = db_path or DEFAULT_DB_PATH
    conn = _require_db(db)
    rng = random.Random(seed)

    input_criteria = criteria
    if input_criteria is not None:
        color_filter = input_criteria.colors
        theme_filter = input_criteria.themes
        slot_counts = input_criteria.slot_template
        include_mechanics = input_criteria.include_mechanics
        avoid_mechanics = input_criteria.avoid_mechanics
        commander_ids = input_criteria.commander_oracle_ids
        seed = input_criteria.seed if input_criteria.seed is not None else seed
    else:
        color_filter = colors or []
        theme_filter = themes or []
        slot_counts = slot_template or {}
        include_mechanics = []
        avoid_mechanics = []
        commander_ids = []

    commanders = _pick_commander(
        conn,
        rng,
        color_filter=color_filter,
        commander_ids=commander_ids,
    )
    identity_rows = [
        {
            "oracle_id": c["oracle_id"],
            "name": c["name"],
            "color_identity": json.loads(c["color_identity"] or "[]"),
            "partner_kind": c["partner_kind"],
            "scryfall_uri": c["scryfall_uri"],
        }
        for c in commanders
    ]
    identity = combined_color_identity(
        [
            CommanderRow(
                oracle_id=r["oracle_id"],
                name=r["name"],
                color_identity=r["color_identity"],
                partner_kind=r["partner_kind"],
                edhrec_rank=None,
            )
            for r in identity_rows
        ]
    )

    commander_ids_in_deck = {c["oracle_id"] for c in commanders}

    synergy_sql = """
        SELECT DISTINCT c.oracle_id, c.name, c.cmc, c.type_line, c.scryfall_uri, c.image_uri
        FROM cards c
    """
    if theme_filter:
        synergy_sql += """
        JOIN card_mechanic_tags t ON t.oracle_id = c.oracle_id
        """
    synergy_sql += """
        WHERE c.commander_legal = 1
          AND c.commander_eligible = 0
          AND c.is_basic_land = 0
    """
    synergy_params: list = []

    for oid in commander_ids_in_deck:
        synergy_sql += " AND c.oracle_id != ?"
        synergy_params.append(oid)

    if theme_filter:
        placeholders = ",".join("?" * len(theme_filter))
        synergy_sql += f" AND t.tag IN ({placeholders}) AND t.layer = 'theme'"
        synergy_params.extend(theme_filter)

    if avoid_mechanics:
        placeholders = ",".join("?" * len(avoid_mechanics))
        synergy_sql += f"""
          AND c.oracle_id NOT IN (
            SELECT oracle_id FROM card_mechanic_tags
            WHERE tag IN ({placeholders}) AND layer = 'keyword'
          )
        """
        synergy_params.extend(avoid_mechanics)

    for color in ("W", "U", "B", "R", "G"):
        if color not in identity:
            synergy_sql += " AND c.color_identity NOT LIKE ?"
            synergy_params.append(f'%"{color}"%')

    if include_mechanics:
        placeholders = ",".join("?" * len(include_mechanics))
        synergy_sql += f"""
        ORDER BY CASE WHEN EXISTS (
            SELECT 1 FROM card_mechanic_tags inc
            WHERE inc.oracle_id = c.oracle_id
              AND inc.tag IN ({placeholders})
              AND inc.layer = 'keyword'
        ) THEN 0 ELSE 1 END
        """
        synergy_params.extend(include_mechanics)
    synergy_sql += " LIMIT 200"

    candidates = conn.execute(synergy_sql, synergy_params).fetchall()
    sample_size = min(10, len(candidates))
    sampled = rng.sample(list(candidates), k=sample_size) if candidates else []

    if input_criteria is not None:
        output_criteria = input_criteria.model_copy(
            update={
                "commander_oracle_ids": [c["oracle_id"] for c in commanders],
                "colors": identity,
                "seed": seed,
            }
        )
    else:
        output_criteria = DeckCriteria(
            themes=theme_filter,
            colors=identity,
            commander_oracle_ids=[c["oracle_id"] for c in commanders],
            slot_template=slot_counts,
            seed=seed,
        )

    out_dir = output_dir or OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    slug_name = commanders[0]["name"].lower().replace(" ", "-")[:40]
    slug = f"stub-{slug_name}"
    timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    base = out_dir / f"{slug}-{timestamp}"

    deck_json = {
        "schema_version": "1.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "generator": {"name": "mtg-deck-tools", "version": "0.1.0", "phase": "stub"},
        "criteria": output_criteria.model_dump(),
        "commanders": identity_rows,
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

    commander_label = ", ".join(c["name"] for c in commanders)
    lines = [
        f"# Stub deck sample — {commander_label}",
        "",
        "> Phase 1 preview only. Full 100-card generation is Phase 2.",
        "",
        f"**Commander{'s' if len(commanders) > 1 else ''}:** {commander_label}",
        f"**Color identity:** {', '.join(identity) or 'colorless'}",
        f"**Seed:** {seed if seed is not None else 'random'}",
        "",
    ]
    if output_criteria.themes:
        lines.append(f"**Themes:** {', '.join(output_criteria.themes)}")
        lines.append("")
    if output_criteria.include_mechanics:
        lines.append(f"**Include:** {', '.join(output_criteria.include_mechanics)}")
        lines.append("")
    if output_criteria.avoid_mechanics:
        lines.append(f"**Avoid:** {', '.join(output_criteria.avoid_mechanics)}")
        lines.append("")
    if output_criteria.budget_usd is not None:
        lines.append(f"**Budget cap:** ${output_criteria.budget_usd:.2f}")
        lines.append("")
    if output_criteria.slot_template:
        lines.append("## Slot template")
        lines.append("")
        for slot, count in output_criteria.slot_template.items():
            lines.append(f"- {slot}: {count}")
        lines.append("")
    lines.extend(["## Sample synergy cards", ""])
    for row in sampled:
        lines.append(f"- {row['name']} ({row['type_line']}, CMC {row['cmc']})")
    if not sampled:
        lines.append("- _(no matching cards for filters)_")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    conn.close()
    return json_path
