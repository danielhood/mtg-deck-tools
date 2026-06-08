"""Saved deck library facades (UX7f)."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mtg_deck_tools.db.decks_schema import apply_decks_schema
from mtg_deck_tools.paths import resolve_db_path, resolve_decks_path
from mtg_deck_tools.service.dto import (
    DeckLibraryDetailResponse,
    DeckLibraryEntry,
    PatchDeckRequest,
)

_SORT_COLUMNS = {
    "saved_at": "saved_at",
    "name": "name COLLATE NOCASE",
    "commander": "json_extract(deck_json, '$.commanders[0].name') COLLATE NOCASE",
}


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _connect_decks(decks_path: Path | None = None) -> sqlite3.Connection:
    path = resolve_decks_path(decks_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    apply_decks_schema(conn)
    return conn


def require_cards_db(db_path: Path | None = None) -> Path:
    """Raise FileNotFoundError when the oracle database is missing (DB gate)."""
    path = resolve_db_path(db_path)
    if not path.exists():
        raise FileNotFoundError(f"Database not found: {path}")
    return path


def default_deck_name(deck: dict[str, Any]) -> str:
    commanders = deck.get("commanders")
    if isinstance(commanders, list) and commanders:
        names: list[str] = []
        for entry in commanders:
            if isinstance(entry, dict):
                name = entry.get("name")
                if isinstance(name, str) and name.strip():
                    names.append(name.strip())
        if names:
            return " / ".join(names)
    return "Untitled deck"


def _summary_from_deck(
    deck_id: str,
    name: str,
    saved_at: str,
    deck: dict[str, Any],
) -> DeckLibraryEntry:
    commanders = deck.get("commanders") if isinstance(deck.get("commanders"), list) else []
    commander_names: list[str] = []
    commander_image_uri: str | None = None
    commander_colors: list[str] = []
    for entry in commanders:
        if not isinstance(entry, dict):
            continue
        cname = entry.get("name")
        if isinstance(cname, str) and cname.strip():
            commander_names.append(cname.strip())
        if commander_image_uri is None:
            image = entry.get("image_uri")
            if isinstance(image, str) and image.strip():
                commander_image_uri = image.strip()
        if not commander_colors:
            colors = entry.get("color_identity")
            if isinstance(colors, list):
                commander_colors = [c for c in colors if isinstance(c, str)]

    criteria = deck.get("criteria") if isinstance(deck.get("criteria"), dict) else {}
    colors_raw = criteria.get("colors") if isinstance(criteria.get("colors"), list) else []
    colors = [c for c in colors_raw if isinstance(c, str)] or commander_colors
    themes_raw = criteria.get("themes") if isinstance(criteria.get("themes"), list) else []
    themes = [t for t in themes_raw if isinstance(t, str)]

    stats = deck.get("stats") if isinstance(deck.get("stats"), dict) else {}
    price = stats.get("estimated_price_usd")
    estimated_price_usd = price if isinstance(price, (int, float)) else None

    return DeckLibraryEntry(
        id=deck_id,
        name=name,
        saved_at=saved_at,
        commander_names=commander_names,
        commander_image_uri=commander_image_uri,
        colors=colors,
        themes=themes,
        estimated_price_usd=estimated_price_usd,
    )


def save_deck_to_library(
    deck: dict[str, Any],
    *,
    deck_id: str | None = None,
    name: str | None = None,
    decks_path: Path | None = None,
) -> DeckLibraryDetailResponse:
    deck_id = deck_id or str(uuid.uuid4())
    label = (name or default_deck_name(deck)).strip() or default_deck_name(deck)
    saved_at = _utc_now_iso()
    payload = json.dumps(deck, separators=(",", ":"))

    with _connect_decks(decks_path) as conn:
        conn.execute(
            """
            INSERT INTO saved_decks (id, name, saved_at, deck_json)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                saved_at = excluded.saved_at,
                deck_json = excluded.deck_json
            """,
            (deck_id, label, saved_at, payload),
        )
        conn.commit()

    return DeckLibraryDetailResponse(
        id=deck_id,
        name=label,
        saved_at=saved_at,
        deck=deck,
    )


def list_library_decks(
    *,
    q: str | None = None,
    sort: str = "saved_at",
    limit: int = 100,
    decks_path: Path | None = None,
) -> list[DeckLibraryEntry]:
    sort_key = _SORT_COLUMNS.get(sort, _SORT_COLUMNS["saved_at"])
    order = "DESC" if sort == "saved_at" else "ASC"
    clauses: list[str] = []
    params: list[Any] = []

    if q and q.strip():
        needle = f"%{q.strip().lower()}%"
        clauses.append(
            """
            (
                lower(name) LIKE ?
                OR lower(json_extract(deck_json, '$.commanders[0].name')) LIKE ?
                OR lower(json_extract(deck_json, '$.commanders[1].name')) LIKE ?
                OR lower(json_extract(deck_json, '$.criteria.themes')) LIKE ?
            )
            """
        )
        params.extend([needle, needle, needle, needle])

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = f"""
        SELECT id, name, saved_at, deck_json
        FROM saved_decks
        {where}
        ORDER BY {sort_key} {order}
        LIMIT ?
    """
    params.append(max(1, min(limit, 500)))

    with _connect_decks(decks_path) as conn:
        rows = conn.execute(sql, params).fetchall()

    entries: list[DeckLibraryEntry] = []
    for row in rows:
        deck = json.loads(row["deck_json"])
        entries.append(_summary_from_deck(row["id"], row["name"], row["saved_at"], deck))
    return entries


def get_library_deck(
    deck_id: str,
    *,
    decks_path: Path | None = None,
) -> DeckLibraryDetailResponse | None:
    with _connect_decks(decks_path) as conn:
        row = conn.execute(
            "SELECT id, name, saved_at, deck_json FROM saved_decks WHERE id = ?",
            (deck_id,),
        ).fetchone()
    if row is None:
        return None
    deck = json.loads(row["deck_json"])
    return DeckLibraryDetailResponse(
        id=row["id"],
        name=row["name"],
        saved_at=row["saved_at"],
        deck=deck,
    )


def patch_library_deck(
    deck_id: str,
    body: PatchDeckRequest,
    *,
    decks_path: Path | None = None,
) -> DeckLibraryDetailResponse | None:
    name = body.name.strip()
    if not name:
        raise ValueError("name must not be empty")

    with _connect_decks(decks_path) as conn:
        row = conn.execute(
            "SELECT id, name, saved_at, deck_json FROM saved_decks WHERE id = ?",
            (deck_id,),
        ).fetchone()
        if row is None:
            return None
        conn.execute(
            "UPDATE saved_decks SET name = ? WHERE id = ?",
            (name, deck_id),
        )
        conn.commit()

    deck = json.loads(row["deck_json"])
    return DeckLibraryDetailResponse(
        id=row["id"],
        name=name,
        saved_at=row["saved_at"],
        deck=deck,
    )


def delete_library_deck(
    deck_id: str,
    *,
    decks_path: Path | None = None,
) -> bool:
    with _connect_decks(decks_path) as conn:
        cursor = conn.execute("DELETE FROM saved_decks WHERE id = ?", (deck_id,))
        conn.commit()
        return cursor.rowcount > 0
