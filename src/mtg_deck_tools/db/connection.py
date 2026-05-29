"""SQLite connection helpers."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from mtg_deck_tools.db.schema import apply_schema
from mtg_deck_tools.paths import DEFAULT_DB_PATH


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def ensure_schema(db_path: Path | None = None) -> sqlite3.Connection:
    conn = connect(db_path)
    apply_schema(conn)
    return conn
