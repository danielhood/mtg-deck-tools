"""Saved deck library schema (UX7f)."""

DECKS_SCHEMA_VERSION = "1"

DECKS_SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS library_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS saved_decks (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    saved_at TEXT NOT NULL,
    deck_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_saved_decks_saved_at ON saved_decks(saved_at);
CREATE INDEX IF NOT EXISTS idx_saved_decks_name ON saved_decks(name);
"""


def apply_decks_schema(conn) -> None:
    conn.executescript(DECKS_SCHEMA_SQL)
    conn.execute(
        "INSERT OR REPLACE INTO library_metadata (key, value) VALUES (?, ?)",
        ("schema_version", DECKS_SCHEMA_VERSION),
    )
    conn.commit()
