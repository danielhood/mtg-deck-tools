"""Database schema definitions."""

SCHEMA_VERSION = "3"

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS import_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cards (
    oracle_id TEXT PRIMARY KEY,
    scryfall_id TEXT,
    name TEXT NOT NULL,
    layout TEXT,
    type_line TEXT,
    oracle_text TEXT,
    mana_cost TEXT,
    cmc REAL,
    colors TEXT,
    color_identity TEXT,
    keywords TEXT,
    produced_mana TEXT,
    power TEXT,
    toughness TEXT,
    commander_legal INTEGER NOT NULL DEFAULT 0,
    commander_eligible INTEGER NOT NULL DEFAULT 0,
    is_basic_land INTEGER NOT NULL DEFAULT 0,
    partner_kind TEXT,
    edhrec_rank INTEGER,
    price_usd REAL,
    price_known INTEGER NOT NULL DEFAULT 0,
    released_at TEXT,
    rarity TEXT,
    scryfall_uri TEXT,
    image_uri TEXT,
    set_type TEXT,
    reprint INTEGER,
    availability_score REAL
);

CREATE TABLE IF NOT EXISTS card_mechanic_tags (
    oracle_id TEXT NOT NULL REFERENCES cards(oracle_id) ON DELETE CASCADE,
    tag TEXT NOT NULL,
    layer TEXT NOT NULL,
    source TEXT,
    PRIMARY KEY (oracle_id, tag)
);

CREATE INDEX IF NOT EXISTS idx_cards_commander_legal ON cards(commander_legal);
CREATE INDEX IF NOT EXISTS idx_cards_commander_eligible ON cards(commander_eligible);
CREATE INDEX IF NOT EXISTS idx_cards_color_identity ON cards(color_identity);
CREATE INDEX IF NOT EXISTS idx_cards_cmc ON cards(cmc);
CREATE INDEX IF NOT EXISTS idx_cards_name ON cards(name);
CREATE INDEX IF NOT EXISTS idx_tags_tag ON card_mechanic_tags(tag);
CREATE INDEX IF NOT EXISTS idx_tags_layer ON card_mechanic_tags(layer);

CREATE TABLE IF NOT EXISTS card_effects (
    oracle_id TEXT NOT NULL REFERENCES cards(oracle_id) ON DELETE CASCADE,
    face_index INTEGER NOT NULL DEFAULT 0,
    effect_kind TEXT NOT NULL,
    payload TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 1.0,
    source TEXT NOT NULL,
    PRIMARY KEY (oracle_id, face_index, effect_kind, source)
);

CREATE INDEX IF NOT EXISTS idx_effects_kind ON card_effects(effect_kind);
CREATE INDEX IF NOT EXISTS idx_effects_oracle ON card_effects(oracle_id);
"""


def _ensure_columns(conn) -> None:
    """Add columns introduced after initial schema without full rebuild."""
    columns = {
        row[1] for row in conn.execute("PRAGMA table_info(cards)").fetchall()
    }
    if "availability_score" not in columns:
        conn.execute("ALTER TABLE cards ADD COLUMN availability_score REAL")


def apply_schema(conn) -> None:
    conn.executescript(SCHEMA_SQL)
    _ensure_columns(conn)
    conn.execute(
        "INSERT OR REPLACE INTO import_metadata (key, value) VALUES (?, ?)",
        ("schema_version", SCHEMA_VERSION),
    )
    conn.commit()
